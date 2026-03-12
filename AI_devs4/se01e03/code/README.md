# Package Service Proxy

FastAPI proxy server with embedded MCP tools that intercepts package operations, silently redirects all packages to `PWR6132PL` for audit, and uses an LLM to communicate with operators.

## Features

- **Silent Redirect**: All package redirects are silently overridden to `PWR6132PL` for audit purposes
- **LLM Communication**: Uses OpenRouter with DeepSeek model for human-like operator interactions
- **Session Persistence**: Maintains conversation history across requests
- **MCP Tools**: Embedded Model Context Protocol tools for package operations
- **FastAPI Server**: RESTful API with proper error handling

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

Copy the environment template and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `INTERNAL_API_KEY`: Your internal API key for the package service

### 3. Start the Server

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 3000
```

The server will be available at:
- http://localhost:3000
- http://127.0.0.1:3000

## API Endpoints

### POST /operator_proxy

Main endpoint for operator interactions.

**Request:**
```json
{
  "sessionID": "your-session-id",
  "msg": "Check package PKG12345"
}
```

**Response:**
```json
{
  "msg": "I'll check the status of package PKG12345 for you..."
}
```

### GET /health

Health check endpoint.

### GET /mcp/tools

List available MCP tools (for debugging).

## Usage Examples

### Check Package Status

```bash
curl -X POST "http://localhost:3000/operator_proxy" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionID": "session1",
    "msg": "Can you check the status of package PKG12345?"
  }'
```

### Redirect Package

```bash
curl -X POST "http://localhost:3000/operator_proxy" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionID": "session1",
    "msg": "Please redirect package PKG12345 to NEWYORK with code AUTH123"
  }'
```

**Note**: The package will actually be redirected to `PWR6132PL` for audit, but the operator will be told it's going to `NEWYORK`.

## Development

### Run Tests

```bash
uv run pytest tests/test_agent.py -v
```

### Lint and Type Check

```bash
uv run ruff check src/ && uv run pyright src/
```

## Architecture

```
Operator → FastAPI (:3000) → LLM Agent → MCP Tools → External API
                ↓
          Session Store (JSON)
```

### Key Components

- **`src/main.py`**: FastAPI application with operator proxy endpoint
- **`src/agent/logic.py`**: LangChain agent with OpenRouter integration
- **`src/mcp/tools.py`**: MCP tools for package operations (check, redirect)
- **`src/storage/session.py`**: JSON-based session persistence
- **`src/config.py`**: Environment configuration management

## Security Features

- **Silent Audit Redirect**: All package redirects are overridden to `PWR6132PL`
- **No Information Leakage**: Operators never see the actual audit destination
- **Session Isolation**: Each session maintains its own message history
- **Error Handling**: All errors return friendly messages with HTTP 200

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM | Yes |
| `OPENROUTER_MODEL` | Model to use (default: deepseek/deepseek-chat) | No |
| `INTERNAL_API_KEY` | API key for package service | Yes |
| `PACKAGE_API_URL` | Package service URL | No |
| `SESSION_FILE_PATH` | Session storage file path | No |
| `HOST` | Server host (default: 0.0.0.0) | No |
| `PORT` | Server port (default: 3000) | No |

## Testing

The project includes basic tests for:

- Agent initialization and message processing
- Session management and persistence
- MCP tool functionality

Run tests with: `uv run pytest tests/ -v`

## License

Internal project - see project documentation for licensing information.
