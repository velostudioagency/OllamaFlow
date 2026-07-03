import json
from typing import Any, Dict

from app.core.config import WORKSPACE_DIR


def browser_use_tool(task: str, llm_provider: str = "ollama", llm_model: str = "",
                     headless: bool = True, allowed_domains: str = "", max_steps: int = 25,
                     **kwargs) -> str:
    try:
        import asyncio
        from browser_use import Agent, BrowserProfile
        if llm_provider == "ollama":
            from langchain_ollama import ChatOllama
            llm = ChatOllama(model=llm_model or "llama3.1:8b")
        elif llm_provider == "openai":
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model=llm_model or "gpt-4o")
        elif llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model=llm_model or "claude-sonnet-4-20250514")
        else:
            return f"Error: Unknown LLM provider '{llm_provider}'. Use ollama, openai, or anthropic."

        domains = [d.strip() for d in allowed_domains.split(",") if d.strip()] if allowed_domains else None
        max_steps = int(max_steps) if max_steps else 25

        async def _run():
            agent = Agent(
                task=task,
                llm=llm,
                browser_profile=BrowserProfile(
                    headless=headless,
                    allowed_domains=domains,
                ),
            )
            history = await agent.run(max_steps=max_steps)
            return history.final_result()

        return asyncio.run(_run())
    except ImportError as e:
        return f"Error: browser-use not installed. Run: pip install browser-use. Details: {e}"
    except Exception as e:
        return f"Browser-use error: {str(e)}"


def crawl4ai_tool(action: str = "scrape", url: str = "", max_pages: int = 5,
                  css_selector: str = "", javascript: str = "", cache: bool = True,
                  fit_markdown: bool = True, **kwargs) -> str:
    try:
        import asyncio
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
        max_pages = int(max_pages) if max_pages else 5

        async def _crawl():
            browser_config = BrowserConfig(headless=True)
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED if cache else CacheMode.BYPASS,
                css_selector=css_selector or None,
                js_code=javascript or None,
            )

            async with AsyncWebCrawler(config=browser_config) as crawler:
                if action == "scrape":
                    result = await crawler.arun(url=url, config=run_config)
                    if fit_markdown and result.markdown and result.markdown.fit_markdown:
                        return result.markdown.fit_markdown
                    return result.markdown.raw_markdown if result.markdown else "Error: No content returned"

                elif action == "deep_crawl":
                    from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
                    strategy = BFSDeepCrawlStrategy(max_depth=max_pages)
                    run_config.strategy = strategy
                    results = await crawler.arun(url=url, config=run_config)
                    output_parts = []
                    for r in results:
                        md = r.markdown.fit_markdown if (fit_markdown and r.markdown and r.markdown.fit_markdown) else (r.markdown.raw_markdown if r.markdown else "")
                        if md:
                            output_parts.append(f"### {r.url}\n\n{md}")
                    return "\n\n---\n\n".join(output_parts) if output_parts else "Error: No content found during deep crawl"

                elif action == "extract_structured":
                    from crawl4ai import JsonCssExtractionStrategy
                    schema = {"type": "object", "properties": {}, "selector": css_selector or "body"}
                    run_config = CrawlerRunConfig(
                        extraction_strategy=JsonCssExtractionStrategy(schema=schema),
                        cache_mode=CacheMode.ENABLED if cache else CacheMode.BYPASS,
                    )
                    async with AsyncWebCrawler(config=browser_config) as crawler2:
                        result = await crawler2.arun(url=url, config=run_config)
                        return json.dumps(result.extracted_content, indent=2)[:10000] if result.extracted_content else "Error: No structured content extracted"
                else:
                    return f"Error: Unknown action '{action}'. Use scrape, deep_crawl, or extract_structured"

        return asyncio.run(_crawl())
    except ImportError as e:
        return f"Error: crawl4ai not installed. Run: pip install crawl4ai. Details: {e}"
    except Exception as e:
        return f"Crawl4ai error: {str(e)}"


def firecrawl_tool(action: str = "scrape", url: str = "", query: str = "",
                   limit: int = 10, formats: str = "markdown", mode: str = "", **kwargs) -> str:
    try:
        from firecrawl import Firecrawl
        from settings_manager import settings_manager as _sm
        limit = int(limit) if limit else 10

        if not mode:
            mode = _sm.get("firecrawl_mode", "self_hosted")

        if mode == "self_hosted":
            base_url = _sm.get("firecrawl_url", "http://localhost:3001")
            app = Firecrawl(api_url=base_url)
        else:
            api_key = _sm.get("firecrawl_api_key", "")
            if not api_key:
                return "Error: Firecrawl API key not configured. Set firecrawl_api_key in Settings."
            app = Firecrawl(api_key=api_key)

        if action == "scrape":
            if not url:
                return "Error: URL is required for scrape"
            result = app.scrape(url, formats=[formats])
            return result.markdown if formats == "markdown" else result.html
        elif action == "crawl":
            if not url:
                return "Error: URL is required for crawl"
            result = app.crawl(url, limit=limit, scrape_options={"formats": [formats]})
            return "\n\n---\n\n".join([d.markdown for d in result.data]) if result.data else "Error: No data returned"
        elif action == "map":
            if not url:
                return "Error: URL is required for map"
            result = app.map(url)
            return json.dumps(result.links, indent=2)[:10000]
        elif action == "search":
            if not query:
                return "Error: Query is required for search"
            result = app.search(query, limit=limit)
            return json.dumps([{"title": r.title, "url": r.url, "markdown": r.markdown} for r in result.data.web], indent=2)[:10000]
        elif action == "agent":
            if not query:
                return "Error: Query is required for agent"
            result = app.agent(prompt=query)
            return result.data.result
        else:
            return f"Error: Unknown action '{action}'. Use scrape, crawl, map, search, or agent"
    except ImportError as e:
        return f"Error: firecrawl-py not installed. Run: pip install firecrawl-py. Details: {e}"
    except Exception as e:
        return f"Firecrawl error: {str(e)}"


def crawlee_tool(action: str = "scrape_urls", urls: str = "", max_requests: int = 10,
                 crawler_type: str = "playwright", proxy_url: str = "",
                 javascript_code: str = "", **kwargs) -> str:
    try:
        import asyncio
        from crawlee.crawlers import PlaywrightCrawler, BeautifulSoupCrawler
        max_requests = int(max_requests) if max_requests else 10
        url_list = [u.strip() for u in urls.split(",") if u.strip()]

        if not url_list:
            return "Error: No URLs provided"

        async def _crawlee_playwright():
            crawler = PlaywrightCrawler(max_requests_per_crawl=max_requests)

            @crawler.router.default_handler
            async def handler(context):
                data = {
                    "url": context.request.url,
                    "title": await context.page.title(),
                    "content": await context.page.content(),
                }
                await context.push_data(data)

            result = await crawler.run(url_list)
            return json.dumps(result.items, indent=2)[:10000]

        async def _crawlee_beautifulsoup():
            crawler = BeautifulSoupCrawler(max_requests_per_crawl=max_requests)

            @crawler.router.default_handler
            async def handler(context):
                data = {
                    "url": context.request.url,
                    "title": context.soup.title.string if context.soup.title else "",
                    "content": context.soup.get_text()[:5000],
                }
                await context.push_data(data)

            result = await crawler.run(url_list)
            return json.dumps(result.items, indent=2)[:10000]

        if crawler_type == "beautifulsoup":
            return asyncio.run(_crawlee_beautifulsoup())
        return asyncio.run(_crawlee_playwright())
    except ImportError as e:
        return f"Error: crawlee not installed. Run: pip install crawlee[all]. Details: {e}"
    except Exception as e:
        return f"Crawlee error: {str(e)}"
