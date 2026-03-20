# log-analyzer

Agentic pipeline that reads `failure.log`, extracts power-plant-related entries,
compresses them to ≤ 1 500 tokens, and submits them to the verification hub.
Each iteration requires explicit human approval before the next run begins.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        agent loop  (src/agent.py)               │
│                                                                  │
│  1. MCPClient  ──stdio──►  MCP Server (src/mcp_server.py)       │
│       read_log_file       (paginates 2 100+ rows in batches)     │
│       filter_power_plant  (regex – ECCS, REACTOR, WTANK, …)     │
│       compress_logs       (deduplicate | top_severity | truncate)│
│       count_tokens        (cl100k_base, same as OAI tokenizer)   │
│       get_session_history (load previous iterations)             │
│                                                                  │
│  2. DSPy  (AnalyzeLogs signature)                               │
│       LLM makes the final editorial selection                    │
│       Takes hub_feedback + previous_answer into account          │
│                                                                  │
│  3. Submit  POST → https://hub.ag3nts.org/verify                 │
│                                                                  │
│  4. DSPy  (EvaluateHubResponse)                                  │
│       Parses hub reply, produces action plan for next iteration  │
│                                                                  │
│  5. Human gate  ──► approve / stop + optional notes             │
│       session_history.json updated before next iteration begins  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick start

### 1 – Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or `brew install uv`)

### 2 – Install

```bash
git clone <this-repo>
cd log-analyzer
uv sync
```

### 3 – Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | Your key from https://openrouter.ai |
| `OPENROUTER_MODEL` | e.g. `openrouter/anthropic/claude-3.5-sonnet` |
| `HUB_API_KEY` | Your key for https://hub.ag3nts.org |
| `HUB_URL` | Verification endpoint (default pre-filled) |
| `HUB_TASK` | Task name (default `failure`) |
| `LOG_FILE_PATH` | Path to `failure.log` (default: project root) |
| `TOKEN_BUDGET` | Max tokens for submitted logs (default `1500`) |

### 4 – Place the log file

Copy your `failure.log` into the project root (or set `LOG_FILE_PATH` in `.env`
to the absolute path).

### 5 – Run

```bash
uv run analyze
```

Or equivalently:

```bash
uv run python -m src.main
```

---

## Iteration flow

```
Iteration 1
  │
  ├─ Read all log lines (paginated, 600 lines/call)
  ├─ MCP filter_power_plant  → keep CRIT + WARN related to plant systems
  ├─ MCP compress_logs       → if still over budget, deduplicate
  ├─ DSPy AnalyzeLogs        → LLM makes final selection (≤ 1500 tokens)
  ├─ MCP count_tokens        → safety check, trim if needed
  ├─ POST to hub             → receive response
  ├─ DSPy EvaluateHubResponse → extract action_plan + missing_topics
  └─ ⏸  HUMAN GATE
       • Review hub response in terminal
       • Add optional notes (e.g. "hub wants more FIRMWARE context")
       • Press Y to launch Iteration 2, N to stop

Iteration 2  (hub_feedback + human_notes + previous_answer fed back in)
  └─ … same steps, LLM now aware of what the hub asked for
```

Session state is persisted in `session_history.json` after every iteration,
so you can stop and resume later.

---

## MCP tools reference

| Tool | Purpose |
|---|---|
| `read_log_file` | Paginated file reader (start_line, max_lines) |
| `filter_power_plant` | Regex filter for plant keywords + severity levels |
| `count_tokens` | cl100k_base token counter with budget check |
| `compress_logs` | Three strategies: deduplicate / top_severity / truncate |
| `get_session_history` | Load `session_history.json` for context |

---

## Adjusting the keyword list

Power-plant keywords live in `src/mcp_server.py` in the `_POWER_PLANT_PATTERNS`
regex. Add patterns there if the hub reports missing system codes.

---

## Files

```
log-analyzer/
├── pyproject.toml          # uv project + dependencies
├── .env.example            # config template
├── session_history.json    # auto-created; persists iteration state
├── failure.log             # ← YOU provide this
└── src/
    ├── __init__.py
    ├── main.py             # entry point
    ├── agent.py            # agentic loop, MCP client, human gate
    ├── signatures.py       # DSPy signatures (AnalyzeLogs, EvaluateHubResponse)
    └── mcp_server.py       # MCP server with all log-analysis tools
```
