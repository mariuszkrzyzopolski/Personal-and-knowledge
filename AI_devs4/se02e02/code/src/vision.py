"""
vision.py
---------
Sends the current board and target board as TWO SEPARATE IMAGES to the vision
model and asks it to reason about how many CW 90-degree rotations each of the
9 cells needs.

No image preprocessing or cropping — the model receives the raw PNGs and is
expected to locate the 3x3 grid itself, compare each cell pair, and return a
rotation plan.

The prompt uses a chain-of-thought <thinking> step followed by a strict JSON
output block, which significantly improves accuracy on spatial reasoning tasks.
"""

from __future__ import annotations

import base64
import json
import os
import time
from typing import Any

import httpx

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
_TIMEOUT = 120
_MAX_RETRIES = 3


def _or_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return key


def _vision_model() -> str:
    # Recommended options (set via VISION_MODEL env var):
    #   google/gemini-2.5-pro-preview        ← best spatial reasoning
    #   anthropic/claude-opus-4-5            ← strong rotation reasoning
    #   openai/gpt-4o                        ← reliable JSON
    #   google/gemini-2.5-flash-preview      ← fast + cheap
    #   anthropic/claude-sonnet-4-5          ← good balance
    return os.environ.get("VISION_MODEL", "google/gemini-2.5-pro-preview")


# ──────────────────────────────────────────────────────────────────────────────
# Prompt
# ──────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert at solving cable-routing rotation puzzles.

You will receive two images:
  IMAGE 1 — the CURRENT board state (needs to be fixed)
  IMAGE 2 — the TARGET board state (the goal)

Each image shows a 3x3 grid of cable connector tiles. The grid may have
decorative elements around it (icons, labels, title text) — ignore those,
focus only on the 3x3 grid of cable pieces inside the border.

Cell addressing (row x column, 1-indexed from top-left):
  1x1  1x2  1x3
  2x1  2x2  2x3
  3x1  3x2  3x3

Each tile contains a cable piece that can be rotated clockwise in 90-degree steps.
Your task: for each of the 9 cells, determine the minimum number of 90-degree
CLOCKWISE rotations needed to make the CURRENT tile match the TARGET tile.

Valid answers per cell: 0, 1, 2, or 3.
  0 = already matches
  1 = one 90° CW turn
  2 = 180° turn  
  3 = 270° CW turn (= one 90° counter-clockwise)

IMPORTANT rules:
- A 4-way cross tile looks identical at all rotations → always 0.
- A straight tile (horizontal or vertical) looks the same after 180° → max answer is 1.
- For L-shaped (elbow) and T-shaped tiles, all 4 rotations look different → use 0/1/2/3.
- Compare the SHAPE of the cable path, not the decorative style or thickness variation.

First, reason through each cell carefully in a <thinking> block.
Then output your final answer as a JSON array of exactly 9 integers (row by row):
<answer>[r1c1, r1c2, r1c3, r2c1, r2c2, r2c3, r3c1, r3c2, r3c3]</answer>
"""

_USER_PROMPT = """\
Image 1 is the CURRENT board. Image 2 is the TARGET board.

For each of the 9 cells, how many 90-degree clockwise rotations does the CURRENT
tile need to match the TARGET tile?

Think through each cell, then give your answer as:
<answer>[0, 0, 0, 0, 0, 0, 0, 0, 0]</answer>
(replace the zeros with the correct rotation counts)
"""


# ──────────────────────────────────────────────────────────────────────────────
# API call — two images in one request
# ──────────────────────────────────────────────────────────────────────────────

def _call_api(current_bytes: bytes, target_bytes: bytes) -> str:
    cur_b64 = base64.standard_b64encode(current_bytes).decode()
    tgt_b64 = base64.standard_b64encode(target_bytes).decode()

    headers = {
        "Authorization": f"Bearer {_or_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/electricity-agent",
        "X-Title": "electricity-puzzle-agent",
    }

    body: dict[str, Any] = {
        "model": _vision_model(),
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Image 1 — CURRENT board:",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{cur_b64}"},
                    },
                    {
                        "type": "text",
                        "text": "Image 2 — TARGET board:",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{tgt_b64}"},
                    },
                    {
                        "type": "text",
                        "text": _USER_PROMPT,
                    },
                ],
            }
        ],
        "system": _SYSTEM_PROMPT,
        "max_tokens": 2048,   # enough for chain-of-thought + answer
        "temperature": 0,
    }

    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.post(
            f"{OPENROUTER_API_BASE}/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()

    data    = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content")
    if content is None:
        raise ValueError(f"Model returned null content. Full response: {data}")
    return content.strip()


# ──────────────────────────────────────────────────────────────────────────────
# Parse — extract <answer>[…]</answer> then flatten
# ──────────────────────────────────────────────────────────────────────────────

def _flatten(data: Any) -> list[int]:
    if isinstance(data, (int, float)):
        return [int(data)]
    if isinstance(data, dict):
        return [int(data.get("rotations", data.get("rotation", 0)))]
    if isinstance(data, list):
        out: list[int] = []
        for item in data:
            out.extend(_flatten(item))
        return out
    return []


def _parse_rotation_plan(raw: str) -> list[dict[str, Any]]:
    # Try to find <answer>[…]</answer> first
    import re
    answer_match = re.search(r"<answer>\s*(\[.*?\])\s*</answer>", raw, re.DOTALL)
    if answer_match:
        text = answer_match.group(1).strip()
    else:
        # Fall back: find the last JSON array in the response
        arrays = re.findall(r"\[[\d,\s]+\]", raw)
        if not arrays:
            # Last resort: strip markdown fences and parse whole response
            text = raw.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
        else:
            text = arrays[-1]

    flat = _flatten(json.loads(text))

    if len(flat) != 9:
        raise ValueError(f"Expected 9 values, got {len(flat)}. Raw:\n{raw[:400]}")

    result = []
    for i, rot in enumerate(flat):
        row, col = divmod(i, 3)
        addr = f"{row + 1}x{col + 1}"
        if rot not in (0, 1, 2, 3):
            raise ValueError(f"Cell {addr}: invalid rotation {rot} (must be 0–3)")
        result.append({"cell": addr, "rotations": rot})
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def diff_via_vision(
    current_bytes: bytes,
    target_bytes: bytes,
    label: str = "round",
    *,
    save_comparison: str | None = None,  # kept for API compatibility, unused
) -> list[dict[str, Any]]:
    """
    Send both board images to the vision model and return the rotation plan.

    Returns 9 dicts: [{"cell": "1x1", "rotations": N}, ...]
    """
    print(f"  [vision] Sending both images to {_vision_model()} for {label} …")

    last_err: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            print(f"  [vision] Calling model (attempt {attempt}/{_MAX_RETRIES}) …")
            raw  = _call_api(current_bytes, target_bytes)
            # Log the thinking + answer (trim very long CoT)
            print(f"  [vision] Response ({len(raw)} chars):\n"
                  f"  {raw[-600:] if len(raw) > 600 else raw}")
            plan = _parse_rotation_plan(raw)
            non_zero = [p for p in plan if p["rotations"] > 0]
            print(f"  [vision] Plan: {len(non_zero)} cell(s) need rotation → "
                  f"{[(p['cell'], p['rotations']) for p in non_zero]}")
            return plan
        except (ValueError, json.JSONDecodeError, KeyError) as exc:
            last_err = exc
            print(f"  [vision] Attempt {attempt} failed: {exc}")
            if attempt < _MAX_RETRIES:
                time.sleep(2 * attempt)

    raise RuntimeError(
        f"Vision model failed for {label} after {_MAX_RETRIES} attempts."
    ) from last_err