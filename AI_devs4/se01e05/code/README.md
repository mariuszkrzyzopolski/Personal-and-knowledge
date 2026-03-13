# HITL API Exploration Agent

A Human-in-the-Loop (HITL) agent for exploring APIs with automatic retry logic, rate limiting, and intelligent path discovery using OpenRouter.

## Features

- **Per-route HITL checkpoints**: Human approval required before and after each route exploration
- **Auto-accept tracking**: Routes can be marked for automatic execution
- **503 error handling**: Exponential backoff with configurable retries
- **Rate limiting**: Automatic parsing of `Retry-After` and `X-RateLimit-Reset` headers
- **Dynamic action discovery**: Periodically calls `help` endpoint to discover new API paths
- **OpenRouter integration**: Uses LLM to generate intelligent exploration plans
- **State persistence**: Resume exploration from where you left off
- **Flag detection**: Automatically extracts `{FLG:...}` patterns from responses

## Setup

1. Install [uv](https://github.com/astral-sh/uv) if not already installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
API_KEY=your-hub-ag3nts-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
```

3. (Optional) Modify `config.yaml` to adjust settings:
- API endpoint configuration
- OpenRouter model selection
- Retry and rate limiting parameters
- HITL behavior

## Usage

Run the agent:
```bash
source .venv/bin/activate
python main.py
```

## HITL Interaction

During exploration, you'll be prompted at key points:

**Before route execution:**
```
[PLAN] Route: a-1
[PLAN] Reasoning: Exploring route to find flags
[PLAN] Actions:
  1. reconfigure: {'route': 'a-1'}
  2. setstatus: {'route': 'a-1', 'value': 'RTOPEN'}
  3. save: {'route': 'a-1'}
Execute? (y/n/auto/steer):
```

Options:
- `y`: Execute the plan
- `n`: Skip this route
- `auto`: Auto-approve all future executions for this route
- `steer`: Provide steering instruction for the next plan

**After route completion:**
```
[COMPLETE] Route a-1 finished
[COMPLETE] Flags found in this route: []
[COMPLETE] Total flags found: 0
Continue to next route? (y/n):
```

## State Persistence

Exploration state is saved to `exploration_state.json`:
- Auto-accepted routes
- Visited routes
- Found flags
- Discovered actions
- Rate limit information

Resume exploration anytime - the agent will pick up where it left off.

## Configuration

Key settings in `config.yaml`:

```yaml
agent:
  max_retries: 5              # Max retry attempts for failed calls
  retry_delay_base: 1        # Base delay for exponential backoff
  hitl_default: true         # Require HITL for all routes by default
  state_file: "exploration_state.json"
  help_refresh_interval: 10  # Call help() every N actions

rate_limit:
  default_wait: 2            # Default wait between calls (seconds)
  max_wait: 60              # Maximum wait time (seconds)
```

## Architecture

```
api_client.py       - HTTP client with retry and rate limiting
state_manager.py    - State persistence and management
hitl_agent.py       - Main agent loop with HITL and OpenRouter
main.py             - Entry point
config.yaml         - Configuration
```

## API Format

The agent expects APIs following this structure:
```json
{
  "apikey": "your-key",
  "task": "railway",
  "answer": {
    "action": "help"
  }
}
```

POST to endpoint configured in `config.yaml`.
