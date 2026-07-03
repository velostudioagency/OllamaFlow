import asyncio
import json
import time
import os
from typing import Any, Dict, List, Optional, Callable
from app.nodes.handlers import NODE_HANDLERS, NodeResult
from app.nodes.types import NODE_TYPES
from app.core.token_tracker import TokenCostTracker
from app.core.config import DATA_DIR


class WorkflowRunner:
    def __init__(self):
        self.context: Dict[str, Any] = {}
        self.logs: List[Dict] = []
        self.is_running = False
        self.should_stop = False
        self.log_callback: Optional[Callable] = None
        self.stream_callback: Optional[Callable] = None
        self.token_tracker = TokenCostTracker()

    def reset(self):
        self.context = {}
        self.logs = []
        self.is_running = False
        self.should_stop = False
        self.token_tracker = TokenCostTracker()

    async def stream(self, node_id: str, node_type: str, token: str):
        if self.stream_callback:
            await self.stream_callback({
                "node_id": node_id,
                "node_type": node_type,
                "token": token
            })

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
                src_type = src_node.get("type", "")
                if src_type == "condition" and branch:
                    handle_id = edge.get("sourceHandle", "")
                    if branch == "true" and ("true" in handle_id.lower() or handle_id == "handle-true"):
                        next_ids.append(edge["target"])
                    elif branch == "false" and ("false" in handle_id.lower() or handle_id == "handle-false"):
                        next_ids.append(edge["target"])
                elif src_type == "switch" and branch:
                    handle_id = edge.get("sourceHandle", "")
                    if branch == "default" and "default" in handle_id.lower():
                        next_ids.append(edge["target"])
                    elif handle_id == f"handle-{branch}":
                        next_ids.append(edge["target"])
                elif src_type == "guardrails" and branch:
                    handle_id = edge.get("sourceHandle", "")
                    if branch == "valid" and "valid" in handle_id.lower():
                        next_ids.append(edge["target"])
                    elif branch == "invalid" and "invalid" in handle_id.lower():
                        next_ids.append(edge["target"])
                else:
                    edge_condition = edge.get("condition", "")
                    if edge_condition:
                        current_value = self.context.get("current_input", "")
                        try:
                            from app.tools.utils import safe_eval
                            cond_result = bool(safe_eval(edge_condition, {
                                "input": current_value,
                                "context": self.context
                            }))
                            if cond_result:
                                next_ids.append(edge["target"])
                        except Exception:
                            next_ids.append(edge["target"])
                    else:
                        next_ids.append(edge["target"])
        return next_ids

    async def _execute_single_node(self, node_id: str, graph: Dict, visited_loops: Dict) -> List[str]:
        """Execute a single node and return the list of next node IDs to process."""
        if self.should_stop:
            return []
        node = graph["nodes"].get(node_id)
        if not node:
            await self.log(f"Node {node_id} not found.", status="error")
            return []
        node_type = node.get("type", "unknown")
        node_config = node.get("config", {})
        handler = NODE_HANDLERS.get(node_type)
        if not handler:
            await self.log(f"Unknown node type: {node_type}", node_id=node_id, status="error")
            return []
        if node_type == "merge":
            merge_inputs = []
            for edge in graph["edges"]:
                if edge["target"] == node_id:
                    src_id = edge["source"]
                    src_output = self.context.get(f"node_output_{src_id}", "")
                    if src_output:
                        merge_inputs.append(src_output)
            if not merge_inputs:
                merge_inputs = [self.context.get("current_input", "")]
            self.context["merge_inputs"] = merge_inputs
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
            self.context["stream_node_id"] = node_id
            self.context["stream_node_type"] = node_type
            result: NodeResult = await handler(node, self.context)
            self.context[f"node_output_{node_id}"] = result.output
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
                if result.error:
                    self.context["current_input"] = f"[ERROR: {result.error}]"
            branch = None
            if node_type == "condition":
                branch = self.context.get("branch", "false")
                await self.log(
                    f"  → Branching to: {'True' if branch == 'true' else 'False'} path",
                    node_id=node_id,
                    node_type=node_type,
                    status="info"
                )
            elif node_type == "switch":
                branch = self.context.get("branch", "default")
                await self.log(
                    f"  → Switch routing to: '{branch}'",
                    node_id=node_id,
                    node_type=node_type,
                    status="info"
                )
            elif node_type == "guardrails":
                branch = self.context.get("branch", "invalid")
                await self.log(
                    f"  → Guardrails: {'Valid' if branch == 'valid' else 'Invalid'} path",
                    node_id=node_id,
                    node_type=node_type,
                    status="info"
                )
            next_nodes = self._get_next_nodes(node_id, graph, branch)
            if node_type == "loop":
                loop_done = self.context.get("loop_done", True)
                if not loop_done and next_nodes:
                    loop_key = f"loop_{node_id}"
                    if loop_key not in visited_loops:
                        visited_loops[loop_key] = 0
                    visited_loops[loop_key] += 1
                    max_iter = node_config.get("max_iterations", 5)
                    if visited_loops[loop_key] < max_iter * len(next_nodes):
                        for next_id in next_nodes:
                            next_nodes_result = await self._execute_single_node(next_id, graph, visited_loops)
                        result_nodes = []
                        for nid in next_nodes_result:
                            if nid not in result_nodes:
                                result_nodes.append(nid)
                        result_nodes.append(node_id)
                        return result_nodes
                    else:
                        await self.log(
                            f"  → Loop finished",
                            node_id=node_id,
                            status="info"
                        )
            return next_nodes
        except Exception as e:
            await self.log(
                f"{icon} {label}: Exception — {str(e)}",
                node_id=node_id,
                node_type=node_type,
                status="error"
            )
            return []

    async def run(self, workflow: Dict, log_callback: Optional[Callable] = None,
                  stream_callback: Optional[Callable] = None) -> Dict:
        self.reset()
        self.log_callback = log_callback
        self.stream_callback = stream_callback
        self.is_running = True
        start_time = time.time()
        self.token_tracker.start()
        self.context["stream_callback"] = self.stream
        self.context["stream_node_id"] = ""
        self.context["stream_node_type"] = ""
        self.context["should_stop"] = lambda: self.should_stop
        graph = self._build_graph(workflow)
        self.context["graph"] = graph
        if not graph["start_nodes"]:
            await self.log("Error: No starting node found. Add an Input node.", status="error")
            return {"status": "error", "output": "No starting node found", "logs": self.logs}
        await self.log(f"Starting workflow '{workflow.get('name', 'Untitled')}'...", status="info")
        visited_loops = {}
        executed = set()
        pending = list(graph["start_nodes"])
        while pending and not self.should_stop:
            ready = [nid for nid in pending if nid not in executed]
            if not ready:
                break
            if len(ready) == 1:
                node_id = ready[0]
                executed.add(node_id)
                next_nodes = await self._execute_single_node(node_id, graph, visited_loops)
                pending = [nid for nid in next_nodes if nid not in executed]
            else:
                tasks = []
                for node_id in ready:
                    executed.add(node_id)
                    tasks.append(self._execute_single_node(node_id, graph, visited_loops))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                next_nodes = []
                for r in results:
                    if isinstance(r, list):
                        next_nodes.extend(r)
                    elif isinstance(r, Exception):
                        await self.log(f"Parallel execution error: {r}", status="error")
                pending = [nid for nid in next_nodes if nid not in executed]
        self.is_running = False
        final_output = self.context.get("final_output", self.context.get("current_input", ""))
        errors = [l for l in self.logs if l["status"] == "error"]
        await self.log("Workflow execution complete.", status="info")
        end_time = time.time()
        duration = round(end_time - start_time, 2)

        # Collect token usage from LLM nodes
        token_usage_by_node = self.context.get("token_usage_by_node", {})
        for nid, usage_data in token_usage_by_node.items():
            node_info = graph["nodes"].get(nid, {})
            self.token_tracker.record_node_usage(
                node_id=nid,
                node_type=node_info.get("type", "llm"),
                provider=usage_data.get("provider", "unknown"),
                model=usage_data.get("model", "unknown"),
                prompt_tokens=usage_data.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=usage_data.get("usage", {}).get("completion_tokens", 0),
            )
        token_summary = self.token_tracker.get_summary()

        run_record = {
            "id": f"run_{int(time.time()*1000)}",
            "workflow_name": workflow.get("name", "Untitled"),
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(start_time)),
            "duration_seconds": duration,
            "status": "completed" if not errors else "completed_with_errors",
            "node_count": len(workflow.get("nodes", [])),
            "output_preview": final_output[:500] if final_output else "",
            "error_count": len(errors),
            "token_usage": token_summary.to_dict(),
            "logs": self.logs
        }
        try:
            history_path = str(DATA_DIR / "execution_history.json")
            os.makedirs(os.path.dirname(history_path), exist_ok=True)
            history = []
            if os.path.exists(history_path):
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            history.insert(0, run_record)
            history = history[:100]
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, default=str)
        except Exception:
            pass
        return {
            "status": "completed" if not errors else "completed_with_errors",
            "output": final_output,
            "logs": self.logs,
            "errors": [e["message"] for e in errors],
            "duration": duration,
            "run_id": run_record["id"],
            "token_usage": token_summary.to_dict(),
        }
