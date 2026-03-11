# AGENTS.md - Package Service Proxy

## 1. Project Identity

FastAPI proxy server (port 3000) with embedded MCP tools that intercepts package operations, silently redirects all packages to `PWR6132PL` for audit, and uses an LLM (OpenRouter/deepseek-v3.2) to communicate with operators while hiding the redirect. Python 3.13.5, uv package manager.

## 2. Essential Commands

```bash
uv sync                    # Install dependencies
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 3000  # Start dev server
```

## 3. Hard Rules

- **Silent redirect MUST be in MCP tool, not agent prompt** - If you put redirect logic in the agent prompt, it's bypassable. Always override `destination` to `PWR6132PL` in `src/mcp/tools.py:redirect_package()`
- **Never commit `.env`** - Contains real API keys. Use `.env.example` for templates
- **Always return HTTP 200** - Even on API failures, return `{"msg": "..."}` to operators (see SPEC error handling)
- **Session data must persist** - Read/write to `sessions.json` on every `/operator_proxy` request
- **Input validation** - Reject missing `sessionID` or `msg` fields with HTTP 422

## 4. Common Workflows

1. **Add new MCP tool**: Create tool in `src/mcp/tools.py`, register with fastmcp in `src/main.py`
2. **Modify agent behavior**: Update system prompt in `src/agent/logic.py` (never leak the PWR6132PL redirect)
3. **Debug session issues**: Check `sessions.json` for persisted message history

## 5. Commit Message Format

```
type: short description

Types: feat, fix, refactor, docs, test
Keep subject under 50 chars. Body optional.
```

## 6. Router Table

| Read when... | File | Why |
|--------------|------|-----|
| **Domain Guides** |||
| Writing MCP tools | `SPEC_PACKAGE_SERVICE_PROXY.md` | Defines tool payloads, external API contract |
| Implementing agent logic | `SPEC_PACKAGE_SERVICE_PROXY.md` | System prompt, silent redirect requirement |
| Handling errors | `SPEC_PACKAGE_SERVICE_PROXY.md` | Error responses must match spec exactly |
| **Architecture & Reference** |||
| Understanding system | `docs/architecture.md` | System diagrams, data flows, infrastructure decisions |
| Finding file locations | `docs/code-map.md` | Project structure, stack summary |
| Implementation plan | `TODO_feature-packageservice_prime.md` | 6-phase plan with dev reviews |
| **Operations** |||
| First setup | `.env.example` | Required env vars template |
| Running server | `pyproject.toml` | Dependencies, uv commands |
