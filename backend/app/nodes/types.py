from app.tools.definitions import TOOL_DEFINITIONS


NODE_TYPES = {
    "input": {
        "type": "input",
        "label": "Input Node",
        "color": "#3B82F6",
        "category": "trigger",
        "icon": "📥",
        "description": "Starting point of the workflow. Provides the initial input/goal.",
        "config_schema": {
            "prompt": {"type": "string", "label": "Goal / Prompt", "default": ""},
            "input_type": {"type": "select", "label": "Input Type",
                          "options": ["text", "file_upload", "scheduled"],
                          "default": "text"},
            "file_path": {"type": "string", "label": "File Path", "default": ""}
        },
        "inputs": 0,
        "outputs": 1
    },
    "llm": {
        "type": "llm",
        "label": "LLM Node",
        "color": "#8B5CF6",
        "category": "ai",
        "icon": "🧠",
        "description": "AI brain node. Sends input to an Ollama LLM and returns the response.",
        "config_schema": {
            "model": {"type": "string", "label": "Model", "default": "llama3.1:8b"},
            "system_prompt": {"type": "textarea", "label": "System Prompt",
                             "default": "You are a helpful assistant."},
            "temperature": {"type": "slider", "label": "Temperature", "min": 0, "max": 1,
                           "step": 0.1, "default": 0.7},
            "max_tokens": {"type": "slider", "label": "Max Tokens", "min": 100, "max": 4000,
                          "step": 100, "default": 2000}
        },
        "inputs": 1,
        "outputs": 1
    },
    "tool": {
        "type": "tool",
        "label": "Tool Node",
        "color": "#F97316",
        "category": "tools",
        "icon": "🛠️",
        "description": "Gives the agent an ability/action like web search, file I/O, or code execution.",
        "config_schema": {
            "tool_name": {"type": "select", "label": "Tool",
                         "options": list(TOOL_DEFINITIONS.keys()),
                         "default": "web_search"}
        },
        "inputs": 1,
        "outputs": 1
    },
    "memory": {
        "type": "memory",
        "label": "Memory Node",
        "color": "#22C55E",
        "category": "memory",
        "icon": "💾",
        "description": "Gives the agent memory capabilities - short-term or long-term.",
        "config_schema": {
            "namespace": {"type": "string", "label": "Namespace", "default": "default"},
            "memory_type": {"type": "select", "label": "Memory Type",
                           "options": ["short_term", "long_term"],
                           "default": "long_term"},
            "action": {"type": "select", "label": "Action",
                      "options": ["remember", "recall", "search", "clear"],
                      "default": "remember"},
            "search_query": {"type": "string", "label": "Search Query", "default": ""}
        },
        "inputs": 1,
        "outputs": 1
    },
    "condition": {
        "type": "condition",
        "label": "Condition Node",
        "color": "#EAB308",
        "category": "logic",
        "icon": "🔀",
        "description": "If/else branching logic. Routes workflow based on conditions.",
        "config_schema": {
            "condition": {"type": "string", "label": "Condition",
                         "default": "if output contains error"}
        },
        "inputs": 1,
        "outputs": 2
    },
    "loop": {
        "type": "loop",
        "label": "Loop Node",
        "color": "#EC4899",
        "category": "logic",
        "icon": "🔁",
        "description": "Repeat an action N times or until a condition is met.",
        "config_schema": {
            "max_iterations": {"type": "number", "label": "Max Iterations", "default": 5},
            "stop_condition": {"type": "string", "label": "Stop Condition", "default": ""}
        },
        "inputs": 1,
        "outputs": 1
    },
    "output": {
        "type": "output",
        "label": "Output Node",
        "color": "#6B7280",
        "category": "output",
        "icon": "📤",
        "description": "End of the workflow. Displays the final result.",
        "config_schema": {},
        "inputs": 1,
        "outputs": 0
    },
    "transform": {
        "type": "transform",
        "label": "Transform Node",
        "color": "#06B6D4",
        "category": "tools",
        "icon": "✨",
        "description": "Transform text with regex, substring, case changes, JSON path, or templates.",
        "config_schema": {
            "transform_type": {"type": "select", "label": "Transform",
                               "options": ["regex_extract", "regex_replace", "substring", "uppercase", "lowercase", "trim", "replace", "json_path", "template"],
                               "default": "trim"},
            "pattern": {"type": "string", "label": "Pattern / Path", "default": ""},
            "replacement": {"type": "string", "label": "Replacement", "default": ""},
            "template": {"type": "textarea", "label": "Template (use {{input}})", "default": "{{input}}"}
        },
        "inputs": 1,
        "outputs": 1
    },
    "merge": {
        "type": "merge",
        "label": "Merge Node",
        "color": "#A78BFA",
        "category": "logic",
        "icon": "🔗",
        "description": "Combine outputs from multiple upstream branches.",
        "config_schema": {
            "merge_mode": {"type": "select", "label": "Mode",
                           "options": ["concat", "newline", "json_merge", "first", "non_empty"],
                           "default": "concat"},
            "separator": {"type": "string", "label": "Separator", "default": "\n\n"}
        },
        "inputs": 2,
        "outputs": 1
    },
    "delay": {
        "type": "delay",
        "label": "Delay Node",
        "color": "#6366F1",
        "category": "logic",
        "icon": "⏱️",
        "description": "Pause workflow execution for a set number of seconds.",
        "config_schema": {
            "delay_seconds": {"type": "number", "label": "Delay (seconds)", "default": 5}
        },
        "inputs": 1,
        "outputs": 1
    },
    "switch": {
        "type": "switch",
        "label": "Switch Node",
        "color": "#F59E0B",
        "category": "logic",
        "icon": "🔀",
        "description": "Multi-way routing based on input value matching.",
        "config_schema": {
            "switch_field": {"type": "string", "label": "Context Key (blank = use input)", "default": ""},
            "cases": {"type": "textarea", "label": "Cases (one per line: value: label)", "default": ""},
            "default_case": {"type": "string", "label": "Default Label", "default": "default"}
        },
        "inputs": 1,
        "outputs": 4
    },
    "webhook": {
        "type": "webhook",
        "label": "Webhook Node",
        "color": "#10B981",
        "category": "trigger",
        "icon": "🪝",
        "description": "Send/receive data via HTTP webhook.",
        "config_schema": {
            "webhook_url": {"type": "string", "label": "Webhook URL", "default": ""},
            "method": {"type": "select", "label": "Method", "options": ["POST", "GET", "PUT"], "default": "POST"},
            "auth_token": {"type": "string", "label": "Auth Token (optional)", "default": ""}
        },
        "inputs": 0,
        "outputs": 1
    },
    "guardrails": {
        "type": "guardrails",
        "label": "Guardrails Node",
        "color": "#F43F5E",
        "category": "ai",
        "icon": "🛡️",
        "description": "Validate LLM output and route to valid/invalid paths.",
        "config_schema": {
            "validation_type": {"type": "select", "label": "Validation",
                                "options": ["not_empty", "json_valid", "contains", "regex", "max_length", "min_length", "custom"],
                                "default": "not_empty"},
            "pattern": {"type": "string", "label": "Pattern / Required Text", "default": ""},
            "max_length": {"type": "number", "label": "Max/Min Length", "default": 5000},
            "retry_on_fail": {"type": "boolean", "label": "Retry on Fail", "default": False},
            "max_retries": {"type": "number", "label": "Max Retries", "default": 3}
        },
        "inputs": 1,
        "outputs": 2
    },
    "variable": {
        "type": "variable",
        "label": "Variable Node",
        "color": "#D946EF",
        "category": "tools",
        "icon": "📦",
        "description": "Store, retrieve, or modify reusable variables across the workflow.",
        "config_schema": {
            "variable_name": {"type": "string", "label": "Variable Name", "default": "my_var"},
            "variable_value": {"type": "textarea", "label": "Value / Expression", "default": ""},
            "variable_type": {"type": "select", "label": "Type",
                              "options": ["string", "number", "boolean", "json"],
                              "default": "string"},
            "mode": {"type": "select", "label": "Mode",
                     "options": ["set", "get", "increment", "append"],
                     "default": "set"},
            "default_value": {"type": "string", "label": "Default Value (for get)", "default": ""}
        },
        "inputs": 1,
        "outputs": 1
    },
    "subworkflow": {
        "type": "subworkflow",
        "label": "Sub-Workflow Node",
        "color": "#0EA5E9",
        "category": "logic",
        "icon": "📐",
        "description": "Nest another workflow inside this node and run it as a sub-pipeline.",
        "config_schema": {
            "subworkflow_json": {"type": "textarea", "label": "Sub-Workflow JSON", "default": ""},
            "pass_input": {"type": "boolean", "label": "Pass Current Input", "default": True}
        },
        "inputs": 1,
        "outputs": 1
    },
    "batch": {
        "type": "batch",
        "label": "Batch Node",
        "color": "#F472B6",
        "category": "logic",
        "icon": "📊",
        "description": "Process lists of inputs through a sub-pipeline, one item at a time.",
        "config_schema": {
            "subworkflow_json": {"type": "textarea", "label": "Sub-Workflow JSON", "default": ""},
            "batch_mode": {"type": "select", "label": "Split Mode",
                           "options": ["split_newline", "split_comma", "json_array"],
                           "default": "split_newline"}
        },
        "inputs": 1,
        "outputs": 1
    },
    "custom": {
        "type": "custom",
        "label": "Custom Node",
        "color": "#A3E635",
        "category": "tools",
        "icon": "⚙️",
        "description": "Define custom logic with Python code. Write a process(input, context) function.",
        "config_schema": {
            "custom_code": {"type": "textarea", "label": "Python Code",
                           "default": "def process(input, context):\n    return input"},
            "handler_name": {"type": "string", "label": "Handler Function", "default": "process"}
        },
        "inputs": 1,
        "outputs": 1
    },
    "webhook_output": {
        "type": "webhook_output",
        "label": "Webhook Output",
        "color": "#F97316",
        "category": "output",
        "icon": "📤",
        "description": "Send workflow output to an external API when the workflow completes.",
        "config_schema": {
            "webhook_url": {"type": "string", "label": "Webhook URL", "default": ""},
            "method": {"type": "select", "label": "HTTP Method",
                       "options": ["POST", "PUT", "PATCH"],
                       "default": "POST"},
            "auth_token": {"type": "string", "label": "Auth Token", "default": ""},
            "auth_header": {"type": "string", "label": "Auth Header", "default": "Authorization"},
            "content_type": {"type": "select", "label": "Content Type",
                             "options": ["application/json", "text/plain", "application/x-www-form-urlencoded"],
                             "default": "application/json"},
            "custom_headers": {"type": "textarea", "label": "Custom Headers (Key: Value per line)", "default": ""},
            "include_context": {"type": "boolean", "label": "Include Workflow Context", "default": False},
            "retry_count": {"type": "slider", "label": "Retry Count", "min": 1, "max": 5, "step": 1, "default": 3},
            "retry_delay": {"type": "slider", "label": "Retry Delay (s)", "min": 1, "max": 10, "step": 1, "default": 1}
        },
        "inputs": 1,
        "outputs": 0
    }
}
