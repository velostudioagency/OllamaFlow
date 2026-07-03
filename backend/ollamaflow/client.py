"""
OllamaFlow Python SDK client.
"""

import asyncio
import json
import os
import websockets
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional, Any


@dataclass
class RunEvent:
    """A single event from workflow execution."""
    type: str  # "log", "stream", "complete", "error", "token_usage"
    data: str = ""
    node_id: str = ""
    node_type: str = ""
    token_usage: Optional[Dict] = None


@dataclass
class WorkflowResult:
    """Result of a completed workflow run."""
    output: str = ""
    status: str = "success"
    logs: List[RunEvent] = field(default_factory=list)
    token_usage: Optional[Dict] = None
    duration_ms: float = 0


class OllamaFlow:
    """Client for interacting with an OllamaFlow server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_token: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token or os.environ.get("OLLAMAFLOW_API_TOKEN", "")
        self.ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    async def list_workflows(self) -> List[str]:
        """List saved workflow names."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/workflows",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("workflows", []) if isinstance(data, dict) else data
            return [
                item["name"] if isinstance(item, dict) else str(item)
                for item in items
            ]

    async def load_workflow(self, name: str) -> Dict:
        """Load a workflow definition by name."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/load/{name}",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("workflow", data) if isinstance(data, dict) else data

    async def save_workflow(self, name: str, workflow: Dict) -> Dict:
        """Save a workflow definition."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/save",
                headers=self._headers(),
                json={"name": name, "workflow": workflow},
            )
            resp.raise_for_status()
            return resp.json()

    async def run(
        self,
        workflow: Any,
        input_text: str = "",
        timeout: float = 300,
    ) -> WorkflowResult:
        """
        Run a workflow synchronously (waits for completion).

        Args:
            workflow: Workflow dict, JSON string, or saved workflow name.
            input_text: Input text for the workflow's input node.
            timeout: Max seconds to wait.

        Returns:
            WorkflowResult with output, logs, and token usage.
        """
        import httpx
        import time

        wf = await self._resolve_workflow(workflow)

        if input_text:
            for node in wf.get("nodes", []):
                if node.get("type") == "input":
                    node.setdefault("config", {})
                    node["config"]["prompt"] = input_text

        start = time.monotonic()

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/run",
                headers=self._headers(),
                json={"workflow": wf},
            )
            resp.raise_for_status()
            data = resp.json()

        elapsed = (time.monotonic() - start) * 1000
        token_usage = data.get("token_usage")
        return WorkflowResult(
            output=data.get("output", ""),
            status=data.get("status", "success"),
            token_usage=token_usage,
            duration_ms=data.get("duration", elapsed),
            logs=[
                RunEvent(type="complete", data=data.get("output", ""))
            ],
        )

    async def run_stream(
        self,
        workflow: Any,
        input_text: str = "",
        timeout: float = 300,
    ) -> AsyncIterator[RunEvent]:
        """
        Run a workflow with streaming events via WebSocket.

        Args:
            workflow: Workflow dict, JSON string, or saved workflow name.
            input_text: Input text for the workflow's input node.
            timeout: Max seconds to wait.

        Yields:
            RunEvent objects as the workflow executes.
        """
        wf = await self._resolve_workflow(workflow)

        if input_text:
            for node in wf.get("nodes", []):
                if node.get("type") == "input":
                    node.setdefault("config", {})
                    node["config"]["prompt"] = input_text

        ws_endpoint = f"{self.ws_url}/ws/run"

        try:
            async with websockets.connect(
                ws_endpoint,
                extra_headers=self._headers(),
                open_timeout=10,
            ) as ws:
                await ws.send(json.dumps(wf))

                while True:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    except asyncio.TimeoutError:
                        yield RunEvent(type="error", data="Timed out waiting for response")
                        break

                    msg = json.loads(raw)
                    msg_type = msg.get("type", "")

                    if msg_type == "log":
                        log_data = msg.get("data", {})
                        event = RunEvent(
                            type="log",
                            data=log_data.get("message", "") if isinstance(log_data, dict) else str(log_data),
                            node_id=log_data.get("node_id", "") if isinstance(log_data, dict) else "",
                            node_type=log_data.get("node_type", "") if isinstance(log_data, dict) else "",
                        )
                    elif msg_type == "stream":
                        event = RunEvent(type="stream", data=str(msg.get("data", "")))
                    elif msg_type == "complete":
                        result_data = msg.get("data", {})
                        event = RunEvent(
                            type="complete",
                            data=result_data.get("output", "") if isinstance(result_data, dict) else str(result_data),
                            token_usage=result_data.get("token_usage") if isinstance(result_data, dict) else None,
                        )
                    elif msg_type == "error":
                        event = RunEvent(type="error", data=str(msg.get("message", msg.get("data", ""))))
                    else:
                        event = RunEvent(type=msg_type, data=str(msg.get("data", "")))

                    yield event

                    if event.type in ("complete", "error"):
                        break
        except (websockets.exceptions.ConnectionClosed, OSError) as e:
            yield RunEvent(type="error", data=f"Connection error: {e}")

    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/models",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("models", []) if isinstance(data, dict) else data

    async def list_tools(self) -> List[Dict]:
        """List available tool definitions."""
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/tools",
                headers=self._headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            tools = data.get("tools", []) if isinstance(data, dict) else data
            details = data.get("details", {}) if isinstance(data, dict) else {}
            result = []
            for name in tools:
                info = details.get(name, {})
                result.append({
                    "name": name,
                    "description": info.get("description", ""),
                    "params": info.get("params", []),
                })
            return result

    async def _resolve_workflow(self, workflow: Any) -> Dict:
        """Resolve workflow from name, JSON string, or dict."""
        if isinstance(workflow, dict):
            return workflow
        if isinstance(workflow, str):
            # Try as JSON first
            try:
                return json.loads(workflow)
            except json.JSONDecodeError:
                pass
            # Treat as workflow name
            return await self.load_workflow(workflow)
        raise ValueError(f"Invalid workflow type: {type(workflow)}")
