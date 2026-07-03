import json
import re
import time
import asyncio
import requests
from typing import Any, Dict, List, Optional, Callable, Awaitable
from app.tools.definitions import execute_tool, TOOL_DEFINITIONS
from app.tools.utils import safe_eval
from app.services.memory import memory_manager


class NodeResult:
    def __init__(self, output: str, status: str = "success", error: str = ""):
        self.output = output
        self.status = status
        self.error = error


async def handle_input(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    prompt = config.get("prompt", "")
    input_type = config.get("input_type", "text")
    if input_type == "file_upload" and config.get("file_path"):
        from app.tools.definitions import read_file
        file_path = config["file_path"]
        context["uploaded_file_path"] = file_path
        content = read_file(file_path)
        prompt = f"File content:\n\n{content}\n\nUser goal: {prompt}"
    context["current_input"] = prompt
    context["original_input"] = prompt
    return NodeResult(output=prompt)


async def handle_llm(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    model = config.get("model", "llama3.1:8b")
    system_prompt = config.get("system_prompt", "You are a helpful research assistant. Your job is to help users find information. If the user asks a factual question, provide what you know. If you're unsure, output a clear search query (just the keywords, no extra text) for the next tool to search the web. Never refuse requests - always be helpful and constructive.")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2000)
    user_input = context.get("current_input", "")
    original_input = context.get("original_input", user_input)
    stream_callback = context.get("stream_callback")
    node_id = context.get("stream_node_id", "")
    node_type = context.get("stream_node_type", "")
    provider = config.get("provider", "ollama")

    # Model aliasing: resolve friendly names to actual model IDs
    MODEL_ALIASES = {
        "fast": {"ollama": "llama3.1:8b", "groq": "llama-3.1-8b-instant"},
        "balanced": {"ollama": "llama3.1:8b", "groq": "llama-3.3-70b-versatile"},
        "quality": {"ollama": "llama3.1:70b", "groq": "llama-3.3-70b-versatile"},
        "code": {"ollama": "codellama:13b", "groq": "llama-3.3-70b-versatile"},
        "creative": {"ollama": "llama3.1:8b", "groq": "mixtral-8x7b-32768"},
    }
    if model in MODEL_ALIASES:
        alias = MODEL_ALIASES[model]
        model = alias.get(provider, alias.get("ollama", model))

    graph = context.get("graph")
    upstream_type = ""
    if graph and node_id:
        for edge in graph.get("edges", []):
            if edge.get("target") == node_id:
                src_node = graph.get("nodes", {}).get(edge.get("source"), {})
                upstream_type = src_node.get("type", "")
                break

    if upstream_type == "tool" and original_input and original_input != user_input:
        user_input = f"Original task: {original_input}\n\nSearch results:\n{user_input}"

    connected_tools = []
    if graph:
        for edge in graph.get("edges", []):
            if edge.get("source") == node_id:
                target_node = graph.get("nodes", {}).get(edge.get("target"), {})
                if target_node.get("type") == "tool":
                    tool_name = target_node.get("config", {}).get("tool_name", "")
                    if tool_name and tool_name in TOOL_DEFINITIONS:
                        connected_tools.append(tool_name)

    tool_context = ""
    if connected_tools:
        tool_context = "\n\nYou have access to the following tools downstream. Output an ACTION line to use a tool:\n"
        for tool_name in connected_tools:
            tool_def = TOOL_DEFINITIONS[tool_name]
            param_parts = []
            for p in tool_def["params"]:
                req = "required" if p["required"] else "optional"
                param_parts.append(f"{p['name']} ({req})")
            tool_context += f"- {tool_name}: {tool_def['description']}\n"
            tool_context += f"  Parameters: {', '.join(param_parts)}\n"
        tool_context += "\nFormat: ACTION: tool_name(param1='value1', param2='value2')"
        tool_context += "\nWhen you have enough information to answer, just respond normally (without ACTION:)."
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content=system_prompt + tool_context),
            HumanMessage(content=user_input)
        ]

        token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        if provider == "groq":
            from app.services.settings import settings_manager
            groq_key = settings_manager.get("groq_api_key", "")
            groq_model = config.get("groq_model", settings_manager.get("groq_model", "llama-3.3-70b-versatile"))
            if not groq_key:
                return NodeResult(output="", status="error", error="Groq API key not set. Go to Settings to configure.")
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                groq_api_key=groq_key,
                model_name=groq_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif provider == "openai":
            from app.services.settings import settings_manager
            openai_key = settings_manager.get("openai_api_key", "")
            openai_base = settings_manager.get("openai_base_url", "https://api.openai.com/v1")
            openai_model = config.get("openai_model", settings_manager.get("openai_model", "gpt-4o"))
            if not openai_key:
                return NodeResult(output="", status="error", error="OpenAI API key not set. Go to Settings to configure.")
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                api_key=openai_key,
                base_url=openai_base,
                model=openai_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif provider == "anthropic":
            from app.services.settings import settings_manager
            anthropic_key = settings_manager.get("anthropic_api_key", "")
            anthropic_model = config.get("anthropic_model", settings_manager.get("anthropic_model", "claude-sonnet-4-20250514"))
            if not anthropic_key:
                return NodeResult(output="", status="error", error="Anthropic API key not set. Go to Settings to configure.")
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                api_key=anthropic_key,
                model=anthropic_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            from langchain_ollama import ChatOllama
            llm = ChatOllama(
                model=model,
                temperature=temperature,
                num_predict=max_tokens
            )

        should_stop = context.get("should_stop", lambda: False)

        if stream_callback:
            collected = []
            for chunk in llm.stream(messages):
                if should_stop():
                    break
                if chunk.content:
                    collected.append(chunk.content)
                    await stream_callback(node_id, node_type, chunk.content)
            output = "".join(collected)
        else:
            response = await asyncio.to_thread(llm.invoke, messages)
            output = response.content
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = response.usage_metadata
                token_usage = {
                    "prompt_tokens": getattr(usage, "input_tokens", 0) or 0,
                    "completion_tokens": getattr(usage, "output_tokens", 0) or 0,
                    "total_tokens": getattr(usage, "total_tokens", 0) or 0,
                }
            elif hasattr(response, "response_metadata") and response["response_metadata"].get("token_usage"):
                tu = response["response_metadata"]["token_usage"]
                token_usage = {
                    "prompt_tokens": tu.get("prompt_tokens", 0),
                    "completion_tokens": tu.get("completion_tokens", 0),
                    "total_tokens": tu.get("total_tokens", 0),
                }

        if connected_tools and "ACTION:" in output:
            action_line = output.split("ACTION:")[-1].split("\n")[0].strip()
            tool_name = action_line.split("(")[0].strip()
            if tool_name in connected_tools:
                params = _parse_action_params(action_line)
                params = _fix_param_names(tool_name, params)
                tool_result = await asyncio.to_thread(execute_tool, tool_name, params)
                messages.append(HumanMessage(content=output))
                messages.append(HumanMessage(content=f"Tool result: {tool_result[:2000]}"))
                if stream_callback:
                    collected = []
                    for chunk in llm.stream(messages):
                        if should_stop():
                            break
                        if chunk.content:
                            collected.append(chunk.content)
                            await stream_callback(node_id, node_type, chunk.content)
                    output = "".join(collected)
                else:
                    response = await asyncio.to_thread(llm.invoke, messages)
                    output = response.content

        search_results = context.get("last_search_results", "")
        search_query = context.get("last_search_query", "")
        if search_results and upstream_type == "tool":
            output += f"\n\n---\n**Research results for:** {search_query}\n\n{search_results}"

        context["current_input"] = output
        context.setdefault("token_usage_by_node", {})
        context["token_usage_by_node"][node_id] = {
            "provider": provider,
            "model": model,
            "usage": token_usage,
        }
        return NodeResult(output=output)
    except Exception as e:
        return NodeResult(output="", status="error", error=f"LLM error: {str(e)}")


async def handle_tool(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    tool_name = config.get("tool_name", "web_search")
    tool_params = config.get("params", {})
    if isinstance(tool_params, str):
        try:
            tool_params = json.loads(tool_params)
        except Exception:
            tool_params = {}
    if not tool_params:
        tool_params = {}
    current_input = context.get("current_input", "")
    original_input = context.get("original_input", current_input)

    graph = context.get("graph")
    node_id = context.get("stream_node_id", "")
    upstream_type = ""
    if graph and node_id:
        for edge in graph.get("edges", []):
            if edge.get("target") == node_id:
                src_node = graph.get("nodes", {}).get(edge.get("source"), {})
                upstream_type = src_node.get("type", "")
                break

    needs_query = "query" not in tool_params or not str(tool_params.get("query", "")).strip()
    if tool_name in ["web_search"] and needs_query:
        if upstream_type == "input":
            tool_params["query"] = original_input if original_input else current_input
        else:
            refusal_patterns = ["i'm sorry", "i am sorry", "i can't assist", "i cannot assist",
                               "i'm unable", "i am unable", "i can't help", "i cannot help"]
            is_refusal = any(p in current_input.lower() for p in refusal_patterns)
            if is_refusal and original_input:
                tool_params["query"] = original_input
            else:
                tool_params["query"] = current_input
    elif tool_name in ["read_file"] and "file_path" not in tool_params:
        uploaded_path = context.get("uploaded_file_path", "")
        if uploaded_path:
            tool_params["file_path"] = uploaded_path
        else:
            tool_params["file_path"] = current_input
    elif tool_name in ["write_file"]:
        if "content" not in tool_params:
            tool_params["content"] = current_input
        if "file_path" not in tool_params:
            file_match = re.search(r"(?:File Name|file_name|filename|filepath|file_path)\s*[:=]\s*[`\"'*]*(.+?)[`\"'*]*\s*(?:---|\n|$)", current_input, re.IGNORECASE)
            if file_match:
                tool_params["file_path"] = file_match.group(1).strip().strip("*")
            else:
                tool_params["file_path"] = "output.txt"
    elif tool_name in ["calculate"] and "expression" not in tool_params:
        tool_params["expression"] = current_input
    elif tool_name in ["run_code"] and "code" not in tool_params:
        tool_params["code"] = current_input
    elif tool_name in ["run_command"] and "command" not in tool_params:
        tool_params["command"] = current_input
    if tool_name in ["http_request", "web_scraper"]:
        if "url" not in tool_params and current_input:
            url_match = re.search(r'https?://[^\s\'"<>\)]+', current_input)
            if url_match:
                tool_params["url"] = url_match.group(0)
            else:
                tool_params["url"] = current_input.strip()
    if tool_name == "send_email":
        for key in ["to", "subject", "body"]:
            if key not in tool_params or not tool_params[key]:
                tool_params[key] = current_input if key == "body" else ""
    result = await asyncio.to_thread(execute_tool, tool_name, tool_params)
    if tool_name == "web_search":
        context["last_search_query"] = tool_params.get("query", "")
        context["last_search_results"] = result
    context["current_input"] = result
    return NodeResult(output=result)


async def handle_memory(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    namespace = config.get("namespace", "default")
    action = config.get("action", "remember")
    memory_type = config.get("memory_type", "long_term")
    current_input = context.get("current_input", "")
    try:
        if action == "remember":
            result = await asyncio.to_thread(memory_manager.save, namespace, current_input, memory_type)
        elif action == "recall":
            result = await asyncio.to_thread(memory_manager.recall, namespace, memory_type)
        elif action == "search":
            query = config.get("search_query", current_input)
            if memory_type == "long_term":
                result = await asyncio.to_thread(memory_manager.search_long_term, namespace, query)
            else:
                result = await asyncio.to_thread(memory_manager.recall_short_term, namespace)
        elif action == "clear":
            result = await asyncio.to_thread(memory_manager.clear, namespace)
        else:
            result = f"Unknown memory action: {action}"
        context["current_input"] = result
        return NodeResult(output=result)
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Memory error: {str(e)}")


async def handle_condition(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    condition = config.get("condition", "")
    current_input = context.get("current_input", "")
    try:
        condition_lower = condition.lower()
        input_lower = current_input.lower()
        if "contains" in condition_lower:
            parts = condition_lower.split("contains")
            if len(parts) == 2:
                check_text = parts[1].strip().strip('"').strip("'")
                result = check_text in input_lower
            else:
                result = bool(current_input.strip())
        elif "equals" in condition_lower:
            parts = condition_lower.split("equals")
            if len(parts) == 2:
                check_text = parts[1].strip().strip('"').strip("'")
                result = check_text in input_lower
            else:
                result = bool(current_input.strip())
        elif "not empty" in condition_lower or "has content" in condition_lower:
            result = bool(current_input.strip())
        elif "empty" in condition_lower:
            result = not bool(current_input.strip())
        elif "error" in condition_lower:
            result = "error" in input_lower or "Error" in current_input
        elif "number" in condition_lower:
            import re
            result = bool(re.search(r'\d', current_input))
        else:
            try:
                result = bool(safe_eval(condition, {"input": current_input}))
            except Exception:
                result = bool(current_input.strip())
        context["condition_result"] = result
        branch = "true" if result else "false"
        output = f"Condition '{condition}' evaluated to {result} (branch: {branch})"
        context["branch"] = branch
        return NodeResult(output=output)
    except Exception as e:
        context["branch"] = "false"
        return NodeResult(output="", status="error", error=f"Condition error: {str(e)}")


async def handle_loop(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    max_iterations = config.get("max_iterations", 5)
    stop_condition = config.get("stop_condition", "")
    current_input = context.get("current_input", "")

    iteration = context.get("loop_iteration", 0)

    if stop_condition and iteration > 0:
        try:
            should_stop = bool(safe_eval(stop_condition, {"input": current_input, "iteration": iteration}))
            if should_stop:
                context["loop_done"] = True
                result = f"Loop stopped at iteration {iteration} by condition. Output: {current_input[:500]}"
                return NodeResult(output=result)
        except Exception:
            pass

    if iteration >= max_iterations:
        context["loop_done"] = True
        result = f"Loop completed: {max_iterations} iterations. Last output: {current_input[:500]}"
        context["current_input"] = current_input
        return NodeResult(output=result)

    context["loop_iteration"] = iteration + 1
    context["loop_done"] = False
    output = f"Loop iteration {iteration + 1}/{max_iterations}"
    return NodeResult(output=output)


def _parse_action_params(action_line: str) -> Dict:
    """Parse parameters from action lines like tool_name(key1='val1', key2='val2')"""
    params = {}
    try:
        paren_start = action_line.index("(")
        paren_end = action_line.rindex(")")
        args_str = action_line[paren_start + 1:paren_end].strip()
        if not args_str:
            return params
        import re
        pattern = r"(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\S+))"
        matches = re.findall(pattern, args_str)
        for key, single_q, double_q, unquoted in matches:
            value = single_q or double_q or unquoted
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            params[key] = value
    except (ValueError, AttributeError):
        pass
    return params


def _fix_param_names(tool_name: str, params: Dict) -> Dict:
    """Map generic/wrong param names to correct ones based on tool definition."""
    if tool_name not in TOOL_DEFINITIONS:
        return params
    tool_params = TOOL_DEFINITIONS[tool_name]["params"]
    if not tool_params:
        return params
    generic_names = ["param1", "param2", "param3", "arg1", "arg2", "arg3",
                     "argument1", "argument2", "input", "value", "data"]
    fixed = {}
    param_index = 0
    for key, value in params.items():
        if key in [p["name"] for p in tool_params]:
            fixed[key] = value
        elif key in generic_names and param_index < len(tool_params):
            correct_name = tool_params[param_index]["name"]
            fixed[correct_name] = value
            param_index += 1
        else:
            fixed[key] = value
            param_index += 1
    return fixed


async def handle_output(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    current_input = context.get("current_input", "")
    search_results = context.get("last_search_results", "")
    search_query = context.get("last_search_query", "")
    final = current_input
    if search_results:
        final += f"\n\n{'='*60}\nFULL SEARCH RESULTS\nQuery: {search_query}\n{'='*60}\n\n{search_results}"
    context["final_output"] = final
    return NodeResult(output=final)


async def handle_transform(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    transform_type = config.get("transform_type", "trim")
    pattern = config.get("pattern", "")
    replacement = config.get("replacement", "")
    template = config.get("template", "")
    current_input = context.get("current_input", "")
    try:
        if transform_type == "regex_extract":
            matches = re.findall(pattern, current_input)
            output = "\n".join(matches) if matches else "No matches found."
        elif transform_type == "regex_replace":
            output = re.sub(pattern, replacement, current_input)
        elif transform_type == "substring":
            parts = pattern.split(":")
            if len(parts) == 2:
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if parts[1] else len(current_input)
                output = current_input[start:end]
            else:
                output = current_input[:int(pattern) if pattern.isdigit() else len(current_input)]
        elif transform_type == "uppercase":
            output = current_input.upper()
        elif transform_type == "lowercase":
            output = current_input.lower()
        elif transform_type == "trim":
            output = current_input.strip()
        elif transform_type == "replace":
            output = current_input.replace(pattern, replacement)
        elif transform_type == "json_path":
            from app.tools.definitions import json_query
            output = json_query(current_input, pattern)
        elif transform_type == "template":
            output = template.replace("{{input}}", current_input)
            for i, match in enumerate(re.findall(r'\{\{(\d+)\}\}', template)):
                idx = int(match)
                parts = current_input.split("\n")
                if idx < len(parts):
                    output = output.replace("{{" + str(idx) + "}}", parts[idx])
        else:
            output = current_input
        context["current_input"] = output
        return NodeResult(output=output)
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Transform error: {str(e)}")


async def handle_merge(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    merge_mode = config.get("merge_mode", "concat")
    separator = config.get("separator", "\n\n")
    inputs = context.get("merge_inputs", [])
    current_input = context.get("current_input", "")
    if not inputs:
        inputs = [current_input]
    try:
        if merge_mode == "concat":
            output = separator.join(str(i) for i in inputs)
        elif merge_mode == "newline":
            output = "\n".join(str(i) for i in inputs)
        elif merge_mode == "json_merge":
            merged = {}
            for inp in inputs:
                try:
                    data = json.loads(inp) if isinstance(inp, str) else inp
                    if isinstance(data, dict):
                        merged.update(data)
                except Exception:
                    pass
            output = json.dumps(merged, indent=2)
        elif merge_mode == "first":
            output = str(inputs[0]) if inputs else ""
        elif merge_mode == "non_empty":
            non_empty = [str(i) for i in inputs if i and str(i).strip()]
            output = separator.join(non_empty) if non_empty else "All inputs were empty."
        else:
            output = separator.join(str(i) for i in inputs)
        context["current_input"] = output
        return NodeResult(output=output)
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Merge error: {str(e)}")


async def handle_delay(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    delay_seconds = min(config.get("delay_seconds", 5), 300)
    current_input = context.get("current_input", "")
    try:
        await asyncio.sleep(delay_seconds)
        context["current_input"] = current_input
        return NodeResult(output=f"Waited {delay_seconds}s. Input passed through.")
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Delay error: {str(e)}")


async def handle_switch(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    switch_field = config.get("switch_field", "")
    cases_str = config.get("cases", "")
    default_case = config.get("default_case", "default")
    current_input = context.get("current_input", "")
    try:
        match_value = ""
        if switch_field and switch_field in context:
            match_value = str(context[switch_field]).lower().strip()
        else:
            match_value = current_input.lower().strip()
        cases = {}
        for line in cases_str.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                key, label = line.split(":", 1)
                cases[key.strip().lower()] = label.strip()
        matched_label = default_case
        for key, label in cases.items():
            if key in match_value or match_value in key:
                matched_label = label
                break
        context["branch"] = matched_label
        output = f"Switch matched: '{matched_label}' (input was: '{match_value[:100]}')"
        return NodeResult(output=output)
    except Exception as e:
        context["branch"] = default_case
        return NodeResult(output="", status="error", error=f"Switch error: {str(e)}")


async def handle_webhook(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    webhook_url = config.get("webhook_url", "")
    method = config.get("method", "POST")
    auth_token = config.get("auth_token", "")
    current_input = context.get("current_input", "")
    if not webhook_url:
        return NodeResult(output="", status="error", error="No webhook URL configured.")
    try:
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        payload = {"input": current_input, "context": {k: str(v)[:500] for k, v in context.items() if k != "stream_callback"}}
        resp = requests.request(
            method.upper(),
            webhook_url,
            json=payload if method.upper() in ("POST", "PUT", "PATCH") else None,
            headers=headers,
            timeout=30
        )
        output = f"Status: {resp.status_code}\n\n{resp.text[:5000]}"
        context["current_input"] = output
        return NodeResult(output=output)
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Webhook error: {str(e)}")


async def handle_webhook_output(node: Dict, context: Dict) -> NodeResult:
    """Send workflow output to an external API via webhook on completion."""
    config = node.get("config", {})
    webhook_url = config.get("webhook_url", "")
    method = config.get("method", "POST")
    auth_token = config.get("auth_token", "")
    auth_header = config.get("auth_header", "Authorization")
    content_type = config.get("content_type", "application/json")
    custom_headers = config.get("custom_headers", "")
    include_context = config.get("include_context", False)
    retry_count = config.get("retry_count", 3)
    retry_delay = config.get("retry_delay", 1)

    if not webhook_url:
        return NodeResult(output="", status="error", error="No webhook URL configured.")

    current_input = context.get("current_input", "")
    final_output = context.get("final_output", current_input)

    headers = {"Content-Type": content_type}
    if auth_token:
        headers[auth_header] = f"Bearer {auth_token}" if not auth_token.startswith("Bearer ") else auth_token
    if custom_headers:
        try:
            for line in custom_headers.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    headers[key.strip()] = val.strip()
        except Exception:
            pass

    if content_type == "application/json":
        payload = {"output": final_output, "input": context.get("original_input", "")}
        if include_context:
            safe_context = {}
            for k, v in context.items():
                if k not in ("stream_callback", "should_stop", "graph"):
                    safe_context[k] = str(v)[:2000]
            payload["context"] = safe_context
    else:
        payload = final_output

    last_error = None
    for attempt in range(retry_count):
        try:
            resp = requests.request(
                method.upper(),
                webhook_url,
                json=payload if method.upper() in ("POST", "PUT", "PATCH") and content_type == "application/json" else (payload if method.upper() in ("POST", "PUT", "PATCH") else None),
                data=payload if content_type != "application/json" and method.upper() in ("POST", "PUT", "PATCH") else None,
                headers=headers,
                timeout=30
            )
            output = f"Webhook sent to {webhook_url}\nStatus: {resp.status_code}\nResponse: {resp.text[:2000]}"
            context["current_input"] = output
            return NodeResult(output=output)
        except Exception as e:
            last_error = str(e)
            if attempt < retry_count - 1:
                await asyncio.sleep(retry_delay)

    return NodeResult(output="", status="error", error=f"Webhook failed after {retry_count} attempts: {last_error}")


async def handle_guardrails(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    validation_type = config.get("validation_type", "not_empty")
    pattern = config.get("pattern", "")
    max_length = config.get("max_length", 5000)
    retry_on_fail = config.get("retry_on_fail", False)
    max_retries = config.get("max_retries", 3)
    current_input = context.get("current_input", "")
    try:
        is_valid = False
        error_msg = ""
        if validation_type == "not_empty":
            is_valid = bool(current_input.strip())
            error_msg = "Input is empty" if not is_valid else ""
        elif validation_type == "json_valid":
            try:
                json.loads(current_input)
                is_valid = True
            except Exception:
                error_msg = "Input is not valid JSON"
        elif validation_type == "contains":
            is_valid = pattern.lower() in current_input.lower()
            error_msg = f"Input does not contain '{pattern}'" if not is_valid else ""
        elif validation_type == "regex":
            is_valid = bool(re.search(pattern, current_input))
            error_msg = f"Input does not match pattern '{pattern}'" if not is_valid else ""
        elif validation_type == "max_length":
            is_valid = len(current_input) <= max_length
            error_msg = f"Input too long ({len(current_input)} > {max_length})" if not is_valid else ""
        elif validation_type == "min_length":
            is_valid = len(current_input) >= max_length
            error_msg = f"Input too short ({len(current_input)} < {max_length})" if not is_valid else ""
        elif validation_type == "custom":
            try:
                is_valid = bool(safe_eval(pattern, {"input": current_input, "re": re}))
                error_msg = "Custom validation failed" if not is_valid else ""
            except Exception as e:
                error_msg = f"Custom validation error: {str(e)}"
        branch = "valid" if is_valid else "invalid"
        context["branch"] = branch
        output = f"Validation {'passed' if is_valid else 'failed'}: {error_msg or validation_type}"
        return NodeResult(output=output)
    except Exception as e:
        context["branch"] = "invalid"
        return NodeResult(output="", status="error", error=f"Guardrails error: {str(e)}")


async def handle_subworkflow(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    subworkflow_json = config.get("subworkflow_json", "")
    pass_input = config.get("pass_input", True)
    current_input = context.get("current_input", "")
    try:
        if not subworkflow_json:
            return NodeResult(output="", status="error", error="No sub-workflow JSON configured.")
        sub_wf = json.loads(subworkflow_json) if isinstance(subworkflow_json, str) else subworkflow_json
        if not sub_wf.get("nodes"):
            return NodeResult(output="", status="error", error="Sub-workflow has no nodes.")
        if pass_input:
            input_nodes = [n for n in sub_wf["nodes"] if n.get("type") == "input"]
            for n in input_nodes:
                n.setdefault("config", {})
                n["config"]["prompt"] = current_input
        from app.core.runner import WorkflowRunner
        runner = WorkflowRunner()
        result = await runner.run(sub_wf)
        output = result.get("output", "")
        context["current_input"] = output
        return NodeResult(output=output)
    except json.JSONDecodeError as e:
        return NodeResult(output="", status="error", error=f"Invalid sub-workflow JSON: {str(e)}")
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Sub-workflow error: {str(e)}")


async def handle_batch(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    subworkflow_json = config.get("subworkflow_json", "")
    batch_mode = config.get("batch_mode", "split_newline")
    current_input = context.get("current_input", "")
    try:
        if not subworkflow_json:
            return NodeResult(output="", status="error", error="No sub-workflow JSON configured for batch.")
        sub_wf = json.loads(subworkflow_json) if isinstance(subworkflow_json, str) else subworkflow_json
        if not sub_wf.get("nodes"):
            return NodeResult(output="", status="error", error="Sub-workflow has no nodes.")
        if batch_mode == "split_newline":
            items = [line.strip() for line in current_input.split("\n") if line.strip()]
        elif batch_mode == "split_comma":
            items = [item.strip() for item in current_input.split(",") if item.strip()]
        elif batch_mode == "json_array":
            try:
                items = json.loads(current_input)
                if not isinstance(items, list):
                    items = [items]
            except Exception:
                items = [current_input]
        else:
            items = [current_input]
        results = []
        from app.core.runner import WorkflowRunner
        for item in items:
            sub_copy = json.loads(json.dumps(sub_wf))
            input_nodes = [n for n in sub_copy["nodes"] if n.get("type") == "input"]
            for n in input_nodes:
                n.setdefault("config", {})
                n["config"]["prompt"] = str(item)
            runner = WorkflowRunner()
            result = await runner.run(sub_copy)
            output = result.get("output", str(item))
            results.append(output)
        final = "\n\n---\n\n".join(results)
        context["current_input"] = final
        return NodeResult(output=final)
    except json.JSONDecodeError as e:
        return NodeResult(output="", status="error", error=f"Invalid sub-workflow JSON: {str(e)}")
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Batch error: {str(e)}")


async def handle_variable(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    var_name = config.get("variable_name", "my_var")
    var_value = config.get("variable_value", "")
    var_type = config.get("variable_type", "string")
    mode = config.get("mode", "set")

    if mode == "set":
        if var_type == "number":
            try:
                var_value = float(var_value)
            except ValueError:
                pass
        elif var_type == "boolean":
            var_value = var_value.lower() in ("true", "1", "yes")
        elif var_type == "json":
            try:
                var_value = json.loads(var_value)
            except json.JSONDecodeError:
                pass
        context[var_name] = var_value
        output = f"Set variable '{var_name}' = {str(var_value)[:200]}"
    elif mode == "get":
        var_value = context.get(var_name, config.get("default_value", ""))
        context["current_input"] = str(var_value)
        output = f"Got variable '{var_name}' = {str(var_value)[:200]}"
    elif mode == "increment":
        current = context.get(var_name, 0)
        try:
            current = float(current) + float(var_value)
        except (ValueError, TypeError):
            current = 0
        context[var_name] = current
        context["current_input"] = str(current)
        output = f"Incremented '{var_name}' to {current}"
    elif mode == "append":
        existing = context.get(var_name, "")
        context[var_name] = str(existing) + str(var_value)
        output = f"Appended to '{var_name}'"
    else:
        output = f"Unknown mode: {mode}"

    return NodeResult(output=output)


async def handle_custom(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    custom_code = config.get("custom_code", "")
    custom_handler_name = config.get("handler_name", "process")
    current_input = context.get("current_input", "")
    if not custom_code:
        return NodeResult(output="", status="error", error="No custom code defined.")
    try:
        local_vars = {"input": current_input, "context": context, "json": json, "re": re, "asyncio": asyncio}
        exec(compile(custom_code, "<custom_node>", "exec"), {}, local_vars)
        handler_fn = local_vars.get(custom_handler_name)
        if handler_fn:
            import inspect
            if inspect.iscoroutinefunction(handler_fn):
                output = await handler_fn(current_input, context)
            else:
                output = handler_fn(current_input, context)
        else:
            output = local_vars.get("output", current_input)
        context["current_input"] = str(output)
        return NodeResult(output=str(output))
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Custom node error: {str(e)}")


NODE_HANDLERS = {
    "input": handle_input,
    "llm": handle_llm,
    "tool": handle_tool,
    "memory": handle_memory,
    "condition": handle_condition,
    "loop": handle_loop,
    "output": handle_output,
    "transform": handle_transform,
    "merge": handle_merge,
    "delay": handle_delay,
    "switch": handle_switch,
    "webhook": handle_webhook,
    "webhook_output": handle_webhook_output,
    "guardrails": handle_guardrails,
    "variable": handle_variable,
    "subworkflow": handle_subworkflow,
    "batch": handle_batch,
    "custom": handle_custom,
}
