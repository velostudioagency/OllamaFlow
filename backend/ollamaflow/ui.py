"""
OllamaFlow CLI - UI helpers: banner, colors, panels, tables, markdown rendering.
"""

import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.columns import Columns
from rich import box

console = Console()

VERSION = "0.1.0"

BANNER_MINI = f"""[bold cyan]OllamaFlow CLI[/] v{VERSION}
[dim]Type /help for commands[/]"""

BANNER_FULL = r"""
[bold cyan]
  ___  _ _ _ _____ _    _     ___
 / _ \| | | |_   _| |  | |   / _ \
| | | | | | | | | | |  | |  | | | |
| |_| | | | | | | | |/\| |__| |_| |
 \___/|_|_|_| |_| \__/\____/ \___/
[/]
[bold]OllamaFlow[/] [dim]v{ver}[/] — Local-first visual AI workflow builder
[dim]Type /help for commands[/]""".format(ver=VERSION)


def print_banner(full=False):
    """Print the startup banner."""
    if full:
        console.print(Panel(BANNER_FULL, border_style="cyan", expand=False))
    else:
        console.print(BANNER_MINI)


def print_server_status(port, ollama_connected, model_count):
    """Print the server status line."""
    ollama_text = "[green]connected[/]" if ollama_connected else "[red]disconnected[/]"
    console.print(
        f"[dim]OllamaFlow API: :{port} | Ollama: {ollama_text} | Models: {model_count}[/]"
    )


def print_success(msg):
    console.print(f"[green]✓[/] {msg}")


def print_error(msg):
    console.print(f"[red]✗[/] {msg}")


def print_info(msg):
    console.print(f"[cyan]ℹ[/] {msg}")


def print_warning(msg):
    console.print(f"[yellow]⚠[/] {msg}")


def print_markdown(text):
    """Render markdown text with rich."""
    console.print(Markdown(text))


def print_table(title, columns, rows, caption=None):
    """Print a rich table."""
    table = Table(title=title, box=box.ROUNDED, show_lines=False)
    for col in columns:
        table.add_column(col, style="cyan" if col == columns[0] else None)
    for row in rows:
        table.add_row(*[str(c) for c in row])
    if caption:
        table.caption = caption
    console.print(table)


def print_workflow_table(workflows):
    """Print workflows as a rich table."""
    table = Table(title="Saved Workflows", box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Saved")
    table.add_column("Nodes", justify="right")
    for wf in workflows:
        name = wf.get("name", "unknown")
        saved = wf.get("saved_at", "Unknown")
        if saved and len(saved) > 16:
            saved = saved[:16]
        nodes = str(wf.get("node_count", 0))
        table.add_row(name, saved, nodes)
    console.print(table)


def print_models_table(models):
    """Print available models as a rich table."""
    table = Table(title="Available Models", box=box.ROUNDED)
    table.add_column("Model", style="cyan")
    for model in models:
        table.add_row(model)
    console.print(table)


def print_tools_table(tools):
    """Print available tools as a rich table."""
    table = Table(title="Available Tools", box=box.ROUNDED)
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Description")
    for tool in tools:
        name = tool.get("name", "unknown")
        desc = tool.get("description", "")[:80]
        table.add_row(name, desc)
    console.print(table)


def print_versions_table(versions, workflow_name):
    """Print workflow version history."""
    table = Table(title=f"Versions: {workflow_name}", box=box.ROUNDED)
    table.add_column("Timestamp", style="cyan")
    table.add_column("Saved At")
    table.add_column("Nodes", justify="right")
    for v in versions:
        table.add_row(
            v.get("timestamp", ""),
            v.get("saved_at", ""),
            str(v.get("node_count", 0)),
        )
    console.print(table)


def prompt_choice(prompt_text, options, allow_empty=False):
    """Prompt user to pick from numbered options. Returns selected value."""
    for i, opt in enumerate(options, 1):
        console.print(f"  [cyan]{i}[/]. {opt}")
    while True:
        try:
            choice = console.input(f"[bold]{prompt_text}[/] > ").strip()
            if not choice and allow_empty:
                return None
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx]
            # Try matching by name
            for opt in options:
                if choice.lower() == opt.lower():
                    return opt
            print_error(f"Invalid choice. Enter 1-{len(options)} or a name.")
        except (EOFError, KeyboardInterrupt):
            return None


def prompt_input(prompt_text, default=None, password=False):
    """Prompt for text input with optional default."""
    suffix = f" [dim][{default}][/]" if default else ""
    try:
        value = console.input(f"[bold]{prompt_text}{suffix}[/] > ").strip()
        if not value and default is not None:
            return default
        return value
    except (EOFError, KeyboardInterrupt):
        return default


def prompt_confirm(prompt_text, default=True):
    """Prompt for Y/n confirmation."""
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        value = console.input(f"[bold]{prompt_text}[/] {suffix} > ").strip().lower()
        if not value:
            return default
        return value in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return default


def print_ascii_diagram(workflow):
    """Print an ASCII box-and-arrow diagram of the workflow."""
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])

    if not nodes:
        print_warning("No nodes in workflow.")
        return

    node_map = {n["id"]: n for n in nodes}
    node_ids = list(node_map.keys())

    # Build adjacency: source -> targets
    adj = {}
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        adj.setdefault(src, []).append(tgt)

    # Find entry nodes (no incoming edges)
    has_incoming = {e.get("target") for e in edges}
    entries = [nid for nid in node_ids if nid not in has_incoming]
    if not entries:
        entries = [node_ids[0]]

    # BFS to get order
    visited = []
    queue = list(entries)
    seen = set()
    while queue:
        nid = queue.pop(0)
        if nid in seen or nid not in node_map:
            continue
        seen.add(nid)
        visited.append(nid)
        for tgt in adj.get(nid, []):
            if tgt not in seen:
                queue.append(tgt)
    # Add any unvisited nodes
    for nid in node_ids:
        if nid not in visited:
            visited.append(nid)

    if len(visited) == 0:
        print_warning("No nodes to display.")
        return

    # Render boxes
    BOX_W = 12
    boxes = {}
    for nid in visited:
        node = node_map[nid]
        ntype = node.get("type", "?")
        label = nid
        if len(label) > BOX_W - 2:
            label = label[:BOX_W - 2]
        type_label = f"({ntype})"
        pad_id = label.center(BOX_W)
        pad_type = type_label.center(BOX_W)
        boxes[nid] = [pad_id, pad_type]

    # Group into rows of 3
    rows_of = 3
    for row_start in range(0, len(visited), rows_of):
        row_ids = visited[row_start:row_start + rows_of]
        # Top border
        top = "     ".join(f"+{'-' * BOX_W}+" for _ in row_ids)
        console.print(f"  {top}")
        # ID line
        id_line = "     ".join(f"|{boxes[nid][0]}|" for nid in row_ids)
        console.print(f"  {id_line}")
        # Type line
        type_line = "     ".join(f"|{boxes[nid][1]}|" for nid in row_ids)
        console.print(f"  {type_line}")
        # Bottom border
        bot = "     ".join(f"+{'-' * BOX_W}+" for _ in row_ids)
        console.print(f"  {bot}")

        # Arrows between nodes in this row
        arrows = []
        for i, nid in enumerate(row_ids):
            targets = adj.get(nid, [])
            connected = [t for t in targets if t in node_map]
            if connected and i < len(row_ids) - 1:
                arrows.append("    ───▶ ")
            else:
                arrows.append("         ")
        # Only print arrows if there are connections
        if any(adj.get(nid, []) for nid in row_ids):
            arrow_line = "     ".join(
                f"    ───▶ " if adj.get(nid) else "         " for nid in row_ids
            )

    # Also show connections text
    if edges:
        console.print()
        console.print("  [dim]Connections:[/]")
        for e in edges:
            src = e.get("source", "?")
            tgt = e.get("target", "?")
            console.print(f"    [cyan]{src}[/] → [cyan]{tgt}[/]")


def print_validation_result(results):
    """Print validation results."""
    console.print()
    for passed, msg in results:
        if passed:
            console.print(f"  [green]✓[/] {msg}")
        else:
            console.print(f"  [yellow]⚠[/] {msg}")
    console.print()
    warnings = sum(1 for p, _ in results if not p)
    if warnings:
        console.print(f"  [yellow]{warnings} warning(s)[/] — workflow can still be saved")
    else:
        console.print("  [green]All checks passed[/]")
