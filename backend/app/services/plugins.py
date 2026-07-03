"""
OllamaFlow Plugin System

Loads external tool/node packages from a plugins directory.

Plugin structure:
    plugins/
        my_plugin/
            __init__.py        # Plugin entry point with register() function
            plugin.json        # Manifest: name, version, description, node_types, tools
            nodes/             # Optional: custom node handler modules
            tools/             # Optional: custom tool handler modules

plugin.json format:
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "My custom plugin",
    "author": "Author Name",
    "node_types": ["custom_node_type"],
    "tools": ["custom_tool_name"],
    "entry_point": "register"
}

register() function signature:
    def register(registry: PluginRegistry) -> None:
        registry.register_node(type_name, handler_fn, metadata_dict)
        registry.register_tool(tool_name, handler_fn, metadata_dict)
"""

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class PluginRegistry:
    """Registry that plugins use to register new node types and tools."""

    def __init__(self):
        self._node_handlers: Dict[str, Callable] = {}
        self._node_types: Dict[str, Dict] = {}
        self._tools: Dict[str, Dict] = {}
        self._loaded_plugins: List[Dict] = []

    def register_node(
        self,
        node_type: str,
        handler: Callable,
        metadata: Dict[str, Any],
    ) -> None:
        """Register a new node type."""
        if node_type in self._node_handlers:
            print(f"[Plugin] Warning: Overwriting existing node type '{node_type}'")
        self._node_handlers[node_type] = handler
        self._node_types[node_type] = metadata
        print(f"[Plugin] Registered node type: {node_type}")

    def register_tool(
        self,
        tool_name: str,
        handler: Callable,
        metadata: Dict[str, Any],
    ) -> None:
        """Register a new tool."""
        if tool_name in self._tools:
            print(f"[Plugin] Warning: Overwriting existing tool '{tool_name}'")
        self._tools[tool_name] = metadata
        print(f"[Plugin] Registered tool: {tool_name}")

    def get_node_handlers(self) -> Dict[str, Callable]:
        return dict(self._node_handlers)

    def get_node_types(self) -> Dict[str, Dict]:
        return dict(self._node_types)

    def get_tools(self) -> Dict[str, Dict]:
        return dict(self._tools)

    def get_loaded_plugins(self) -> List[Dict]:
        return list(self._loaded_plugins)


class PluginManager:
    """Discovers and loads plugins from the plugins directory."""

    def __init__(self, plugins_dir: Optional[str] = None):
        if plugins_dir is None:
            plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
        self.plugins_dir = Path(plugins_dir)
        self.registry = PluginRegistry()
        self._loaded = False

    def discover_plugins(self) -> List[str]:
        """Find all valid plugin directories."""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return []

        plugins = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                manifest = item / "plugin.json"
                if manifest.exists():
                    plugins.append(item.name)
        return plugins

    def load_all(self) -> None:
        """Load all discovered plugins."""
        if self._loaded:
            return

        plugins = self.discover_plugins()
        print(f"[Plugin] Found {len(plugins)} plugin(s)")

        for plugin_name in plugins:
            try:
                self._load_plugin(plugin_name)
            except Exception as e:
                print(f"[Plugin] Failed to load '{plugin_name}': {e}")

        self._loaded = True

    def _load_plugin(self, plugin_name: str) -> None:
        """Load a single plugin."""
        plugin_dir = self.plugins_dir / plugin_name
        manifest_path = plugin_dir / "plugin.json"

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Validate manifest
        if "name" not in manifest:
            raise ValueError("Plugin manifest missing 'name'")
        if "entry_point" not in manifest:
            manifest["entry_point"] = "register"

        # Add plugin dir to sys.path temporarily
        plugin_dir_str = str(plugin_dir)
        if plugin_dir_str not in sys.path:
            sys.path.insert(0, plugin_dir_str)

        try:
            # Import the entry point module
            entry_module_name = manifest.get("entry_module", "__init__")
            spec = importlib.util.spec_from_file_location(
                f"ollamaflow_plugin_{plugin_name}",
                plugin_dir / f"{entry_module_name}.py",
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load entry module '{entry_module_name}'")

            module = importlib.util.module_from_spec(spec)
            sys.modules[f"ollamaflow_plugin_{plugin_name}"] = module
            spec.loader.exec_module(module)

            # Call the register function
            register_fn = getattr(module, manifest["entry_point"], None)
            if register_fn is None:
                raise ImportError(f"Entry point '{manifest['entry_point']}' not found")

            register_fn(self.registry)

            # Track loaded plugin
            self.registry._loaded_plugins.append({
                "name": manifest["name"],
                "version": manifest.get("version", "0.0.0"),
                "description": manifest.get("description", ""),
                "author": manifest.get("author", ""),
                "node_types": manifest.get("node_types", []),
                "tools": manifest.get("tools", []),
            })

            print(f"[Plugin] Loaded: {manifest['name']} v{manifest.get('version', '0.0.0')}")

        finally:
            if plugin_dir_str in sys.path:
                sys.path.remove(plugin_dir_str)

    def apply_to_registry(self) -> None:
        """Apply all registered plugins to the main node registry."""
        if not self._loaded:
            self.load_all()

        from app.nodes.handlers import NODE_HANDLERS
        from app.nodes.types import NODE_TYPES
        from app.tools.definitions import TOOL_DEFINITIONS

        # Register new node types
        for node_type, handler in self.registry.get_node_handlers().items():
            NODE_HANDLERS[node_type] = handler

        for node_type, metadata in self.registry.get_node_types().items():
            NODE_TYPES[node_type] = metadata

        # Register new tools
        for tool_name, tool_meta in self.registry.get_tools().items():
            if tool_name not in TOOL_DEFINITIONS:
                TOOL_DEFINITIONS[tool_name] = {
                    "name": tool_name,
                    "description": tool_meta.get("description", ""),
                    "handler": tool_meta.get("handler", lambda **kwargs: "Not implemented"),
                    "parameters": tool_meta.get("parameters", {}),
                }


def create_plugin_template(plugin_name: str, plugins_dir: Optional[str] = None) -> str:
    """Create a new plugin template directory."""
    if plugins_dir is None:
        plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")

    plugin_dir = Path(plugins_dir) / plugin_name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    nodes_dir = plugin_dir / "nodes"
    nodes_dir.mkdir(exist_ok=True)
    tools_dir = plugin_dir / "tools"
    tools_dir.mkdir(exist_ok=True)

    # Create manifest
    manifest = {
        "name": plugin_name,
        "version": "0.1.0",
        "description": f"A custom OllamaFlow plugin: {plugin_name}",
        "author": "",
        "node_types": ["example_node"],
        "tools": ["example_tool"],
        "entry_point": "register",
    }
    with open(plugin_dir / "plugin.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Create entry point
    init_code = f'''"""
OllamaFlow Plugin: {plugin_name}
"""

from ollamaflow_plugin_{plugin_name}.nodes.example_node import handle_example_node
from ollamaflow_plugin_{plugin_name}.tools.example_tool import execute_example_tool


def register(registry):
    """Register plugin node types and tools with OllamaFlow."""
    registry.register_node(
        "example_node",
        handle_example_node,
        {{
            "type": "example_node",
            "label": "Example Node",
            "color": "#10B981",
            "category": "tools",
            "icon": "\\U0001f527",
            "description": "A custom plugin node.",
            "config_schema": {{
                "message": {{"type": "string", "label": "Message", "default": "Hello from plugin!"}},
            }},
            "inputs": 1,
            "outputs": 1,
        }},
    )

    registry.register_tool(
        "example_tool",
        execute_example_tool,
        {{
            "name": "example_tool",
            "description": "An example plugin tool.",
            "parameters": {{
                "text": {{"type": "string", "description": "Input text", "required": True}},
            }},
            "handler": execute_example_tool,
        }},
    )
'''
    with open(plugin_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_code)

    # Create example node handler
    node_code = '''"""Example node handler for the plugin template."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

try:
    from node_registry import NodeResult
except ImportError:
    from dataclasses import dataclass

    @dataclass
    class NodeResult:
        output: str
        status: str = "success"
        error: str = ""


async def handle_example_node(node: dict, context: dict) -> NodeResult:
    """Handle the example_node type."""
    config = node.get("config", {})
    message = config.get("message", "Hello from plugin!")
    current_input = context.get("current_input", "")

    output = f"{message}\\\\nInput was: {current_input}"
    context["current_input"] = output
    return NodeResult(output=output)
'''
    with open(nodes_dir / "example_node.py", "w", encoding="utf-8") as f:
        f.write(node_code)

    # Create example tool handler
    tool_code = '''"""Example tool handler for the plugin template."""


def execute_example_tool(text: str = "") -> str:
    """Execute the example tool."""
    return f"Example tool processed: {text}"
'''
    with open(tools_dir / "example_tool.py", "w", encoding="utf-8") as f:
        f.write(tool_code)

    print(f"[Plugin] Created template at: {plugin_dir}")
    return str(plugin_dir)
