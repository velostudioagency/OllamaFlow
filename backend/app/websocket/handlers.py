import json
import time
import asyncio
from typing import List
from fastapi import WebSocket, WebSocketDisconnect
from app.core.runner import WorkflowRunner

active_connections: List[WebSocket] = []


async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    runner = None
    stop_received = asyncio.Event()
    try:
        data = await websocket.receive_text()
        workflow = json.loads(data)
        if not workflow.get("nodes"):
            await websocket.send_json({"type": "error", "message": "Workflow has no nodes"})
            return

        async def send_log(log_entry):
            try:
                await websocket.send_json({"type": "log", "data": log_entry})
            except Exception:
                pass

        async def send_stream(stream_data):
            try:
                await websocket.send_json({"type": "stream", "data": stream_data})
            except Exception:
                pass

        runner = WorkflowRunner()

        async def listen_for_stop():
            try:
                while not stop_received.is_set():
                    msg = await websocket.receive_text()
                    parsed = json.loads(msg)
                    if parsed.get("type") == "stop":
                        runner.stop()
                        stop_received.set()
                        return
            except (WebSocketDisconnect, Exception):
                stop_received.set()

        listener = asyncio.create_task(listen_for_stop())
        result = await runner.run(workflow, log_callback=send_log, stream_callback=send_stream)
        listener.cancel()
        await websocket.send_json({"type": "complete", "data": result})
    except WebSocketDisconnect:
        if runner:
            runner.stop()
    except Exception as e:
        if runner:
            runner.stop()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


async def websocket_chat_run(websocket: WebSocket):
    await websocket.accept()
    runner = None
    stop_received = asyncio.Event()
    try:
        data = await websocket.receive_text()
        payload = json.loads(data)
        workflow = payload.get("workflow", {})
        text = payload.get("text", "")
        file_path = payload.get("file_path")

        if not workflow.get("nodes"):
            await websocket.send_json({"type": "error", "message": "No workflow loaded. Build a workflow on the canvas first."})
            return

        input_text = text
        if file_path:
            try:
                from app.tools.file_ops import read_file
                content = await asyncio.to_thread(read_file, file_path)
                input_text = f"File content:\n\n{content}\n\nUser request: {text}"
            except Exception:
                input_text = f"File: {file_path}\nUser request: {text}"

        if input_text:
            input_nodes = [n for n in workflow["nodes"] if n.get("type") == "input"]
            for node in input_nodes:
                node.setdefault("config", {})
                node["config"]["prompt"] = input_text

        start_time = time.time()
        runner = WorkflowRunner()

        async def send_log(log_entry):
            try:
                await websocket.send_json({"type": "log", "data": log_entry})
            except Exception:
                pass

        async def send_stream(stream_data):
            try:
                await websocket.send_json({"type": "stream", "data": stream_data})
            except Exception:
                pass

        async def listen_for_stop():
            try:
                while not stop_received.is_set():
                    msg = await websocket.receive_text()
                    parsed = json.loads(msg)
                    if parsed.get("type") == "stop":
                        runner.stop()
                        stop_received.set()
                        return
            except (WebSocketDisconnect, Exception):
                stop_received.set()

        listener = asyncio.create_task(listen_for_stop())
        result = await runner.run(workflow, log_callback=send_log, stream_callback=send_stream)
        listener.cancel()
        elapsed = round(time.time() - start_time, 1)
        result["duration"] = elapsed
        await websocket.send_json({"type": "complete", "data": result})
    except WebSocketDisconnect:
        if runner:
            runner.stop()
    except Exception as e:
        if runner:
            runner.stop()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
