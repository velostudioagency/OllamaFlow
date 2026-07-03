import json
import time as _time
from typing import Dict

import requests

from app.core.config import WORKSPACE_DIR


_rate_limit_buckets = {}


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


def slack_webhook(webhook_url: str, message: str, channel: str = "",
                  username: str = "OllamaFlow", **kwargs) -> str:
    try:
        payload = {"text": message, "username": username}
        if channel:
            payload["channel"] = channel
        resp = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        if resp.status_code == 200:
            return f"Message sent successfully via Slack webhook"
        else:
            return f"Slack webhook error: Status {resp.status_code} - {resp.text[:500]}"
    except Exception as e:
        return f"Slack webhook error: {str(e)}"


def rss_read(url: str, max_items: int = 10, **kwargs) -> str:
    try:
        import feedparser
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            return f"Error parsing feed: {feed.bozo_exception}"
        title = feed.feed.get("title", "Unknown Feed")
        lines = [f"Feed: {title}", f"URL: {url}", ""]
        for i, entry in enumerate(feed.entries[:max_items], 1):
            entry_title = entry.get("title", "No title")
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))
            summary = entry.get("summary", "")[:200]
            lines.append(f"{i}. {entry_title}")
            if published:
                lines.append(f"   Date: {published}")
            if link:
                lines.append(f"   Link: {link}")
            if summary:
                lines.append(f"   {summary}")
            lines.append("")
        return "\n".join(lines)[:10000]
    except ImportError:
        return "Error: feedparser not installed. Run: pip install feedparser"
    except Exception as e:
        return f"Error reading RSS feed: {str(e)}"


def rate_limiter(max_requests: int = 10, window_seconds: int = 60, bucket: str = "default", **kwargs) -> str:
    """Simple in-memory rate limiter. Returns 'allowed' or 'rate_limited'."""
    now = _time.time()
    if bucket not in _rate_limit_buckets:
        _rate_limit_buckets[bucket] = []
    timestamps = _rate_limit_buckets[bucket]
    timestamps = [t for t in timestamps if now - t < window_seconds]
    if len(timestamps) >= max_requests:
        _rate_limit_buckets[bucket] = timestamps
        wait_time = window_seconds - (now - timestamps[0])
        return f"rate_limited: Wait {wait_time:.1f}s. Limit: {max_requests} requests per {window_seconds}s."
    timestamps.append(now)
    _rate_limit_buckets[bucket] = timestamps
    remaining = max_requests - len(timestamps)
    return f"allowed: {remaining} requests remaining in {window_seconds}s window."
