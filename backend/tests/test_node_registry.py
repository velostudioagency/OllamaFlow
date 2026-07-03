import pytest
import asyncio
import json


@pytest.mark.asyncio
async def test_handle_input_basic():
    from node_registry import handle_input
    node = {"id": "n1", "type": "input", "config": {"prompt": "Test prompt"}}
    context = {}
    result = await handle_input(node, context)
    assert result.status == "success"
    assert result.output == "Test prompt"
    assert context["current_input"] == "Test prompt"
    assert context["original_input"] == "Test prompt"


@pytest.mark.asyncio
async def test_handle_input_empty():
    from node_registry import handle_input
    node = {"id": "n1", "type": "input", "config": {"prompt": ""}}
    context = {}
    result = await handle_input(node, context)
    assert result.status == "success"
    assert result.output == ""


@pytest.mark.asyncio
async def test_handle_transform_uppercase():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {"transform_type": "uppercase"}}
    context = {"current_input": "hello world"}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert result.output == "HELLO WORLD"
    assert context["current_input"] == "HELLO WORLD"


@pytest.mark.asyncio
async def test_handle_transform_lowercase():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {"transform_type": "lowercase"}}
    context = {"current_input": "HELLO WORLD"}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert result.output == "hello world"


@pytest.mark.asyncio
async def test_handle_transform_trim():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {"transform_type": "trim"}}
    context = {"current_input": "  hello  "}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert result.output == "hello"


@pytest.mark.asyncio
async def test_handle_transform_regex_extract():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {
        "transform_type": "regex_extract",
        "pattern": r"\d+"
    }}
    context = {"current_input": "abc 123 def 456"}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert "123" in result.output
    assert "456" in result.output


@pytest.mark.asyncio
async def test_handle_transform_regex_replace():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {
        "transform_type": "regex_replace",
        "pattern": r"\d+",
        "replacement": "NUM"
    }}
    context = {"current_input": "abc 123 def 456"}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert result.output == "abc NUM def NUM"


@pytest.mark.asyncio
async def test_handle_transform_replace():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {
        "transform_type": "replace",
        "pattern": "hello",
        "replacement": "goodbye"
    }}
    context = {"current_input": "hello world hello"}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert result.output == "goodbye world goodbye"


@pytest.mark.asyncio
async def test_handle_transform_substring():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {
        "transform_type": "substring",
        "pattern": "0:5"
    }}
    context = {"current_input": "Hello World"}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert result.output == "Hello"


@pytest.mark.asyncio
async def test_handle_transform_template():
    from node_registry import handle_transform
    node = {"id": "n1", "type": "transform", "config": {
        "transform_type": "template",
        "template": "Prefix: {{input}} Suffix"
    }}
    context = {"current_input": "content"}
    result = await handle_transform(node, context)
    assert result.status == "success"
    assert result.output == "Prefix: content Suffix"


@pytest.mark.asyncio
async def test_handle_merge_concat():
    from node_registry import handle_merge
    node = {"id": "n1", "type": "merge", "config": {"merge_mode": "concat", "separator": "\n"}}
    context = {"merge_inputs": ["a", "b", "c"], "current_input": ""}
    result = await handle_merge(node, context)
    assert result.status == "success"
    assert result.output == "a\nb\nc"


@pytest.mark.asyncio
async def test_handle_merge_json_merge():
    from node_registry import handle_merge
    node = {"id": "n1", "type": "merge", "config": {"merge_mode": "json_merge"}}
    context = {
        "merge_inputs": [json.dumps({"a": 1}), json.dumps({"b": 2})],
        "current_input": ""
    }
    result = await handle_merge(node, context)
    assert result.status == "success"
    merged = json.loads(result.output)
    assert merged["a"] == 1
    assert merged["b"] == 2


@pytest.mark.asyncio
async def test_handle_merge_first():
    from node_registry import handle_merge
    node = {"id": "n1", "type": "merge", "config": {"merge_mode": "first"}}
    context = {"merge_inputs": ["first", "second"], "current_input": ""}
    result = await handle_merge(node, context)
    assert result.status == "success"
    assert result.output == "first"


@pytest.mark.asyncio
async def test_handle_merge_non_empty():
    from node_registry import handle_merge
    node = {"id": "n1", "type": "merge", "config": {"merge_mode": "non_empty"}}
    context = {"merge_inputs": ["", "hello", "", "world"], "current_input": ""}
    result = await handle_merge(node, context)
    assert result.status == "success"
    assert "hello" in result.output
    assert "world" in result.output


@pytest.mark.asyncio
async def test_handle_condition_contains():
    from node_registry import handle_condition
    node = {"id": "n1", "type": "condition", "config": {"condition": "if output contains error"}}
    context = {"current_input": "This is an error message"}
    result = await handle_condition(node, context)
    assert result.status == "success"
    assert context["branch"] == "true"


@pytest.mark.asyncio
async def test_handle_condition_not_contains():
    from node_registry import handle_condition
    node = {"id": "n1", "type": "condition", "config": {"condition": "if output contains error"}}
    context = {"current_input": "Everything is fine"}
    result = await handle_condition(node, context)
    assert result.status == "success"
    assert context["branch"] == "false"


@pytest.mark.asyncio
async def test_handle_condition_not_empty():
    from node_registry import handle_condition
    node = {"id": "n1", "type": "condition", "config": {"condition": "if output is not empty"}}
    context = {"current_input": "some content"}
    result = await handle_condition(node, context)
    assert result.status == "success"
    assert context["branch"] == "true"


@pytest.mark.asyncio
async def test_handle_condition_empty():
    from node_registry import handle_condition
    node = {"id": "n1", "type": "condition", "config": {"condition": "if output is empty"}}
    context = {"current_input": ""}
    result = await handle_condition(node, context)
    assert result.status == "success"
    assert context["branch"] == "true"


@pytest.mark.asyncio
async def test_handle_condition_number():
    from node_registry import handle_condition
    node = {"id": "n1", "type": "condition", "config": {"condition": "if output has number"}}
    context = {"current_input": "abc 123"}
    result = await handle_condition(node, context)
    assert result.status == "success"
    assert context["branch"] == "true"


@pytest.mark.asyncio
async def test_handle_variable_set():
    from node_registry import handle_variable
    node = {"id": "n1", "type": "variable", "config": {
        "variable_name": "test_var",
        "variable_value": "hello",
        "variable_type": "string",
        "mode": "set"
    }}
    context = {}
    result = await handle_variable(node, context)
    assert result.status == "success"
    assert context["test_var"] == "hello"


@pytest.mark.asyncio
async def test_handle_variable_get():
    from node_registry import handle_variable
    node = {"id": "n1", "type": "variable", "config": {
        "variable_name": "test_var",
        "mode": "get",
        "default_value": "default"
    }}
    context = {"test_var": "stored_value"}
    result = await handle_variable(node, context)
    assert result.status == "success"
    assert context["current_input"] == "stored_value"


@pytest.mark.asyncio
async def test_handle_variable_increment():
    from node_registry import handle_variable
    node = {"id": "n1", "type": "variable", "config": {
        "variable_name": "counter",
        "variable_value": "5",
        "mode": "increment"
    }}
    context = {"counter": 10}
    result = await handle_variable(node, context)
    assert result.status == "success"
    assert context["counter"] == 15.0


@pytest.mark.asyncio
async def test_handle_variable_append():
    from node_registry import handle_variable
    node = {"id": "n1", "type": "variable", "config": {
        "variable_name": "log",
        "variable_value": " line",
        "mode": "append"
    }}
    context = {"log": "first"}
    result = await handle_variable(node, context)
    assert result.status == "success"
    assert context["log"] == "first line"


@pytest.mark.asyncio
async def test_handle_guardrails_not_empty():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {"validation_type": "not_empty"}}
    context = {"current_input": "some text"}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "valid"


@pytest.mark.asyncio
async def test_handle_guardrails_not_empty_fail():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {"validation_type": "not_empty"}}
    context = {"current_input": ""}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "invalid"


@pytest.mark.asyncio
async def test_handle_guardrails_json_valid():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {"validation_type": "json_valid"}}
    context = {"current_input": '{"key": "value"}'}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "valid"


@pytest.mark.asyncio
async def test_handle_guardrails_json_valid_fail():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {"validation_type": "json_valid"}}
    context = {"current_input": "not json"}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "invalid"


@pytest.mark.asyncio
async def test_handle_guardrails_contains():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {
        "validation_type": "contains",
        "pattern": "hello"
    }}
    context = {"current_input": "hello world"}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "valid"


@pytest.mark.asyncio
async def test_handle_guardrails_regex():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {
        "validation_type": "regex",
        "pattern": r"\d{3}-\d{4}"
    }}
    context = {"current_input": "Call 555-1234 now"}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "valid"


@pytest.mark.asyncio
async def test_handle_guardrails_max_length():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {
        "validation_type": "max_length",
        "max_length": 10
    }}
    context = {"current_input": "short"}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "valid"


@pytest.mark.asyncio
async def test_handle_guardrails_max_length_fail():
    from node_registry import handle_guardrails
    node = {"id": "n1", "type": "guardrails", "config": {
        "validation_type": "max_length",
        "max_length": 5
    }}
    context = {"current_input": "this is too long"}
    result = await handle_guardrails(node, context)
    assert result.status == "success"
    assert context["branch"] == "invalid"


@pytest.mark.asyncio
async def test_handle_switch_match():
    from node_registry import handle_switch
    node = {"id": "n1", "type": "switch", "config": {
        "cases": "fruits: fruits\ncolors: colors",
        "default_case": "other"
    }}
    context = {"current_input": "I like fruits"}
    result = await handle_switch(node, context)
    assert result.status == "success"
    assert context["branch"] == "fruits"


@pytest.mark.asyncio
async def test_handle_switch_default():
    from node_registry import handle_switch
    node = {"id": "n1", "type": "switch", "config": {
        "cases": "fruits: fruits\ncolors: colors",
        "default_case": "other"
    }}
    context = {"current_input": "something else"}
    result = await handle_switch(node, context)
    assert result.status == "success"
    assert context["branch"] == "other"


@pytest.mark.asyncio
async def test_handle_switch_with_field():
    from node_registry import handle_switch
    node = {"id": "n1", "type": "switch", "config": {
        "switch_field": "category",
        "cases": "tech: technology\nfood: cuisine",
        "default_case": "misc"
    }}
    context = {"category": "tech news", "current_input": "something"}
    result = await handle_switch(node, context)
    assert result.status == "success"
    assert context["branch"] == "technology"


@pytest.mark.asyncio
async def test_handle_loop_first_iteration():
    from node_registry import handle_loop
    node = {"id": "n1", "type": "loop", "config": {"max_iterations": 3}}
    context = {"current_input": "start", "loop_iteration": 0}
    result = await handle_loop(node, context)
    assert result.status == "success"
    assert context["loop_iteration"] == 1
    assert context["loop_done"] is False


@pytest.mark.asyncio
async def test_handle_loop_max_reached():
    from node_registry import handle_loop
    node = {"id": "n1", "type": "loop", "config": {"max_iterations": 2}}
    context = {"current_input": "data", "loop_iteration": 2}
    result = await handle_loop(node, context)
    assert result.status == "success"
    assert context["loop_done"] is True


@pytest.mark.asyncio
async def test_handle_loop_stop_condition():
    from node_registry import handle_loop
    node = {"id": "n1", "type": "loop", "config": {
        "max_iterations": 10,
        "stop_condition": "iteration >= 3"
    }}
    context = {"current_input": "data", "loop_iteration": 3}
    result = await handle_loop(node, context)
    assert result.status == "success"
    assert context["loop_done"] is True


@pytest.mark.asyncio
async def test_handle_delay():
    from node_registry import handle_delay
    node = {"id": "n1", "type": "delay", "config": {"delay_seconds": 0}}
    context = {"current_input": "pass through"}
    result = await handle_delay(node, context)
    assert result.status == "success"
    assert context["current_input"] == "pass through"


@pytest.mark.asyncio
async def test_handle_delay_max_capped():
    from node_registry import handle_delay
    node = {"id": "n1", "type": "delay", "config": {"delay_seconds": 9999}}
    context = {"current_input": "test"}
    result = await handle_delay(node, context)
    assert result.status == "success"


@pytest.mark.asyncio
async def test_handle_output():
    from node_registry import handle_output
    node = {"id": "n1", "type": "output", "config": {}}
    context = {"current_input": "final result"}
    result = await handle_output(node, context)
    assert result.status == "success"
    assert result.output == "final result"
    assert context["final_output"] == "final result"


@pytest.mark.asyncio
async def test_handle_output_with_search():
    from node_registry import handle_output
    node = {"id": "n1", "type": "output", "config": {}}
    context = {
        "current_input": "result",
        "last_search_results": "search data here",
        "last_search_query": "test query"
    }
    result = await handle_output(node, context)
    assert result.status == "success"
    assert "search data here" in result.output


@pytest.mark.asyncio
async def test_handle_webhook_no_url():
    from node_registry import handle_webhook_output
    node = {"id": "n1", "type": "webhook_output", "config": {"webhook_url": ""}}
    context = {"current_input": "test"}
    result = await handle_webhook_output(node, context)
    assert result.status == "error"
    assert "No webhook URL" in result.error


@pytest.mark.asyncio
async def test_handle_custom_code():
    from node_registry import handle_custom
    node = {"id": "n1", "type": "custom", "config": {
        "custom_code": "def process(input, context):\n    return input.upper()",
        "handler_name": "process"
    }}
    context = {"current_input": "hello"}
    result = await handle_custom(node, context)
    assert result.status == "success"
    assert result.output == "HELLO"


@pytest.mark.asyncio
async def test_handle_custom_no_code():
    from node_registry import handle_custom
    node = {"id": "n1", "type": "custom", "config": {"custom_code": ""}}
    context = {"current_input": "test"}
    result = await handle_custom(node, context)
    assert result.status == "error"


def test_parse_action_params():
    from node_registry import _parse_action_params
    params = _parse_action_params("web_search(query='test query', num_results=5)")
    assert params["query"] == "test query"
    assert params["num_results"] == 5


def test_parse_action_params_bool():
    from node_registry import _parse_action_params
    params = _parse_action_params("tool(flag=True, other=False)")
    assert params["flag"] is True
    assert params["other"] is False


def test_fix_param_names():
    from node_registry import _fix_param_names
    params = {"param1": "test", "param2": 5}
    fixed = _fix_param_names("web_search", params)
    assert "query" in fixed
    assert "num_results" in fixed
