# ⚡ Electricity Puzzle Agent

An autonomous agent that solves the `electricity` cable-rotation puzzle on
**hub.ag3nts.org** using a vision model via **OpenRouter**.

---

## How it works

```
fetch target PNG  ──► vision model ──► target board state
                                              │
   ┌──────────────────────────────────────────┘
   │
   ▼
fetch current PNG ──► vision model ──► current board state
                                              │
                                         diff boards
                                              │
                                    compute rotations (min CW turns)
                                              │
                                    POST /verify for each rotation
                                              │
                                      flag found? → done
                                              │
                                       (loop back)
```

The agent is **self-correcting**: after each round it re-fetches the board
and re-analyses it, so vision errors in an earlier round are automatically
corrected.

---

## Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed (`pip install uv` or `curl -Lsf https://astral.sh/uv/install.sh | sh`)
- Python 3.11+
- An [OpenRouter](https://openrouter.ai) API key
- Your `hub.ag3nts.org` puzzle API key

### Install

```bash
git clone <this-repo>
cd electricity-agent
uv sync
```

### Configure

```bash
cp .env.example .env
# Edit .env and fill in OPENROUTER_API_KEY and PUZZLE_API_KEY
```

```dotenv
OPENROUTER_API_KEY=sk-or-v1-...
PUZZLE_API_KEY=your-hub-key-here
VISION_MODEL=google/gemini-2.5-pro-exp-03-25   # or any OpenRouter vision model
MAX_ROUNDS=20
```

---

## Usage

```bash
# Run the agent
uv run agent.py

# Reset the puzzle first, then run
python -c "import hub; hub.reset_board()" && uv run agent.py
```

The agent will:
1. Analyse the target (solved) board image once.
2. In each round, fetch + analyse the current board, compute the minimum
   rotations needed, and send them to the hub.
3. Print the flag `{FLG:...}` when the hub confirms the puzzle is solved.

---

## File layout

| File | Purpose |
|------|---------|
| `agent.py` | Main orchestrator loop |
| `vision.py` | OpenRouter vision model calls |
| `board.py` | Rotation math & board diffing |
| `hub.py` | HTTP client for hub.ag3nts.org |
| `pyproject.toml` | uv / hatchling project config |
| `.env.example` | Environment variable template |

---

## Choosing a vision model

Any model on OpenRouter that supports image input works.  Recommended choices:

| Model | Notes |
|-------|-------|
| `google/gemini-2.5-pro-exp-03-25` | Best accuracy, free tier available |
| `google/gemini-2.0-flash-exp:free` | Fast & free |
| `anthropic/claude-3.5-sonnet` | High accuracy, paid |
| `openai/gpt-4o` | Strong baseline |

Set via `VISION_MODEL` in `.env`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Vision model returns wrong exits | Try a stronger model (`claude-3.5-sonnet`, `gpt-4o`) |
| `ValueError: Cannot reach … by rotation` | Shape mismatch in vision output; agent will auto-retry next round |
| Hub always returns "wrong" | Reset the board (`?reset=1`) and restart |
| `MAX_ROUNDS exceeded` | Increase `MAX_ROUNDS` in `.env`; check saved PNG files for clues |
