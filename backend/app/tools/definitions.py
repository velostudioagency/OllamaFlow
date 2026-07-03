from typing import Any, Dict

from app.tools.search import (
    web_search, web_scraper, web_research, youtube_transcript
)
from app.tools.file_ops import (
    read_file, write_file, list_directory, search_files, file_watcher,
    clipboard_copy, clipboard_paste
)
from app.tools.code import run_code, run_command, calculate
from app.tools.browser import playwright_browser
from app.tools.data import csv_analyze, database_query, json_query, markitdown_convert
from app.tools.network import http_request, send_email, slack_webhook, rate_limiter, rss_read
from app.tools.utils import random_generate, diff_texts, hash_data, get_datetime
from app.tools.advanced import browser_use_tool, crawl4ai_tool, firecrawl_tool, crawlee_tool


TOOL_DEFINITIONS = {
    "web_search": {
        "name": "web_search",
        "description": "Search the web and scrape top results for clean content (Firecrawl-style)",
        "handler": web_search,
        "params": [
            {"name": "query", "type": "string", "required": True, "label": "Search Query"},
            {"name": "num_results", "type": "number", "required": False, "label": "Num Results", "default": 5},
            {"name": "scrape", "type": "boolean", "required": False, "label": "Scrape URLs for full content", "default": True}
        ]
    },
    "web_scraper": {
        "name": "web_scraper",
        "description": "Scrape a webpage and return clean text (strips HTML, scripts, styles — Firecrawl clone)",
        "handler": web_scraper,
        "params": [
            {"name": "url", "type": "string", "required": True, "label": "URL to Scrape"},
            {"name": "max_chars", "type": "number", "required": False, "label": "Max Characters", "default": 8000}
        ]
    },
    "read_file": {
        "name": "read_file",
        "description": "Read the contents of a file (txt, pdf, docx, pptx, csv, xlsx)",
        "handler": read_file,
        "params": [
            {"name": "file_path", "type": "string", "required": True, "label": "File Path"}
        ]
    },
    "write_file": {
        "name": "write_file",
        "description": "Write content to a file",
        "handler": write_file,
        "params": [
            {"name": "file_path", "type": "string", "required": True, "label": "File Path"},
            {"name": "content", "type": "string", "required": True, "label": "Content"}
        ]
    },
    "run_code": {
        "name": "run_code",
        "description": "Execute Python code and return output",
        "handler": run_code,
        "params": [
            {"name": "code", "type": "string", "required": True, "label": "Python Code"}
        ]
    },
    "send_email": {
        "name": "send_email",
        "description": "Send an email via SMTP",
        "handler": send_email,
        "params": [
            {"name": "to", "type": "string", "required": True, "label": "To Email"},
            {"name": "subject", "type": "string", "required": True, "label": "Subject"},
            {"name": "body", "type": "string", "required": True, "label": "Body"},
            {"name": "smtp_server", "type": "string", "required": False, "label": "SMTP Server", "default": "smtp.gmail.com"},
            {"name": "smtp_port", "type": "number", "required": False, "label": "SMTP Port", "default": 587},
            {"name": "username", "type": "string", "required": False, "label": "Username"},
            {"name": "password", "type": "string", "required": False, "label": "Password"}
        ]
    },
    "http_request": {
        "name": "http_request",
        "description": "Make an HTTP request to any REST API",
        "handler": http_request,
        "params": [
            {"name": "url", "type": "string", "required": True, "label": "URL"},
            {"name": "method", "type": "select", "required": True, "label": "Method",
             "options": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
            {"name": "headers", "type": "string", "required": False, "label": "Headers (JSON)"},
            {"name": "body", "type": "string", "required": False, "label": "Body"},
            {"name": "timeout", "type": "number", "required": False, "label": "Timeout (s)", "default": 30}
        ]
    },
    "calculate": {
        "name": "calculate",
        "description": "Evaluate a mathematical expression",
        "handler": calculate,
        "params": [
            {"name": "expression", "type": "string", "required": True, "label": "Expression"}
        ]
    },
    "get_datetime": {
        "name": "get_datetime",
        "description": "Get the current date and time",
        "handler": get_datetime,
        "params": [
            {"name": "format_str", "type": "string", "required": False, "label": "Format",
             "default": "%Y-%m-%d %H:%M:%S"}
        ]
    },
    "run_command": {
        "name": "run_command",
        "description": "Execute a terminal/shell command on the user's PC",
        "handler": run_command,
        "params": [
            {"name": "command", "type": "string", "required": True, "label": "Command"},
            {"name": "working_directory", "type": "string", "required": False, "label": "Working Directory"},
            {"name": "timeout", "type": "number", "required": False, "label": "Timeout (s)", "default": 60}
        ]
    },
    "playwright_browser": {
        "name": "playwright_browser",
        "description": "Browse the web using Playwright (Chromium, Chrome, Brave, Edge, Firefox, WebKit)",
        "handler": playwright_browser,
        "params": [
            {"name": "action", "type": "select", "required": True, "label": "Action",
             "options": ["goto", "click", "type", "extract", "screenshot", "evaluate"]},
            {"name": "url", "type": "string", "required": False, "label": "URL"},
            {"name": "browser", "type": "select", "required": False, "label": "Browser", "default": "chrome",
             "options": ["chrome", "brave", "msedge", "chromium", "firefox", "webkit"]},
            {"name": "selector", "type": "string", "required": False, "label": "CSS Selector"},
            {"name": "text", "type": "string", "required": False, "label": "Text / JS Code"},
            {"name": "screenshot", "type": "string", "required": False, "label": "Screenshot Path"},
            {"name": "wait_seconds", "type": "number", "required": False, "label": "Wait (s)", "default": 3}
        ]
    },
    "list_directory": {
        "name": "list_directory",
        "description": "List files and folders in a directory with sizes",
        "handler": list_directory,
        "params": [
            {"name": "path", "type": "string", "required": False, "label": "Directory Path"},
            {"name": "pattern", "type": "string", "required": False, "label": "Glob Pattern", "default": ""}
        ]
    },
    "search_files": {
        "name": "search_files",
        "description": "Search for files by name pattern or grep content across files",
        "handler": search_files,
        "params": [
            {"name": "query", "type": "string", "required": True, "label": "Search Query"},
            {"name": "path", "type": "string", "required": False, "label": "Search Directory"},
            {"name": "search_type", "type": "select", "required": False, "label": "Search Type",
             "options": ["name", "content"], "default": "name"}
        ]
    },
    "json_query": {
        "name": "json_query",
        "description": "Extract values from JSON using dot-notation path (e.g. data.users.0.name)",
        "handler": json_query,
        "params": [
            {"name": "data", "type": "textarea", "required": True, "label": "JSON Data"},
            {"name": "query", "type": "string", "required": True, "label": "Query Path"}
        ]
    },
    "csv_analyze": {
        "name": "csv_analyze",
        "description": "Analyze CSV files - summary stats, filter, sort, group by columns",
        "handler": csv_analyze,
        "params": [
            {"name": "file_path", "type": "string", "required": True, "label": "CSV File Path"},
            {"name": "operation", "type": "select", "required": True, "label": "Operation",
             "options": ["summary", "head", "filter", "sort", "group"], "default": "summary"},
            {"name": "column", "type": "string", "required": False, "label": "Column Name"},
            {"name": "filter_value", "type": "string", "required": False, "label": "Filter / Sort Direction"},
            {"name": "limit", "type": "number", "required": False, "label": "Row Limit", "default": 20}
        ]
    },
    "database_query": {
        "name": "database_query",
        "description": "Execute SQL queries against a SQLite database",
        "handler": database_query,
        "params": [
            {"name": "db_path", "type": "string", "required": True, "label": "Database Path"},
            {"name": "query", "type": "textarea", "required": True, "label": "SQL Query"},
            {"name": "params", "type": "string", "required": False, "label": "Bind Parameters (JSON array)"}
        ]
    },
    "random_generate": {
        "name": "random_generate",
        "description": "Generate random UUIDs, passwords, numbers, or strings",
        "handler": random_generate,
        "params": [
            {"name": "type", "type": "select", "required": True, "label": "Type",
             "options": ["uuid", "password", "number", "string"], "default": "uuid"},
            {"name": "length", "type": "number", "required": False, "label": "Length", "default": 16},
            {"name": "count", "type": "number", "required": False, "label": "Count", "default": 1}
        ]
    },
    "diff_texts": {
        "name": "diff_texts",
        "description": "Compare two texts and show unified diff",
        "handler": diff_texts,
        "params": [
            {"name": "text_a", "type": "textarea", "required": True, "label": "Text A"},
            {"name": "text_b", "type": "textarea", "required": True, "label": "Text B"},
            {"name": "context_lines", "type": "number", "required": False, "label": "Context Lines", "default": 3}
        ]
    },
    "hash_data": {
        "name": "hash_data",
        "description": "Generate SHA256, SHA1, or MD5 hash of data",
        "handler": hash_data,
        "params": [
            {"name": "data", "type": "string", "required": True, "label": "Data to Hash"},
            {"name": "algorithm", "type": "select", "required": False, "label": "Algorithm",
             "options": ["sha256", "sha1", "md5"], "default": "sha256"}
        ]
    },
    "rss_read": {
        "name": "rss_read",
        "description": "Read and parse RSS/Atom feeds",
        "handler": rss_read,
        "params": [
            {"name": "url", "type": "string", "required": True, "label": "Feed URL"},
            {"name": "max_items", "type": "number", "required": False, "label": "Max Items", "default": 10}
        ]
    },
    "slack_webhook": {
        "name": "slack_webhook",
        "description": "Send a message to Slack via incoming webhook",
        "handler": slack_webhook,
        "params": [
            {"name": "webhook_url", "type": "string", "required": True, "label": "Webhook URL"},
            {"name": "message", "type": "string", "required": True, "label": "Message"},
            {"name": "channel", "type": "string", "required": False, "label": "Channel Override"},
            {"name": "username", "type": "string", "required": False, "label": "Bot Username", "default": "OllamaFlow"}
        ]
    },
    "web_research": {
        "name": "web_research",
        "description": "Search the web and scrape pages using Playwright + Brave browser to bypass anti-bot defenses (403/429 errors)",
        "handler": web_research,
        "params": [
            {"name": "action", "type": "select", "required": True, "label": "Action",
             "options": ["search", "search_and_scrape", "goto", "extract", "screenshot", "click", "type", "evaluate"]},
            {"name": "query", "type": "string", "required": False, "label": "Search Query / JS Code"},
            {"name": "url", "type": "string", "required": False, "label": "URL"},
            {"name": "engine", "type": "select", "required": False, "label": "Search Engine", "default": "google",
             "options": ["google", "bing", "duckduckgo", "brave"]},
            {"name": "max_results", "type": "number", "required": False, "label": "Max Results", "default": 5},
            {"name": "selector", "type": "string", "required": False, "label": "CSS Selector (for extract/click/type)"},
            {"name": "screenshot", "type": "string", "required": False, "label": "Screenshot Path"},
            {"name": "wait_seconds", "type": "number", "required": False, "label": "Wait (s)", "default": 3}
        ]
    },
    "youtube_transcript": {
        "name": "youtube_transcript",
        "description": "Extract transcript/subtitles from a YouTube video",
        "handler": youtube_transcript,
        "params": [
            {"name": "video_url", "type": "string", "required": True, "label": "YouTube Video URL"},
            {"name": "language", "type": "string", "required": False, "label": "Language Code", "default": "en"}
        ]
    },
    "clipboard_copy": {
        "name": "clipboard_copy",
        "description": "Copy text to the system clipboard",
        "handler": clipboard_copy,
        "params": [
            {"name": "text", "type": "string", "required": True, "label": "Text to Copy"}
        ]
    },
    "clipboard_paste": {
        "name": "clipboard_paste",
        "description": "Read text from the system clipboard",
        "handler": clipboard_paste,
        "params": []
    },
    "rate_limiter": {
        "name": "rate_limiter",
        "description": "Rate-limit API calls with sliding window (in-memory)",
        "handler": rate_limiter,
        "params": [
            {"name": "max_requests", "type": "number", "required": False, "label": "Max Requests", "default": 10},
            {"name": "window_seconds", "type": "number", "required": False, "label": "Window (seconds)", "default": 60},
            {"name": "bucket", "type": "string", "required": False, "label": "Bucket Name", "default": "default"}
        ]
    },
    "file_watcher": {
        "name": "file_watcher",
        "description": "List recently modified files in a directory",
        "handler": file_watcher,
        "params": [
            {"name": "path", "type": "string", "required": False, "label": "Directory Path"},
            {"name": "pattern", "type": "string", "required": False, "label": "Glob Pattern", "default": "*"},
            {"name": "action", "type": "select", "required": False, "label": "Action", "options": ["list_changes"], "default": "list_changes"},
            {"name": "since_minutes", "type": "number", "required": False, "label": "Since (minutes)", "default": 60}
        ]
    },
    "browser_use": {
        "name": "browser_use",
        "description": "AI-driven browser agent — give it a natural language task and it automates the web autonomously",
        "handler": browser_use_tool,
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
}


def execute_tool(tool_name: str, params: Dict[str, Any]) -> str:
    if tool_name not in TOOL_DEFINITIONS:
        return f"Error: Unknown tool '{tool_name}'"
    tool = TOOL_DEFINITIONS[tool_name]
    try:
        return tool["handler"](**params)
    except TypeError as e:
        return f"Error: Invalid parameters for {tool_name}: {str(e)}"
    except Exception as e:
        return f"Tool error ({tool_name}): {str(e)}"


def get_tools_list() -> list:
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "params": t["params"]
        }
        for t in TOOL_DEFINITIONS.values()
    ]



