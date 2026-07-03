import os
import json
import re
import html as html_mod
from html.parser import HTMLParser
from html import unescape
from typing import Any, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from app.core.config import WORKSPACE_DIR
from app.tools.browser import _get_browser_path


def _dedup_results(all_results: List[Dict]) -> List[Dict]:
    seen_urls = set()
    deduped = []
    for r in all_results:
        url = r.get("href", "").rstrip("/").lower()
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(r)
    return deduped


def _search_duckduckgo(query: str, num_results: int) -> List[Dict]:
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results, region="us-en"))
        return [{"title": r.get("title", ""), "href": r.get("href", ""), "body": r.get("body", ""), "engine": "duckduckgo"} for r in results]
    except Exception:
        return []


def _search_bing_scrape(query: str, num_results: int) -> List[Dict]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Accept": "text/html",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(
            "https://www.bing.com/search",
            params={"q": query, "count": num_results},
            headers=headers,
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        html = resp.text
        results = []
        seen_urls = set()
        links = re.findall(r'href="(https?://[^"]+)"', html)
        for url in links:
            if "bing.com" in url or "microsoft.com" in url or "go.microsoft" in url:
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            title = url.split("//")[-1].split("/")[0]
            results.append({"title": title, "href": url, "body": "", "engine": "bing"})
            if len(results) >= num_results:
                break
        return results
    except Exception:
        return []


def _search_brave_api(query: str, num_results: int, api_key: str) -> List[Dict]:
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": query, "count": num_results},
            headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for r in data.get("web", {}).get("results", []):
            results.append({
                "title": r.get("title", ""),
                "href": r.get("url", ""),
                "body": r.get("description", ""),
                "engine": "brave",
            })
        return results
    except Exception:
        return []


def _search_searxng(query: str, num_results: int, base_url: str) -> List[Dict]:
    try:
        resp = requests.get(
            f"{base_url.rstrip('/')}/search",
            params={"q": query, "format": "json", "engines": "google,bing,duckduckgo"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for r in data.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "href": r.get("url", ""),
                "body": r.get("content", ""),
                "engine": r.get("engine", "searxng"),
            })
        return results[:num_results]
    except Exception:
        return []


def _optimize_search_query(query: str) -> str:
    """Convert natural language questions into search-engine-friendly keywords."""
    q = query.strip()
    prefixes = [
        r"^how\s+(do|can|to|would)\s+(i|you|we)\s+",
        r"^how\s+",
        r"^what\s+(is|are|do|does|can|should|would)\s+(a|an|the|i|you|we)?\s*",
        r"^what\s+",
        r"^why\s+(do|does|is|are|can|should)\s+(i|you|we)?\s*",
        r"^why\s+",
        r"^when\s+(do|does|is|are|can|should)\s+(i|you|we)?\s*",
        r"^when\s+",
        r"^where\s+(do|does|is|are|can|should)\s+(i|you|we)?\s*",
        r"^where\s+",
        r"^which\s+(is|are|do|does|can|should)\s+(a|an|the|i|you|we)?\s*",
        r"^which\s+",
        r"^can\s+(i|you|we)\s+",
        r"^can\s+",
        r"^should\s+(i|you|we)\s+",
        r"^should\s+",
        r"^is\s+it\s+",
        r"^is\s+",
        r"^are\s+",
        r"^do\s+(i|you|we)\s+",
        r"^does\s+",
    ]
    for pattern in prefixes:
        q = re.sub(pattern, "", q, count=1, flags=re.IGNORECASE)
    stopwords = {"a", "an", "the", "to", "for", "of", "in", "on", "at", "by", "with",
                 "from", "this", "that", "it", "its", "and", "or", "but", "not", "very",
                 "really", "just", "also", "so", "too", "my", "your", "our", "their",
                 "downloaded", "download", "using", "use", "get", "got", "make", "made",
                 "way", "best", "good", "proper", "correct", "right"}
    words = [w for w in q.split() if w.lower() not in stopwords]
    if len(words) > 5:
        words = words[:5]
    return " ".join(words) if words else query


def _is_irrelevant_result(result: Dict, query: str) -> bool:
    """Filter out obviously irrelevant search results."""
    text = (result.get("href", "") + " " + result.get("title", "") + " " + result.get("body", "")).lower()
    irrelevant_domains = ["poki.com", "friv.com", "crazygames.com", "miniclip.com",
                          "kongregate.com", "newgrounds.com", "armor-games.com",
                          "play.google.com/store/apps", "apps.apple.com",
                          "amazon.com", "ebay.com", "walmart.com", "aliexpress.com",
                          "tiktok.com", "instagram.com", "facebook.com",
                          "netflix.com", "hulu.com", "disneyplus.com",
                          "softonic.com", "uptodown.com", "filehippo.com",
                          "trustpilot.com", "glassdoor.com", "reddit.com/r/gaming"]
    for domain in irrelevant_domains:
        if domain in text:
            return True
    irrelevant_phrases = ["play free games", "online games", "free online games",
                          "survival shooter", "battle royale", "mobile game",
                          "play now", "unblocked games", "io games",
                          "free fire", "freegames", "free.fr"]
    score = sum(1 for kw in irrelevant_phrases if kw in text)
    if score >= 1:
        return True
    query_words = set(query.lower().split())
    query_words -= {"how", "do", "you", "to", "the", "a", "an", "is", "are", "what",
                    "why", "when", "where", "which", "can", "should", "for", "of",
                    "in", "on", "at", "and", "or", "it", "this", "that", "i", "we"}
    result_text = result.get("title", "").lower() + " " + result.get("body", "").lower()
    matching_words = sum(1 for w in query_words if w in result_text)
    if query_words and matching_words == 0:
        return True
    return False


class _HTMLTextExtractor(HTMLParser):
    """Strip HTML tags and return clean text. Firecrawl-style content extraction."""

    SKIP_TAGS = {"script", "style", "noscript", "iframe", "svg", "nav", "footer",
                 "header", "aside", "form", "button", "input", "select", "textarea",
                 "meta", "link", "head"}
    BLOCK_TAGS = {"p", "div", "br", "h1", "h2", "h3", "h4", "h5", "h6", "li",
                  "tr", "blockquote", "pre", "section", "article", "main", "figcaption"}
    TEXT_TAGS = {"a": "href", "img": "alt", "source": "src"}

    def __init__(self):
        super().__init__()
        self._text_parts: List[str] = []
        self._skip_depth = 0
        self._skip_tag = ""

    def handle_starttag(self, tag: str, attrs: List[tuple]):
        tag_lower = tag.lower()
        if tag_lower in self.SKIP_TAGS:
            self._skip_depth += 1
            self._skip_tag = tag_lower
            return
        if tag_lower in self.BLOCK_TAGS:
            self._text_parts.append("\n")
        if tag_lower == "a":
            attr_dict = dict(attrs)
            href = attr_dict.get("href", "")
            if href and href.startswith(("http://", "https://")):
                self._text_parts.append(f" [{href}] ")
        if tag_lower == "img":
            attr_dict = dict(attrs)
            alt = attr_dict.get("alt", "")
            if alt:
                self._text_parts.append(f" [{alt}] ")

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag_lower in self.BLOCK_TAGS:
            self._text_parts.append("\n")

    def handle_data(self, data: str):
        if self._skip_depth > 0:
            return
        text = data.strip()
        if text:
            self._text_parts.append(text + " ")

    def get_text(self) -> str:
        raw = " ".join(self._text_parts)
        raw = unescape(raw)
        raw = re.sub(r'[ \t]+', ' ', raw)
        raw = re.sub(r'\n{3,}', '\n\n', raw)
        return raw.strip()


def web_scraper(url: str, max_chars=8000, **kwargs) -> str:
    """Firecrawl-clone: fetch a URL, strip all HTML/code, return clean text."""
    try:
        max_chars = int(max_chars) if max_chars else 8000
    except (ValueError, TypeError):
        max_chars = 8000
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        }

        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            if "text/" in content_type:
                return resp.text[:max_chars]
            return f"Non-HTML content ({content_type}). Cannot scrape."

        html = resp.text

        extractor = _HTMLTextExtractor()
        extractor.feed(html)
        clean_text = extractor.get_text()

        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else ""
        title = unescape(re.sub(r'<[^>]+>', '', title)).strip()

        if title:
            clean_text = f"# {title}\n\n{clean_text}"

        if len(clean_text) > max_chars:
            clean_text = clean_text[:max_chars] + "\n\n... [content truncated]"

        if not clean_text.strip():
            return f"Scraped {url} but extracted text was empty (likely JS-rendered page)."

        return clean_text

    except requests.exceptions.Timeout:
        return f"Error: Timed out scraping {url}"
    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to {url}"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} from {url}"
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


def _scrape_search_result_urls(urls: List[str], max_chars_per_page: int = 4000) -> Dict[str, str]:
    """Scrape multiple URLs in parallel and return {url: clean_text}."""
    results: Dict[str, str] = {}
    if not urls:
        return results

    def _fetch_one(url: str) -> tuple:
        text = web_scraper(url, max_chars=max_chars_per_page)
        return (url, text)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_fetch_one, u): u for u in urls[:3]}
        for future in as_completed(futures, timeout=20):
            try:
                url, text = future.result()
                results[url] = text
            except Exception:
                results[futures[future]] = "Error: Failed to scrape"

    return results


def web_search(query: str, num_results=5, scrape=True) -> str:
    try:
        num_results = int(num_results) if num_results else 5
        scrape = str(scrape).lower() == "true" if isinstance(scrape, str) else bool(scrape)
    except (ValueError, TypeError):
        num_results = 5
        scrape = True
    try:
        from settings_manager import settings_manager
        search_settings = settings_manager.get_search_settings()
    except Exception:
        search_settings = {"search_provider": "auto", "brave_api_key": "", "searxng_url": ""}

    provider = search_settings.get("search_provider", "auto")
    brave_key = search_settings.get("brave_api_key", "")
    searxng_url = search_settings.get("searxng_url", "")

    optimized_query = _optimize_search_query(query)

    fetch_count = max(num_results * 4, 20)
    all_results: List[Dict] = []

    if provider == "brave" and brave_key:
        all_results = _search_brave_api(optimized_query, fetch_count, brave_key)
    elif provider == "searxng" and searxng_url:
        all_results = _search_searxng(optimized_query, fetch_count, searxng_url)
    elif provider == "duckduckgo":
        all_results = _search_duckduckgo(optimized_query, fetch_count)
    else:
        engines = []
        if brave_key:
            engines.append(("brave", lambda: _search_brave_api(optimized_query, fetch_count, brave_key)))
        if searxng_url:
            engines.append(("searxng", lambda: _search_searxng(optimized_query, fetch_count, searxng_url)))
        engines.append(("duckduckgo", lambda: _search_duckduckgo(optimized_query, fetch_count)))
        engines.append(("bing", lambda: _search_bing_scrape(optimized_query, fetch_count)))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(fn): name for name, fn in engines}
            for future in as_completed(futures, timeout=20):
                engine_name = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception:
                    pass

    all_results = _dedup_results(all_results)
    all_results = [r for r in all_results if not _is_irrelevant_result(r, optimized_query)]

    if not all_results:
        return f"No results found for: {query}"

    final = all_results[:num_results]

    scraped_content: Dict[str, str] = {}
    if scrape:
        urls_to_scrape = [r.get("href", "") for r in final if r.get("href", "").startswith("http")]
        if urls_to_scrape:
            scraped_content = _scrape_search_result_urls(urls_to_scrape, max_chars_per_page=4000)

    output_lines = []
    engines_used = set()
    for i, r in enumerate(final, 1):
        engines_used.add(r.get("engine", "unknown"))
        url = r.get("href", "N/A")
        output_lines.append(f"{i}. {r.get('title', 'No title')}")
        output_lines.append(f"   URL: {url}")
        output_lines.append(f"   {r.get('body', 'No description')}")
        if url in scraped_content and scraped_content[url]:
            page_text = scraped_content[url]
            output_lines.append(f"   [Scraped content]: {page_text[:2000]}")
        output_lines.append("")
    output_lines.append(f"--- Sources: {', '.join(sorted(engines_used))} ---")
    return "\n".join(output_lines)


def web_research(action: str = "search", query: str = "", url: str = "",
                 engine: str = "google", max_results: int = 5, selector: str = "",
                 screenshot: str = "", wait_seconds: int = 3, **kwargs) -> str:
    """Search the web or scrape pages using Playwright with Brave browser to bypass anti-bot defenses."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "Error: playwright not installed. Run: pip install playwright && playwright install chromium"

    brave_path = _get_browser_path()
    if not brave_path:
        return "Error: Brave browser not found. Set browser_path in Settings or OLLAMAFLOW_BROWSER_PATH env var."

    search_urls = {
        "google": "https://www.google.com/search?q={query}&num={num}",
        "bing": "https://www.bing.com/search?q={query}&count={num}",
        "duckduckgo": "https://duckduckgo.com/?q={query}",
        "brave": "https://search.brave.com/search?q={query}",
    }

    def _extract_page_text(page) -> str:
        return page.evaluate("""() => {
            const skipTags = new Set(['script','style','noscript','iframe','svg','nav','footer','header','aside','form','button','input','select','textarea','meta','link','head']);
            function walk(node) {
                if (node.nodeType === 3) return node.textContent.trim() + ' ';
                if (node.nodeType !== 1) return '';
                if (skipTags.has(node.tagName.toLowerCase())) return '';
                let text = '';
                for (const child of node.childNodes) text += walk(child);
                const tag = node.tagName.toLowerCase();
                if (['p','div','br','h1','h2','h3','h4','h5','h6','li','tr','blockquote','pre','section','article','main'].includes(tag)) text = '\\n' + text + '\\n';
                if (tag === 'a') {
                    const href = node.getAttribute('href');
                    if (href && href.startsWith('http')) text = ' [' + href + '] ' + text;
                }
                return text;
            }
            return walk(document.body).replace(/[ \\t]+/g, ' ').replace(/\\n{3,}/g, '\\n\\n').trim();
        }""")

    def _extract_search_results(page) -> list:
        return page.evaluate("""() => {
            const results = [];
            const seen = new Set();
            const links = document.querySelectorAll('a[href]');
            for (const link of links) {
                const href = link.getAttribute('href');
                if (!href || !href.startsWith('http')) continue;
                if (seen.has(href)) continue;
                const text = link.innerText.trim();
                if (!text || text.length < 5) continue;
                if (href.includes('google.com') || href.includes('bing.com') || href.includes('duckduckgo.com') || href.includes('brave.com')) continue;
                seen.add(href);
                const parent = link.closest('div, li, article');
                let body = '';
                if (parent) {
                    const clone = parent.cloneNode(true);
                    clone.querySelectorAll('a').forEach(a => a.remove());
                    body = clone.innerText.trim().substring(0, 300);
                }
                results.push({title: text, url: href, body: body});
                if (results.length >= 20) break;
            }
            return results;
        }""")

    try:
        with sync_playwright() as p:
            launch_opts = {
                "headless": True,
                "executable_path": brave_path,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-infobars",
                ]
            }
            browser = p.chromium.launch(**launch_opts)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            """)

            if action == "search":
                if not query:
                    browser.close()
                    return "Error: query parameter is required for search"
                num = max(min(max_results, 20), 1)
                search_url = search_urls.get(engine, search_urls["google"]).format(query=query.replace(" ", "+"), num=num)
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)
                results = _extract_search_results(page)
                browser.close()
                if not results:
                    return f"No search results found for: {query}"
                lines = [f"Search results for: {query} (via {engine})", ""]
                for i, r in enumerate(results[:max_results], 1):
                    lines.append(f"{i}. {r['title']}")
                    lines.append(f"   URL: {r['url']}")
                    if r['body']:
                        lines.append(f"   {r['body']}")
                    lines.append("")
                return "\n".join(lines)

            elif action == "search_and_scrape":
                if not query:
                    browser.close()
                    return "Error: query parameter is required for search_and_scrape"
                num = max(min(max_results, 10), 1)
                search_url = search_urls.get(engine, search_urls["google"]).format(query=query.replace(" ", "+"), num=num)
                page.goto(search_url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)
                results = _extract_search_results(page)
                if not results:
                    browser.close()
                    return f"No search results found for: {query}"
                lines = [f"Search results for: {query} (via {engine})", ""]
                for i, r in enumerate(results[:num], 1):
                    lines.append(f"{i}. {r['title']}")
                    lines.append(f"   URL: {r['url']}")
                    if r['body']:
                        lines.append(f"   {r['body']}")
                    try:
                        page.goto(r['url'], timeout=20000)
                        page.wait_for_load_state("domcontentloaded", timeout=10000)
                        page.wait_for_timeout(2000)
                        text = _extract_page_text(page)
                        if text and len(text) > 50:
                            lines.append(f"   [Scraped]: {text[:3000]}")
                    except Exception:
                        pass
                    lines.append("")
                browser.close()
                return "\n".join(lines)

            elif action == "goto":
                if not url:
                    browser.close()
                    return "Error: url parameter is required for goto"
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                page.goto(url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(wait_seconds * 1000)
                title = page.title()
                text = _extract_page_text(page)
                browser.close()
                return f"Title: {title}\n\n{text[:10000]}"

            elif action == "extract":
                if not url:
                    browser.close()
                    return "Error: url parameter is required for extract"
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                page.goto(url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(wait_seconds * 1000)
                if selector:
                    elements = page.query_selector_all(selector)
                    texts = [el.inner_text() for el in elements[:20]]
                    browser.close()
                    return f"Extracted {len(texts)} elements matching '{selector}':\n" + "\n---\n".join(texts)
                else:
                    text = _extract_page_text(page)
                    browser.close()
                    return f"Page content:\n\n{text[:10000]}"

            elif action == "screenshot":
                if not url:
                    browser.close()
                    return "Error: url parameter is required for screenshot"
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                page.goto(url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(wait_seconds * 1000)
                screenshot_path = screenshot or "screenshot.png"
                if not os.path.isabs(screenshot_path):
                    screenshot_path = os.path.join(WORKSPACE_DIR, screenshot_path)
                page.screenshot(path=screenshot_path, full_page=True)
                browser.close()
                return f"Screenshot saved to: {screenshot_path}"

            elif action == "click":
                if not url or not selector:
                    browser.close()
                    return "Error: url and selector parameters are required for click"
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                page.goto(url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                page.click(selector)
                page.wait_for_timeout(wait_seconds * 1000)
                text = _extract_page_text(page)
                browser.close()
                return f"Clicked: {selector}\n\n{text[:10000]}"

            elif action == "type":
                if not url or not selector:
                    browser.close()
                    return "Error: url and selector parameters are required for type"
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                page.goto(url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                page.fill(selector, query)
                page.keyboard.press("Enter")
                page.wait_for_timeout(wait_seconds * 1000)
                text = _extract_page_text(page)
                browser.close()
                return f"Typed and submitted in '{selector}'\n\n{text[:10000]}"

            elif action == "evaluate":
                if not query:
                    browser.close()
                    return "Error: query parameter (JS code) is required for evaluate"
                if url:
                    if not url.startswith(("http://", "https://")):
                        url = "https://" + url
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                    page.wait_for_timeout(2000)
                result = page.evaluate(query)
                browser.close()
                return f"Result: {str(result)[:10000]}"

            else:
                browser.close()
                return f"Error: Unknown action '{action}'. Actions: search, search_and_scrape, goto, extract, screenshot, click, type, evaluate"

    except Exception as e:
        return f"Web research error: {str(e)}"


def youtube_transcript(video_url: str, language: str = "en", **kwargs) -> str:
    """Extract transcript from a YouTube video URL."""
    try:
        video_id_match = re.search(r'(?:v=|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})', video_url)
        if not video_id_match:
            return f"Error: Could not extract video ID from URL: {video_url}"
        video_id = video_id_match.group(1)
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            lines = [f"[{t['start']:.1f}s] {t['text']}" for t in transcript]
            return "\n".join(lines)[:10000]
        except ImportError:
            pass
        api_url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(api_url, headers=headers, timeout=15)
        caption_match = re.search(r'"captions":\s*(\{.*?\})\s*,\s*"videoDetails"', resp.text)
        if not caption_match:
            return f"Error: No captions available for video {video_id}. The video may not have subtitles."
        caption_data = json.loads(caption_match.group(1))
        tracks = caption_data.get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
        if not tracks:
            return f"Error: No caption tracks found for video {video_id}."
        track_url = tracks[0].get("baseUrl", "")
        if not track_url:
            return "Error: No caption URL found."
        caption_resp = requests.get(track_url, timeout=10)
        text_matches = re.findall(r'<text[^>]*>(.*?)</text>', caption_resp.text)
        lines = [html_mod.unescape(t) for t in text_matches if t.strip()]
        if not lines:
            return f"Error: Could not parse captions for video {video_id}."
        return "\n".join(lines)[:10000]
    except Exception as e:
        return f"YouTube transcript error: {str(e)}"
