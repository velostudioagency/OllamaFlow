# OllamaFlow — Product Demo Walkthrough

> **Tagline:** *Visual AI Workflow Builder — Drag, Connect, Run.*
>
> Build local AI agents by dragging and connecting nodes on an interactive canvas. No cloud required. Zero API keys needed to get started.

---

## 1. The Hook — What Is OllamaFlow?

OllamaFlow is a **local-first, visual AI workflow builder**. Think of it as a whiteboard for AI agents — you drag nodes onto a canvas, wire them together, and suddenly you have an automated AI pipeline running on your own machine.

- **No cloud dependency.** Everything runs locally via Ollama. No accounts, no API keys, no data leaving your computer.
- **Visual programming.** Instead of writing glue code, you connect blocks visually. It's like Node-RED, but purpose-built for LLM workflows.
- **18 node types, 25+ tools, 4 AI providers.** From simple text generation to multi-step research agents with web search, file I/O, browser automation, and vector memory.
- **Free and open source.** MIT license.

---

## 2. Installation — Running in Under 2 Minutes

**Prerequisites:** Python 3.10+, Node.js 18+, and [Ollama](https://ollama.com) with a model pulled (`ollama pull llama3.1:8b`).

### Windows (one-click)
```
install.bat
start.bat
```

### Manual (cross-platform)
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
```

### Docker (full stack)
```bash
docker-compose up
```

Open **http://localhost:5173** and you're in.

### CLI & Python SDK
```bash
# CLI
python ollamaflow_cli.py run "My Workflow" --input "Hello"

# Python SDK
from ollamaflow import OllamaFlow
client = OllamaFlow()
result = await client.run("my_workflow", input_text="Hello")
```

---

## 3. The Canvas — UI Tour

When you open OllamaFlow, you see four main zones:

```
┌─────────────────────────────────────────────────────────┐
│  [≡ Nodes]        [Toolbar: Run · Save · Load · ⚙]    │
│  ┌─────────┐   ┌──────────────────────────────────┐    │
│  │ Input   │   │                                  │    │
│  │ LLM     │   │      [Drag & Drop Canvas]        │    │
│  │ Tool    │   │                                  │    │
│  │ Memory  │   │      ╔══════════════════╗        │    │
│  │ Cond    │   │      ║  ReactFlow Grid  ║        │    │
│  │ Loop    │   │      ║  Infinite Pan    ║        │    │
│  │ ...     │   │      ║  Zoom + Minimap  ║        │    │
│  └─────────┘   │      ╚══════════════════╝        │    │
│                 │                                  │    │
│                 │         Node Config →            │    │
│                 │   ┌────────────────────────┐     │    │
│                 │   │ Model: llama3.1:8b     │     │    │
│                 │   │ System Prompt: ...     │     │    │
│                 │   │ Temperature: 0.7      │     │    │
│                 │   └────────────────────────┘     │    │
│                 └──────────────────────────────────┘    │
│  [Output Panel: Logs · Output · Tokens · History]       │
└─────────────────────────────────────────────────────────┘
```

### Left Sidebar — Node Palette
Drag any node type onto the canvas. Nodes are color-coded:

| Color  | Category      | Purpose                          |
|--------|---------------|----------------------------------|
| Blue   | Input/Output  | Start/end your workflow          |
| Purple | LLM           | Call AI models                   |
| Orange | Tools         | Web search, files, code, browser |
| Green  | Memory        | Store and recall information     |
| Yellow | Logic         | Conditions, branching            |
| Pink   | Flow Control  | Loops, delays, batch processing  |
| Cyan   | Transform     | Text manipulation, JSON querying |
| Red    | Guardrails    | Content validation               |
| Lime   | Custom        | User-defined Python logic        |
| Indigo | Scheduler     | Delays and pauses                |
| Magenta| Variables     | Reusable workflow variables      |

### Center — ReactFlow Canvas
- **Infinite pan** and **zoom** with mouse wheel
- **Minimap** in the bottom-right corner for orientation
- **Grid background** for easy alignment
- **Node handles** — drag from the output handle (right) to an input handle (left) to create connections
- **Node status** — animated glow while running, green pulse on success, red flash on error

### Right Sidebar — Config Panel
Click any node to configure it. Each node type shows relevant settings:
- **LLM node:** Model picker, system prompt, temperature, max tokens
- **Tool node:** Tool selector + its parameters
- **Condition node:** Expression builder

### Bottom Panel — Output & Logs
Real-time execution output with tabs:
- **Logs** — timestamped execution trace
- **Output** — final result display
- **Tokens** — per-node token count and estimated cost
- **History** — past runs with duration and status

---

## 4. Building a Workflow — Step-by-Step Demo

Let's build a **Web Research Agent** that searches the web and summarizes results.

### Step 1: Add an Input Node
Drag an **Input** node (blue) from the palette. This is your workflow's entry point. Configure it with:
- **Mode:** Text prompt
- **Default value:** `"What are the latest developments in AI?"`

### Step 2: Connect a Tool Node for Web Search
Drag a **Tool** node (orange) onto the canvas. Connect the Input node's output handle to the Tool node's input handle.

Configure the Tool node:
- **Tool:** `web_search`
- **Search query:** `{{input}}` (references the upstream input)
- **Max results:** 5

The `web_search` tool runs all available search engines in parallel (DuckDuckGo, Bing, Brave, SearXNG), deduplicates results by URL, and optionally scrapes the top pages for full content.

### Step 3: Add an LLM Node for Summarization
Drag an **LLM** node (purple) and connect it after the Tool node.

Configure:
- **Provider:** Ollama (or Groq/OpenAI/Anthropic if configured)
- **Model:** `llama3.1:8b`
- **System prompt:**
  ```
  Summarize the following search results concisely.
  Highlight key findings, common themes, and notable differences.
  ```
- **Input:** `{{tool_output}}`
- **Temperature:** 0.3 (for factual consistency)

### Step 4: Add an Output Node
Drag an **Output** node (gray) and connect it to the LLM node. This displays the final result in the output panel.

### Step 5: Run It
Click the **Run** button in the toolbar. Watch as:
1. The Input node activates (blue glow)
2. The Tool node runs the web search (orange glow, logs showing "Searching DuckDuckGo...", "Searching Brave...", "Found 5 results")
3. The LLM node streams tokens (purple glow, tokens appearing in the output panel in real time via WebSocket)
4. The Output node receives the final summary and displays it

**Total time:** ~10–30 seconds. **Cost:** $0 (all local).

---

## 5. Node Types — Deep Dive

### Input Nodes
- **Text Prompt** — Manual input or reference `{{input}}` from previous nodes
- **File Upload** — Accept PDF, DOCX, XLSX, images, audio, code files. Automatically converted to Markdown via `markitdown`.
- **Schedule Trigger** — Run on a cron-like interval (e.g., every 15 minutes)

### LLM Nodes
Four AI providers with model aliasing:
| Alias      | Ollama               | Groq            | OpenAI           | Anthropic       |
|------------|----------------------|-----------------|------------------|-----------------|
| Fast       | llama3.1:8b         | llama3.1-8b     | gpt-4o-mini      | claude-3-haiku  |
| Balanced   | llama3.1:70b        | llama3.1-70b    | gpt-4o           | claude-3-sonnet |
| Quality    | mixtral:8x22b       | mixtral-8x7b    | gpt-4o (max)     | claude-3-opus   |
| Code       | codellama           | codellama-70b   | gpt-4o           | claude-3-sonnet |
| Creative   | llama3.1:70b (temp) | llama3.1-70b    | gpt-4o           | claude-3-sonnet |

Switch providers mid-workflow — each LLM node can use a different model.

### Tool Nodes (25+)
| Category        | Tools                                                               |
|-----------------|---------------------------------------------------------------------|
| Web Search      | `web_search` (multi-engine), `web_scraper`, `web_research`          |
| Files           | `read_file`, `write_file`, `list_directory`, `search_files`         |
| Code            | `run_code` (sandboxed Python), `run_command` (shell)                |
| HTTP            | `http_request` (REST), `send_email` (SMTP), `slack_webhook`         |
| Browser         | `playwright_browser`, `browser_use` (AI-driven), `crawl4ai`         |
| Data            | `json_query`, `csv_analyze`, `database_query` (SQLite)              |
| Conversion      | `markitdown` (PDF/Office/images/audio to Markdown)                  |
| Utilities       | `calculate`, `get_datetime`, `random_generate`, `hash_data`         |
| Diff            | `diff_texts` (unified diff)                                         |
| Media           | `youtube_transcript`, `rss_read`                                    |
| System          | `clipboard_copy`, `clipboard_paste`, `rate_limiter`, `file_watcher` |

### Memory Nodes
- **Remember** — Store a value in short-term (JSON) or long-term (ChromaDB vector) memory
- **Recall** — Retrieve by key or semantic search (cosine similarity)
- **Search** — Query long-term memory with natural language
- **Clear** — Reset memory namespace

### Logic & Flow Control Nodes
- **Condition** — If/else branching: `{{input.count > 5}}` routes to True or False output
- **Switch** — Multi-way routing: match input value to one of N cases
- **Loop** — Repeat N times with optional early-stop condition
- **Merge** — Combine outputs from parallel branches
- **Delay** — Pause for N seconds

### Advanced Nodes
- **Guardrails** — Validate LLM output (e.g., "Is this response safe?") and route to valid/invalid paths
- **Variable** — Store, retrieve, modify reusable variables across the workflow
- **Sub-Workflow** — Nest an entire saved workflow as a single node
- **Batch** — Process a list of inputs through a sub-pipeline (map pattern)
- **Custom** — Write arbitrary Python logic with access to workflow context
- **Webhook** — Trigger workflows from external systems via HTTP
- **Webhook Output** — Send workflow output to an external API

---

## 6. Running a Workflow

### Direct Run (Canvas)
Click **Run** — execution follows the DAG in topological order:
- Independent branches run in parallel
- Condition/Switch/Guardrails route selectively
- Each node logs timestamps, duration, and status

### Real-Time Streaming
Output streams token-by-token via WebSocket. You see the LLM "typing" in real time, with the active node highlighted and pulsing on the canvas.

### Chat Interface
The **Chat Panel** lets you interact with any workflow conversationally:
- Type a message → it flows through the workflow → see the response
- Upload files directly in the chat
- Full conversation history

### Stop Mid-Execution
Click the **Stop** button to halt execution at any point. Already-completed nodes keep their results.

### Execution History
Every run is recorded with:
- Timestamp and duration
- Per-node execution logs
- Final output preview
- Token usage breakdown
- Export to JSON or CSV

---

## 7. Advanced Features

### Workflow Scheduling
Schedule any workflow to run automatically:
- **Interval:** Every X minutes (persisted across server restarts)
- **Enable/disable** with a toggle
- Output goes to the history panel; scheduled runs are tagged

### Workflow Versioning
Every save creates an automatic version snapshot:
- View version history with timestamps
- Rollback to any previous version
- Diff between versions (node-by-node comparison)
- Export versions with checksum verification

### Memory System
Two-tier memory architecture:
- **Short-term (JSON):** Recent conversation context (last N items, configurable)
- **Long-term (ChromaDB):** Vector database with semantic search. Store facts, retrieve by similarity. Organized by namespace for multi-agent isolation.

### Plugin System
Extend OllamaFlow without modifying core code:
```json
// plugins/my-plugin/manifest.json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "nodes": ["AnalyticsNode"],
  "tools": ["analytics_query"]
}
```
- Drop a folder into `plugins/` — auto-detected on server start
- Register new node types and tools dynamically
- Template generator: `python plugin_loader.py generate my-plugin`

### Token Cost Tracking
Per-node, per-provider token counts with pricing:
- **Groq:** Free tier (token counts only)
- **OpenAI:** $0.15–$10.00/1M tokens depending on model
- **Anthropic:** $0.25–$15.00/1M tokens
- **Ollama:** Local — $0

View cost breakdown in the Output Panel's **Tokens** tab.

### PDF Generation
Export any workflow output as a PDF with `reportlab`.

---

## 8. Use Cases & Example Workflows

### Web Research Agent
Auto search → scrape → summarize → save report. Ships as a built-in example.

### File Summarizer
Drop in a PDF, DOCX, or image. It's converted to Markdown, summarized by an LLM, and the summary is displayed.

### Multi-Step Research Report
End-to-end pipeline: search multiple queries → scrape pages → analyze each → synthesize into a structured report.

### RAG Agent
Ingest documents → embed into ChromaDB → answer questions with retrieved context.

### Data Pipeline
Read CSV → clean with LLM → analyze → write results → email the output.

### Content Monitor
Schedule a workflow to scan RSS feeds or search for keywords every 15 minutes. Alert via Slack or email when new content matches criteria.

### AI Chatbot with Memory
Input node → short-term memory → LLM with system prompt → long-term memory recall → output. A persistent chatbot that remembers past conversations.

### Batch Document Processor
Drop 100 PDFs into a folder → batch node processes each → LLM extracts key fields → outputs to CSV.

---

## 9. Web Search — Multi-Engine Architecture

OllamaFlow's search system is designed for reliability and coverage:

**Auto mode** runs all configured engines in parallel:
1. **Brave Search** (fast, independent index, 2,000 free queries/month)
2. **SearXNG** (self-hosted meta-search: Google + Bing + DDG)
3. **DuckDuckGo** (no setup, unlimited, always-on fallback)
4. **Bing** (scraped RSS, no API key)

Results are deduplicated by URL, scored by relevance, and the top N are returned. Optionally, each result's page is scraped for full content.

**Zero configuration required.** It works out of the box with DuckDuckGo as the default.

---

## 10. Extensibility

### Plugin System
Create custom nodes and tools without forking the repo:
```bash
python plugin_loader.py generate my-plugin
# Edit plugins/my-plugin/plugin.py + manifest.json
# Restart server — auto-loaded
```

### Python SDK
Integrate OllamaFlow into your own applications:
```python
from ollamaflow import OllamaFlow

client = OllamaFlow("http://localhost:8000")

# Run a workflow
result = await client.run("My Workflow", input_text="Analyze this")

# Stream results
async for event in client.run_stream("My Workflow", input_text="Analyze"):
    print(event)

# List available tools
tools = await client.get_tools()
```

### CLI
```bash
python ollamaflow_cli.py list              # List workflows
python ollamaflow_cli.py run "My Flow" -i "Hi"  # Run
python ollamaflow_cli.py models            # List Ollama models
python ollamaflow_cli.py tools             # List tools
python ollamaflow_cli.py serve             # Start server
```

### REST API
Full REST + WebSocket API for programmatic control (see `/api/health` for a quick check, `/api/node-types` for schema definitions).

---

## 11. Deployment

### Local (default)
```bash
python start.py
```
Opens at `http://localhost:5173`.

### Docker
```bash
docker-compose up
```
Runs backend + frontend + Ollama in containers. Optional Firecrawl + Redis for advanced scraping.

### Docker with Firecrawl
```bash
docker-compose --profile firecrawl up
```

### Production Considerations
- Set `CORS_ORIGINS` to your domain (not `*`)
- Enable `API_TOKEN` authentication on all endpoints
- Configure `SEARCH_PROVIDERS` for your preferred engines
- Volume-mount `./data` and `./workspace` for persistence

---

## 12. Security

- **Code sandboxing:** `run_code` uses a blocklist of dangerous modules (`os`, `subprocess`, `shutil`, etc.)
- **Safe expressions:** `safe_eval()` with restricted builtins — no arbitrary code execution in condition/Switch nodes
- **Command safety:** `run_command` validates against a blocklist
- **CORS:** Configurable origins (not wildcard in production)
- **Auth:** Optional Bearer token on all endpoints
- **File isolation:** File tools are restricted to the `workspace/` directory

---

## 13. Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, LangChain, ChromaDB, WebSockets |
| Frontend | React 18, ReactFlow 11, TailwindCSS 3.4, Vite 5 |
| AI Engines | Ollama (local), Groq, OpenAI, Anthropic |
| Web Search | DuckDuckGo, Bing, Brave, SearXNG (parallel auto-fallback) |
| Browser | Playwright, browser-use, crawl4ai, firecrawl, crawlee |
| Memory | JSON (short-term), ChromaDB (long-term vector) |
| Deployment | Docker, Docker Compose |
| Testing | pytest, pytest-asyncio |

---

## 14. Closing

**OllamaFlow** turns the complexity of LLM agent orchestration into a visual, drag-and-drop experience. Whether you're prototyping a quick AI assistant, building a production data pipeline, or exploring what's possible with local LLMs, OllamaFlow gives you a canvas to experiment and build — all without leaving your machine, spending a cent, or sending your data to the cloud.

> *Visual AI Workflow Builder — Drag, Connect, Run.*

---

*This demo walkthrough was generated from the OllamaFlow codebase. For the latest information, visit the repository or run `python ollamaflow_cli.py --help`.*
