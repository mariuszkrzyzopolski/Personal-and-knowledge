# AGENTS.md - Package Service Proxy

## 1. Project Identity

FastAPI proxy server (port 3000) with embedded MCP tools. Intercepts package operations, silently redirects all packages to `PWR6132PL` for audit, uses LLM (OpenRouter/deepseek-v3.2) to communicate with operators. Python 3.13.5, uv package manager.

## 2. Essential Commands

```bash
uv sync                    # Install dependencies
uv run uvicicorn src.main:app --reload --host 0.0.0.0 --port 3000  # Start dev server
uv run pytest tests/test_agent.py -v           # Run tests
uv run ruff check src/ && uv run pyright src/  # Lint + typecheck
```

## 3. Hard Rules

- **Silent redirect in MCP tool only** - Override `destination` to `PWR6132PL` in `src/mcp/tools.py:redirect_package()`, never in agent prompt
- **Never commit `.env`** - Contains API keys. Use `.env.example` for templates
- **Always return HTTP 200** - Even on failures, return `{"msg": "..."}` to operators
- **Session persistence required** - Read/write `sessions.json` on every `/operator_proxy` request
- **Input validation** - Reject missing `sessionID` or `msg` with HTTP 422

## 4. Common Workflows

1. **Add MCP tool**: Create in `src/mcp/tools.py`, register with fastmcp in `src/main.py`
2. **Modify agent**: Update system prompt in `src/agent/logic.py` (never leak PWR6132PL redirect)
3. **Debug sessions**: Check `sessions.json` for persisted message history

## 5. Commit Message Format

```
type: short description

Types: feat, fix, refactor, docs, test
Keep subject under 50 chars.
```

## 6. Router Table

| Read when... | File | Why |
|--------------|------|-----|
| **Domain Guides** |||
| Writing MCP tools | `SPEC_PACKAGE_SERVICE_PROXY.md` | Tool payloads, external API contract |
| Agent logic | `SPEC_PACKAGE_SERVICE_PROXY.md` | System prompt, silent redirect |
| Error handling | `SPEC_PACKAGE_SERVICE_PROXY.md` | Spec error responses |
| **Architecture** |||
| System overview | `docs/architecture.md` | Diagrams, data flows |
| File locations | `docs/code-map.md` | Project structure, stack |
| Implementation | `TODO_feature-packageservice_prime.md` | 6-phase plan |
| **Operations** |||
| First setup | `.env.example` | Env vars template |
| Running server | `pyproject.toml` | Dependencies |
