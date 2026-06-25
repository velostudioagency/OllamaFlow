import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable
from node_registry import NODE_HANDLERS, NODE_TYPES, NodeResult


class WorkflowRunner:
    def __init__(self):
        self.context: Dict[str, Any] = {}
        self.logs: List[Dict] = []
        self.is_running = False
        self.should_stop = False
        self.log_callback: Optional[Callable] = None

    def reset(self):
        self.context = {}
        self.logs = []
        self.is_running = False
        self.should_stop = False

    async def log(self, message: str, node_id: str = "", node_type: str = "", status: str = "info"):
        timestamp = time.strftime("%H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "message": message,
            "node_id": node_id,
            "node_type": node_type,
            "status": status
        }
        self.logs.append(log_entry)
        if self.log_callback:
            await self.log_callback(log_entry)

    def stop(self):
        self.should_stop = True

    def _build_graph(self, workflow: Dict) -> Dict:
        nodes = {n["id"]: n for n in workflow.get("nodes", [])}
        edges = workflow.get("edges", [])
        adjacency = {nid: [] for nid in nodes}
        in_degree = {nid: 0 for nid in nodes}
        for edge in edges:
            src = edge["source"]
            tgt = edge["target"]
            if src in nodes and tgt in nodes:
                adjacency[src].append(tgt)
                in_degree[tgt] = in_degree.get(tgt, 0) + 1
        start_nodes = [nid for nid, deg in in_degree.items() if deg == 0]
        if not start_nodes and nodes:
            start_nodes = list(nodes.keys())[:1]
        return {
            "nodes": nodes,
            "adjacency": adjacency,
            "in_degree": in_degree,
            "start_nodes": start_nodes,
            "edges": edges
        }

    def _get_next_nodes(self, current_id: str, graph: Dict, branch: Optional[str] = None) -> List[str]:
        next_ids = []
        for edge in graph["edges"]:
            if edge["source"] == current_id:
                src_node = graph["nodes"].get(current_id, {})
                if src_node.get("type") == "condition" and branch:
                    handle_id = edge.get("sourceHandle", "")
                    if branch == "true" and ("true" in handle_id.lower() or handle_id == "handle-true"):
                        next_ids.append(edge["target"])
                    elif branch == "false" and ("false" in handle_id.lower() or handle_id == "handle-false"):
                        next_ids.append(edge["target"])
                else:
                    next_ids.append(edge["target"])
        return next_ids

    async def run(self, workflow: Dict, log_callback: Optional[Callable] = None) -> Dict:
        self.reset()
        self.log_callback = log_callback
        self.is_running = True
        graph = self._build_graph(workflow)
        if not graph["start_nodes"]:
            await self.log("Error: No starting node found. Add an Input node.", status="error")
            return {"status": "error", "output": "No starting node found", "logs": self.logs}
        await self.log(f"Starting workflow '{workflow.get('name', 'Untitled')}'...", status="info")
        visited_loops = {}
        async def execute_node(node_id: str, depth: int = 0):
            if self.should_stop:
                await self.log("Workflow stopped by user.", status="warning")
                return
            if depth > 50:
                await self.log("Max recursion depth reached.", status="error")
                return
            node = graph["nodes"].get(node_id)
            if not node:
                await self.log(f"Node {node_id} not found.", status="error")
                return
            node_type = node.get("type", "unknown")
            node_config = node.get("config", {})
            handler = NODE_HANDLERS.get(node_type)
            if not handler:
                await self.log(f"Unknown node type: {node_type}", node_id=node_id, status="error")
                return
            type_info = NODE_TYPES.get(node_type, {})
            icon = type_info.get("icon", "⚪")
            label = node_config.get("label", type_info.get("label", node_type))
            await self.log(
                f"{icon} {label}: Processing...",
                node_id=node_id,
                node_type=node_type,
                status="running"
            )
            try:
                result: NodeResult = await handler(node, self.context)
                if result.status == "success":
                    await self.log(
                        f"{icon} {label}: Done — {result.output[:200]}{'...' if len(result.output) > 200 else ''}",
                        node_id=node_id,
                        node_type=node_type,
                        status="success"
                    )
                else:
                    await self.log(
                        f"{icon} {label}: Error — {result.error}",
                        node_id=node_id,
                        node_type=node_type,
                        status="error"
                    )
                branch = None
                if node_type == "condition":
                    branch = self.context.get("branch", "false")
                    await self.log(
                        f"  → Branching to: {'True' if branch == 'true' else 'False'} path",
                        node_id=node_id,
                        node_type=node_type,
                        status="info"
                    )
                next_nodes = self._get_next_nodes(node_id, graph, branch)
                if node_type == "loop":
                    max_iter = node_config.get("max_iterations", 5)
                    loop_key = f"loop_{node_id}"
                    if loop_key not in visited_loops:
                        visited_loops[loop_key] = 0
                    visited_loops[loop_key] += 1
                    if visited_loops[loop_key] <= max_iter and next_nodes:
                        for next_id in next_nodes:
                            await execute_node(next_id, depth + 1)
                        return
                    elif visited_loops[loop_key] > max_iter:
                        await self.log(
                            f"  → Loop max iterations ({max_iter}) reached",
                            node_id=node_id,
                            status="info"
                        )
                for next_id in next_nodes:
                    await execute_node(next_id, depth + 1)
            except Exception as e:
                await self.log(
                    f"{icon} {label}: Exception — {str(e)}",
                    node_id=node_id,
                    node_type=node_type,
                    status="error"
                )
        for start_id in graph["start_nodes"]:
            await execute_node(start_id)
        self.is_running = False
        final_output = self.context.get("final_output", self.context.get("current_input", ""))
        errors = [l for l in self.logs if l["status"] == "error"]
        await self.log("Workflow execution complete.", status="info")
        return {
            "status": "completed" if not errors else "completed_with_errors",
            "output": final_output,
            "logs": self.logs,
            "errors": [e["message"] for e in errors]
        }


workflow_runner = WorkflowRunner()
