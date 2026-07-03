# Web Scraping & Crawling Tools Integration Plan

> Integrate browser-use, crawl4ai, firecrawl, crawlee, and markitdown into OllamaFlow
> Created: 2026-06-30

---

## Browser-Use vs Playwright — Key Difference

| Aspect | Playwright | Browser-use |
|--------|-----------|-------------|
| Control | Explicit code per action | Natural language task description |
| Intelligence | None — you script everything | LLM-powered decision making |
| Use case | Reliable, predictable automation | Complex, adaptive web tasks |
| Anti-bot | Manual stealth setup | Built-in stealth + fingerprinting |
| Multi-step | You write the flow | Agent figures out the flow |
| Example | `page.goto(url); page.click("button")` | `Agent(task="buy groceries from this list", llm=...)` |

**Playwright** is a low-level browser automation API (click, type, navigate, screenshot).
**Browser-use** is an AI agent layer on top of Playwright that uses LLMs to decide what to do.

---

## Integration Overview

| # | Tool Name | Library | Purpose | Mode |
|---|-----------|---------|---------|------|
| 1 | `browser_use` | browser-use | AI-driven browser agent for complex web tasks | Local (needs LLM) |
| 2 | `crawl4ai` | crawl4ai | LLM-friendly web crawling with markdown output | Local Python |
| 3 | `firecrawl` | firecrawl-py | Web scraping API | Self-hosted Docker + Cloud API |
| 4 | `crawlee` | crawlee | Anti-bot scraping with proxy rotation | Local Python |
| 5 | `markitdown` | markitdown | Convert files (PDF, Office, images, audio) to Markdown | Local Python |

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/requirements.txt` | Add 5 new dependencies |
| `backend/tool_library.py` | Add 5 tool handler functions + TOOL_DEFINITIONS entries |
| `backend/settings_manager.py` | Add Firecrawl config (API key, self-hosted URL, mode) |
| `backend/main.py` | Add Firecrawl settings endpoint if needed |
| `.env.example` | Document new env vars |
| `docker-compose.yml` | Add optional Firecrawl service |

No frontend changes needed — tool params are dynamically rendered from TOOL_DEFINITIONS.

---

## Step 1: Update `backend/requirements.txt`

Add the following lines:

```
browser-use
crawl4ai
firecrawl-py
crawlee[all]
markitdown[all]
```

### Notes
- `crawl4ai` pulls in Playwright (already installed)
- `crawlee[all]` includes BeautifulSoup, Playwright, and Parsel crawlers
- `markitdown[all]` includes PDF, DOCX, PPTX, XLSX, audio, YouTube support
- `browser-use` pulls in Playwright and LangChain integrations

---

## Step 2: Add Tool Handlers in `backend/tool_library.py`

### 2a. `browser_use` — AI Browser Agent

**What it does**: Give the agent a natural language task and it autonomously navigates, clicks, types, and extracts data using an LLM.

**Params**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `task` | string | Yes | Natural language task description |
| `llm_provider` | select | Yes | `ollama`, `openai`, `anthropic` |
| `llm_model` | string | No | Model name (default: provider's default) |
| `headless` | boolean | No | Run headless (default: true) |
| `allowed_domains` | string | No | Comma-separated domain whitelist |
| `max_steps` | number | No | Max agent steps (default: 25) |

**Implementation approach**:
```python
def browser_use(task, llm_provider="ollama", llm_model="", headless=True,
                allowed_domains="", max_steps=25, **kwargs):
    from browser_use import Agent
    from langchain_ollama import ChatOllama
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic

    # Build LLM based on provider
    if llm_provider == "ollama":
        llm = ChatOllama(model=llm_model or "llama3.1:8b")
    elif llm_provider == "openai":
        llm = ChatOpenAI(model=llm_model or "gpt-4o")
    elif llm_provider == "anthropic":
        llm = ChatAnthropic(model=llm_model or "claude-sonnet-4-20250514")

    # Parse allowed domains
    domains = [d.strip() for d in allowed_domains.split(",") if d.strip()] if allowed_domains else None

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
```

**Handler type**: Async (runs in async context via node_registry)

---

### 2b. `crawl4ai` — LLM-Friendly Web Crawler

**What it does**: Crawls URLs and returns clean, structured Markdown optimized for LLM consumption. Supports deep crawling, anti-bot detection, and structured data extraction.

**Params**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | select | Yes | `scrape`, `deep_crawl`, `extract_structured` |
| `url` | string | Yes | Target URL |
| `max_pages` | number | No | Max pages for deep_crawl (default: 5) |
| `css_selector` | string | No | CSS selector for targeted extraction |
| `javascript` | string | No | JS to execute before extraction |
| `cache` | boolean | No | Enable caching (default: true) |
| `fit_markdown` | boolean | No | Return noise-filtered fit_markdown (default: true) |

**Implementation approach**:
```python
def crawl4ai(action="scrape", url="", max_pages=5, css_selector="",
             javascript="", cache=True, fit_markdown=True, **kwargs):
    import asyncio
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

    async def _crawl():
        browser_config = BrowserConfig(headless=True)
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.ENABLED if cache else CacheMode.BYPASS,
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)

            if fit_markdown and result.markdown.fit_markdown:
                return result.markdown.fit_markdown
            return result.markdown.raw_markdown

    return asyncio.run(_crawl())
```

**Deep crawl variant**: Use `BFSDeepCrawlStrategy` or `DFSDeepCrawlStrategy` from `crawl4ai.deep_crawling`.

**Structured extraction**: Use `JsonCssExtractionStrategy` with a schema for CSS-based extraction, or `LLMExtractionStrategy` for LLM-powered extraction.

---

### 2c. `firecrawl` — Web Scraping API

**What it does**: API-first web scraping with search, crawl, map, and AI agent endpoints. Supports self-hosted Docker server and cloud API.

**Params**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | select | Yes | `scrape`, `crawl`, `map`, `search`, `agent` |
| `url` | string | No | Target URL (required for scrape/crawl/map) |
| `query` | string | No | Search query (for search/agent actions) |
| `limit` | number | No | Max results/pages (default: 10) |
| `formats` | select | No | Output format: `markdown`, `html` (default: markdown) |
| `mode` | select | No | `self_hosted` or `cloud` (default: from settings) |

**Implementation approach**:
```python
def firecrawl(action="scrape", url="", query="", limit=10,
              formats="markdown", mode="", **kwargs):
    from firecrawl import Firecrawl
    from settings_manager import settings_manager

    # Resolve mode from settings
    if not mode:
        mode = settings_manager.get("firecrawl_mode", "self_hosted")

    if mode == "self_hosted":
        base_url = settings_manager.get("firecrawl_url", "http://localhost:3001")
        app = Firecrawl(api_url=base_url)
    else:
        api_key = settings_manager.get("firecrawl_api_key", "")
        if not api_key:
            return "Error: Firecrawl API key not configured. Set firecrawl_api_key in Settings."
        app = Firecrawl(api_key=api_key)

    if action == "scrape":
        result = app.scrape(url, formats=[formats])
        return result.markdown if formats == "markdown" else result.html
    elif action == "crawl":
        result = app.crawl(url, limit=limit, scrape_options={"formats": [formats]})
        return "\n\n---\n\n".join([d.markdown for d in result.data])
    elif action == "map":
        result = app.map(url)
        return json.dumps(result.links, indent=2)
    elif action == "search":
        result = app.search(query, limit=limit)
        return json.dumps([{"title": r.title, "url": r.url, "markdown": r.markdown} for r in result.data.web], indent=2)
    elif action == "agent":
        result = app.agent(prompt=query)
        return result.data.result
```

**Self-hosted mode**: Connects to local Firecrawl Docker server at configured URL.
**Cloud mode**: Uses firecrawl.dev API with API key.

---

### 2d. `crawlee` — Anti-Bot Web Scraping

**What it does**: Production-grade scraping with built-in proxy rotation, browser fingerprint spoofing, automatic retries, and queue management. Appears human-like by default.

**Params**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | select | Yes | `scrape_urls`, `deep_crawl` |
| `urls` | string | Yes | Comma-separated URLs to scrape |
| `max_requests` | number | No | Max total requests (default: 10) |
| `crawler_type` | select | No | `playwright` (JS rendering) or `beautifulsoup` (fast HTTP) (default: playwright) |
| `proxy_url` | string | No | Proxy URL for rotation |
| `javascript_code` | string | No | JS to execute on pages (Playwright only) |

**Implementation approach**:
```python
def crawlee(action="scrape_urls", urls="", max_requests=10, crawler_type="playwright",
            proxy_url="", javascript_code="", **kwargs):
    import asyncio
    from crawlee.crawlers import PlaywrightCrawler, BeautifulSoupCrawler

    url_list = [u.strip() for u in urls.split(",") if u.strip()]

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
```

---

### 2e. `markitdown` — File to Markdown Converter

**What it does**: Convert PDFs, Word docs, PowerPoint, Excel, images (OCR), audio (transcription), HTML, CSV, JSON, ZIP, YouTube URLs, and EPUBs to clean Markdown.

**Params**:
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `file_path` | string | Yes | Path to local file |
| `input_type` | select | No | `local_file` or `url` (default: local_file) |
| `url` | string | No | URL to convert (when input_type is url) |
| `use_llm` | boolean | No | Use LLM for image descriptions (default: false) |
| `llm_model` | string | No | LLM model for image descriptions |

**Implementation approach**:
```python
def markitdown_convert(file_path="", input_type="local_file", url="",
                       use_llm=False, llm_model="", **kwargs):
    from markitdown import MarkItDown

    kwargs_markitdown = {}
    if use_llm and llm_model:
        from openai import OpenAI
        kwargs_markitdown["llm_client"] = OpenAI()
        kwargs_markitdown["llm_model"] = llm_model

    md = MarkItDown(**kwargs_markitdown)

    if input_type == "url" and url:
        result = md.convert_url(url)
    elif file_path:
        result = md.convert(file_path)
    else:
        return "Error: Provide file_path or url"

    return result.text_content
```

**Handler type**: Sync (simple file conversion)

---

## Step 3: TOOL_DEFINITIONS Entries

Add to the `TOOL_DEFINITIONS` dict in `tool_library.py`:

```python
"browser_use": {
    "name": "browser_use",
    "description": "AI-driven browser agent — give it a natural language task and it automates the web autonomously",
    "handler": browser_use,
    "params": [
        {"name": "task", "type": "textarea", "required": True, "label": "Task Description"},
        {"name": "llm_provider", "type": "select", "required": True, "label": "LLM Provider",
         "options": ["ollama", "openai", "anthropic"]},
        {"name": "llm_model", "type": "string", "required": False, "label": "Model (blank = default)"},
        {"name": "headless", "type": "boolean", "required": False, "label": "Headless Mode", "default": True},
        {"name": "allowed_domains", "type": "string", "required": False, "label": "Allowed Domains (comma-separated)"},
        {"name": "max_steps", "type": "number", "required": False, "label": "Max Steps", "default": 25}
    ]
},
"crawl4ai": {
    "name": "crawl4ai",
    "description": "LLM-friendly web crawler — returns clean Markdown optimized for AI. Supports deep crawling and anti-bot detection",
    "handler": crawl4ai_tool,
    "params": [
        {"name": "action", "type": "select", "required": True, "label": "Action",
         "options": ["scrape", "deep_crawl", "extract_structured"]},
        {"name": "url", "type": "string", "required": True, "label": "URL"},
        {"name": "max_pages", "type": "number", "required": False, "label": "Max Pages (deep crawl)", "default": 5},
        {"name": "css_selector", "type": "string", "required": False, "label": "CSS Selector"},
        {"name": "javascript", "type": "textarea", "required": False, "label": "JavaScript to Execute"},
        {"name": "cache", "type": "boolean", "required": False, "label": "Enable Caching", "default": True},
        {"name": "fit_markdown", "type": "boolean", "required": False, "label": "Filter Noise (fit_markdown)", "default": True}
    ]
},
"firecrawl": {
    "name": "firecrawl",
    "description": "Web scraping API — scrape, crawl, map, search, or use AI agent. Supports self-hosted Docker and cloud",
    "handler": firecrawl_tool,
    "params": [
        {"name": "action", "type": "select", "required": True, "label": "Action",
         "options": ["scrape", "crawl", "map", "search", "agent"]},
        {"name": "url", "type": "string", "required": False, "label": "URL"},
        {"name": "query", "type": "string", "required": False, "label": "Search Query / Agent Prompt"},
        {"name": "limit", "type": "number", "required": False, "label": "Limit", "default": 10},
        {"name": "formats", "type": "select", "required": False, "label": "Output Format",
         "options": ["markdown", "html"], "default": "markdown"},
        {"name": "mode", "type": "select", "required": False, "label": "Mode",
         "options": ["self_hosted", "cloud"], "default": "self_hosted"}
    ]
},
"crawlee": {
    "name": "crawlee",
    "description": "Anti-bot web scraping with proxy rotation, fingerprint spoofing, and automatic retries. Appears human-like",
    "handler": crawlee_tool,
    "params": [
        {"name": "action", "type": "select", "required": True, "label": "Action",
         "options": ["scrape_urls", "deep_crawl"]},
        {"name": "urls", "type": "string", "required": True, "label": "URLs (comma-separated)"},
        {"name": "max_requests", "type": "number", "required": False, "label": "Max Requests", "default": 10},
        {"name": "crawler_type", "type": "select", "required": False, "label": "Crawler Type",
         "options": ["playwright", "beautifulsoup"], "default": "playwright"},
        {"name": "proxy_url", "type": "string", "required": False, "label": "Proxy URL"},
        {"name": "javascript_code", "type": "textarea", "required": False, "label": "JavaScript to Execute"}
    ]
},
"markitdown": {
    "name": "markitdown",
    "description": "Convert files to Markdown — PDF, Word, PowerPoint, Excel, images (OCR), audio (transcription), HTML, YouTube",
    "handler": markitdown_convert,
    "params": [
        {"name": "file_path", "type": "string", "required": False, "label": "File Path"},
        {"name": "input_type", "type": "select", "required": False, "label": "Input Type",
         "options": ["local_file", "url"], "default": "local_file"},
        {"name": "url", "type": "string", "required": False, "label": "URL (for url input type)"},
        {"name": "use_llm", "type": "boolean", "required": False, "label": "Use LLM for Image Descriptions", "default": False},
        {"name": "llm_model", "type": "string", "required": False, "label": "LLM Model (for images)"}
    ]
}
```

---

## Step 4: Update Settings Manager

Add new config keys to `backend/settings_manager.py`:

```python
# Firecrawl configuration
"firecrawl_url": "http://localhost:3001",      # Self-hosted Docker URL
"firecrawl_api_key": "",                        # Cloud API key (optional)
"firecrawl_mode": "self_hosted",                # "self_hosted" or "cloud"
```

Add these to the default settings dict and expose them in the Settings UI.

---

## Step 5: Update `.env.example`

Add:

```bash
# Firecrawl (self-hosted Docker or cloud API)
FIRECRAWL_URL=http://localhost:3001
FIRECRAWL_API_KEY=fc-your-api-key-here
FIRECRAWL_MODE=self_hosted

# Browser-use (LLM provider for AI browser agent)
BROWSER_USE_LLM_PROVIDER=ollama
BROWSER_USE_LLM_MODEL=llama3.1:8b
```

---

## Step 6: Update `docker-compose.yml` (Optional)

Add Firecrawl as an optional service:

```yaml
firecrawl:
  image: ghcr.io/mendableai/firecrawl:latest
  ports:
    - "3001:3001"
  environment:
    - PORT=3001
    - FIRECRAWL_REDIS_URL=redis://redis:6379
  depends_on:
    - redis
  profiles:
    - firecrawl

redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  profiles:
    - firecrawl
```

To start with Firecrawl: `docker compose --profile firecrawl up`
Without Firecrawl: `docker compose up` (unchanged behavior)

---

## Implementation Order

| Order | Task | Est. Effort | Dependencies |
|-------|------|-------------|-------------|
| 1 | Update `requirements.txt` | 5 min | None |
| 2 | Add `markitdown` tool | 30 min | requirements.txt |
| 3 | Add `crawl4ai` tool | 45 min | requirements.txt |
| 4 | Add `crawlee` tool | 45 min | requirements.txt |
| 5 | Update `settings_manager.py` for Firecrawl config | 15 min | None |
| 6 | Add `firecrawl` tool | 45 min | settings_manager |
| 7 | Add `browser_use` tool | 60 min | requirements.txt |
| 8 | Update `.env.example` | 5 min | None |
| 9 | Update `docker-compose.yml` | 10 min | None |
| 10 | Test all tools end-to-end | 60 min | All above |
| 11 | Run lint/typecheck | 10 min | All above |

**Total estimated effort**: ~5.5 hours

---

## Testing Checklist

- [ ] `markitdown` converts a PDF to markdown
- [ ] `markitdown` converts a Word doc to markdown
- [ ] `markitdown` converts an image to markdown (with OCR)
- [ ] `crawl4ai` scrapes a single URL and returns clean markdown
- [ ] `crawl4ai` deep crawls a site (BFS strategy)
- [ ] `crawlee` scrapes multiple URLs with Playwright crawler
- [ ] `crawlee` scrapes with BeautifulSoup crawler (faster, no JS)
- [ ] `firecrawl` self-hosted scrapes a URL (requires Docker)
- [ ] `firecrawl` cloud searches the web (requires API key)
- [ ] `firecrawl` agent performs autonomous data gathering
- [ ] `browser_use` completes a simple task with Ollama
- [ ] `browser_use` completes a task with OpenAI/Anthropic
- [ ] All tools appear in the Tool Node dropdown in the UI
- [ ] Tool params render correctly in ConfigPanel
- [ ] Workflows using new tools execute successfully
- [ ] No import errors on startup (graceful handling if deps missing)

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| browser-use requires cloud LLM API key | Medium | Default to Ollama (local, free). Cloud providers are optional. |
| crawl4ai installs large Playwright browsers | Low | Already installed by existing OllamaFlow |
| Firecrawl Docker uses significant RAM | Medium | Make it optional via Docker profiles. Document in README. |
| crawlee Python has many optional deps | Low | Use `crawlee[all]`, handle ImportError gracefully |
| Async tool handlers conflict with sync pattern | Medium | Use `asyncio.run()` wrapper for async tools (same pattern as existing code) |
| Import errors if deps not installed | Medium | Wrap imports in try/except with clear error messages |

---

## Tool Comparison Matrix

| Feature | browser_use | crawl4ai | firecrawl | crawlee | markitdown |
|---------|-------------|----------|-----------|---------|------------|
| Primary use | AI browser agent | LLM-friendly crawl | API scraping | Anti-bot scraping | File conversion |
| LLM integration | Built-in | Optional | Agent endpoint | No | Optional (OCR) |
| Anti-bot | Yes | Yes | Yes (cloud) | Yes (best) | N/A |
| Deep crawl | No | Yes | Yes | Yes | N/A |
| Proxy rotation | Via browser profile | Via config | Via cloud | Built-in | N/A |
| Markdown output | No (raw result) | Yes (optimized) | Yes | No (raw HTML) | Yes |
| Structured extraction | Via LLM | CSS/LLM | Schema | No | N/A |
| Async | Yes | Yes | Sync SDK | Yes | Sync |
| Docker support | No | Yes | Yes | No | No |
| Self-hosted | Yes | Yes | Yes | Yes | Yes |
| Cloud API | Optional | Beta | Yes | Optional (Apify) | No |
