import os
import json
import math
import datetime
import requests
import subprocess
import tempfile
from typing import Any, Dict, Optional
from pathlib import Path

WORKSPACE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)


def web_search(query: str, num_results: int = 5) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
        if not results:
            return "No results found."
        output_lines = []
        for i, r in enumerate(results, 1):
            output_lines.append(f"{i}. {r.get('title', 'No title')}")
            output_lines.append(f"   URL: {r.get('href', 'N/A')}")
            output_lines.append(f"   {r.get('body', 'No description')}")
            output_lines.append("")
        return "\n".join(output_lines)
    except Exception as e:
        return f"Search error: {str(e)}"


def read_file(file_path: str, **kwargs) -> str:
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(WORKSPACE_DIR) / file_path
        if not path.exists():
            return f"Error: File not found: {file_path}"
        suffix = path.suffix.lower()
        if suffix == ".txt" or suffix == ".md" or suffix == ".py" or suffix == ".json" or suffix == ".csv":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            if len(content) > 10000:
                content = content[:10000] + "\n... [truncated]"
            return content
        elif suffix == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                text_parts = []
                for page in reader.pages[:20]:
                    text_parts.append(page.extract_text() or "")
                return "\n".join(text_parts)[:10000]
            except ImportError:
                return "Error: pypdf not installed"
        elif suffix == ".docx":
            try:
                from docx import Document
                doc = Document(str(path))
                return "\n".join([p.text for p in doc.paragraphs])[:10000]
            except ImportError:
                return "Error: python-docx not installed"
        elif suffix in [".xlsx", ".xls"]:
            try:
                import pandas as pd
                df = pd.read_excel(str(path))
                return df.to_string()[:10000]
            except ImportError:
                return "Error: openpyxl not installed"
        else:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()[:10000]
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(file_path: str, content: str, **kwargs) -> str:
    try:
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(WORKSPACE_DIR) / file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def run_code(code: str, **kwargs) -> str:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=WORKSPACE_DIR) as f:
            f.write(code)
            temp_path = f.name
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORKSPACE_DIR
        )
        os.unlink(temp_path)
        output = result.stdout
        if result.stderr:
            output += "\nSTDERR:\n" + result.stderr
        if not output.strip():
            output = "Code executed successfully (no output)."
        return output[:5000]
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (30s limit)"
    except Exception as e:
        return f"Error running code: {str(e)}"


def send_email(to: str, subject: str, body: str, smtp_server: str = "smtp.gmail.com",
               smtp_port: int = 587, username: str = "", password: str = "", **kwargs) -> str:
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = username
        msg["To"] = to
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)
        return f"Email sent to {to}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


def http_request(url: str, method: str = "GET", headers: str = "",
                 body: str = "", timeout: int = 30, **kwargs) -> str:
    try:
        parsed_headers = {}
        if headers:
            try:
                parsed_headers = json.loads(headers) if isinstance(headers, str) else headers
            except json.JSONDecodeError:
                for line in headers.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        parsed_headers[k.strip()] = v.strip()
        kwargs_req = {
            "url": url,
            "headers": parsed_headers,
            "timeout": timeout
        }
        if method.upper() == "POST":
            kwargs_req["data"] = body
        elif method.upper() == "PUT":
            kwargs_req["data"] = body
        response = requests.request(method.upper(), **kwargs_req)
        content = response.text[:10000]
        return f"Status: {response.status_code}\n\n{content}"
    except Exception as e:
        return f"HTTP request error: {str(e)}"


def calculate(expression: str, **kwargs) -> str:
    try:
        allowed_names = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sum": sum, "len": len, "int": int, "float": float,
            "pi": math.pi, "e": math.e, "sqrt": math.sqrt,
            "pow": pow, "log": math.log, "sin": math.sin,
            "cos": math.cos, "tan": math.tan, "ceil": math.ceil,
            "floor": math.floor
        }
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"


def run_command(command: str, working_directory: str = "", timeout: int = 60, **kwargs) -> str:
    try:
        import sys
        is_windows = sys.platform == "win32"
        if is_windows:
            shell_cmd = ["cmd", "/c", command]
        else:
            shell_cmd = ["bash", "-c", command]
        if working_directory and Path(working_directory).is_dir():
            cwd = working_directory
        else:
            cwd = WORKSPACE_DIR
        result = subprocess.run(
            shell_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        if not output.strip():
            output = "Command executed successfully (no output)."
        exit_code = result.returncode
        return f"Exit Code: {exit_code}\n\n{output[:8000]}"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s"
    except FileNotFoundError:
        return f"Error: Shell not found. Command: {command}"
    except Exception as e:
        return f"Error running command: {str(e)}"


def get_datetime(format_str: str = "%Y-%m-%d %H:%M:%S", **kwargs) -> str:
    return datetime.datetime.now().strftime(format_str)


def playwright_browser(action: str = "goto", url: str = "", browser: str = "chrome",
                       selector: str = "", text: str = "", screenshot: str = "",
                       wait_seconds: int = 3, **kwargs) -> str:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_type = p.chromium
            if browser == "brave":
                brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
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


TOOL_DEFINITIONS = {
    "web_search": {
        "name": "web_search",
        "description": "Search the web using multiple engines (DuckDuckGo, Brave, Bing, etc.)",
        "handler": web_search,
        "params": [
            {"name": "query", "type": "string", "required": True, "label": "Search Query"},
            {"name": "num_results", "type": "number", "required": False, "label": "Num Results", "default": 5}
        ]
    },
    "read_file": {
        "name": "read_file",
        "description": "Read the contents of a file (txt, pdf, docx, csv, xlsx)",
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
    }
}


def execute_tool(tool_name: str, params: Dict[str, Any]) -> str:
    if tool_name not in TOOL_DEFINITIONS:
        return f"Error: Unknown tool '{tool_name}'"
    tool = TOOL_DEFINITIONS[tool_name]
    try:
        return tool["handler"](**params)
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
