import os
from typing import Any, Dict

from app.core.config import WORKSPACE_DIR


def _get_browser_path() -> str:
    """Get browser executable path from settings or env var."""
    try:
        from settings_manager import settings_manager
        path = settings_manager.get("browser_path", "")
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    env_path = os.environ.get("OLLAMAFLOW_BROWSER_PATH", "")
    if env_path and os.path.exists(env_path):
        return env_path
    brave_paths = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
        "/usr/bin/brave-browser",
        "/usr/bin/brave",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    for p in brave_paths:
        if os.path.exists(p):
            return p
    return ""


def playwright_browser(action: str = "goto", url: str = "", browser: str = "chrome",
                       selector: str = "", text: str = "", screenshot: str = "",
                       wait_seconds: int = 3, **kwargs) -> str:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_type = p.chromium
            if browser == "brave":
                brave_path = _get_browser_path()
                if not brave_path:
                    return "Error: Brave browser not found. Set browser_path in Settings or OLLAMAFLOW_BROWSER_PATH env var."
                launch_opts = {"headless": True, "executable_path": brave_path}
            elif browser == "msedge":
                launch_opts = {"headless": True, "channel": "msedge"}
            elif browser == "firefox":
                browser_type = p.firefox
                launch_opts = {"headless": True}
            elif browser == "webkit":
                browser_type = p.webkit
                launch_opts = {"headless": True}
            else:
                launch_opts = {"headless": True, "channel": "chrome"}

            pw_browser = browser_type.launch(**launch_opts)
            page = pw_browser.new_page()

            if url and not url.startswith(("http://", "https://")):
                url = "https://" + url

            if action == "goto" and url:
                page.goto(url, timeout=30000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                title = page.title()
                content = page.content()[:15000]
                pw_browser.close()
                return f"Title: {title}\n\n{content}"

            elif action == "click" and selector:
                page.goto(url, timeout=30000) if url else None
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                page.click(selector)
                page.wait_for_timeout(wait_seconds * 1000)
                content = page.content()[:15000]
                pw_browser.close()
                return f"Clicked: {selector}\n\n{content}"

            elif action == "type" and selector and text:
                page.goto(url, timeout=30000) if url else None
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                page.fill(selector, text)
                content = page.content()[:15000]
                pw_browser.close()
                return f"Typed into: {selector}\n\n{content}"

            elif action == "extract" and selector:
                page.goto(url, timeout=30000) if url else None
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                elements = page.query_selector_all(selector)
                texts = [el.inner_text() for el in elements[:20]]
                pw_browser.close()
                return f"Extracted {len(texts)} elements:\n" + "\n---\n".join(texts)

            elif action == "screenshot":
                page.goto(url, timeout=30000) if url else None
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(3000)
                screenshot_path = screenshot or "screenshot.png"
                if not os.path.isabs(screenshot_path):
                    screenshot_path = os.path.join(WORKSPACE_DIR, screenshot_path)
                page.screenshot(path=screenshot_path, full_page=True)
                pw_browser.close()
                return f"Screenshot saved to: {screenshot_path}"

            elif action == "evaluate" and text:
                page.goto(url, timeout=30000) if url else None
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                page.wait_for_timeout(2000)
                result = page.evaluate(text)
                pw_browser.close()
                return f"Result: {str(result)[:5000]}"

            else:
                pw_browser.close()
                return f"Error: Invalid action '{action}' or missing parameters. Actions: goto, click, type, extract, screenshot, evaluate"

    except Exception as e:
        return f"Browser error: {str(e)}"
