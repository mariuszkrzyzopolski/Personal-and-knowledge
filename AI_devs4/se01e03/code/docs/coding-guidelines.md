# Coding Guidelines - Package Service Proxy

## Build, Test & Lint Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 3000

# Run tests (single test file)
uv run pytest tests/test_agent.py -v

# Run a specific test
uv run pytest tests/test_agent.py::test_function_name -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Lint with ruff
uv run ruff check src/

# Format code
uv run ruff format src/

# Type checking with pyright
uv run pyright src/

# All checks (lint + typecheck + test)
uv run ruff check src/ && uv run pyright src/ && uv run pytest tests/ -v
```

## Code Style Guidelines

### Imports
- Use absolute imports: `from src.module import something` (not `from .module`)
- Group imports: stdlib → third-party → local
- Sort imports alphabetically within groups
- Use `import httpx` not `from httpx import AsyncClient`

### Formatting
- Line length: 100 characters max
- Use 4 spaces for indentation (no tabs)
- Use trailing commas in multi-line calls
- One blank line between top-level definitions

### Types
- Use Python 3.13+ type hints on all function signatures
- Prefer `type[...]` over `Type[...]` for generics
- Use `None` instead of `Optional[None]`
- Annotate async functions with `async def` and return types

```python
# Good
async def redirect_package(package_id: str, destination: str, code: str) -> dict[str, Any]:
    ...

# Avoid
async def redirect_package(package_id, destination, code):
    ...
```

### Naming Conventions
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `SCREAMING_SNAKE_CASE`
- Private members: prefix with `_` (e.g., `_internal_method`)
- Booleans: use `is_`, `has_`, `can_` prefixes (e.g., `is_valid`, `has_session`)

### Error Handling
- Always return HTTP 200 to operators per spec
- Catch exceptions and return friendly messages: `{"msg": "There was an issue, please try again"}`
- Use try/except only when you can handle the error meaningfully
- Let FastAPI handle validation errors (HTTP 422) automatically

```python
# Good - returns friendly message to operator
try:
    response = await httpx.post(url, json=payload)
    response.raise_for_status()
except Exception:
    return {"msg": "There was an issue, please try again"}

# Avoid - don't expose internal errors
except Exception as e:
    raise HTTPException(500, detail=str(e))
```

### Async/Await
- Use `async def` for all functions that await
- Never use `asyncio.run()` in request handlers (FastAPI handles this)
- Use `httpx.AsyncClient` for HTTP calls (not `requests`)
- Avoid blocking calls in async functions

### Pydantic Models
- Use Pydantic for request/response validation
- Use `BaseModel` for internal data structures
- Define with clear field types and descriptions

```python
class OperatorRequest(BaseModel):
    sessionID: str
    msg: str
```

### File Organization
- One class per file recommended
- Keep related functions together in modules
- `__init__.py` for package markers
- Tests mirror src/ structure: `tests/test_agent.py` tests `src/agent/logic.py`

### Logging
- Use `logging.getLogger(__name__)` for module loggers
- Log at appropriate levels: DEBUG (detailed), INFO (normal), WARNING (issue), ERROR (failure)
- Don't log sensitive data (API keys, internal IDs)
