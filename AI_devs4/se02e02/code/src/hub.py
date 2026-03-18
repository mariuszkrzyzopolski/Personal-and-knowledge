"""
hub.py
------
Low-level client for hub.ag3nts.org:
  • fetch_board_image()   → raw PNG bytes (current state)
  • fetch_solved_image()  → raw PNG bytes (target state)
  • reset_board()         → resets the puzzle
  • rotate_cell()         → sends one rotation, returns hub JSON response
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

HUB_BASE = "https://hub.ag3nts.org"
_TIMEOUT = 30


def _api_key() -> str:
    key = os.environ.get("PUZZLE_API_KEY", "")
    if not key:
        raise RuntimeError("PUZZLE_API_KEY is not set in environment / .env")
    return key


def fetch_board_image(reset: bool = False) -> bytes:
    """Return the current puzzle board PNG as raw bytes."""
    key = _api_key()
    url = f"{HUB_BASE}/data/{key}/electricity.png"
    params = {"reset": "1"} if reset else {}
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
    return r.content


def fetch_solved_image() -> bytes:
    """Return the target / solved puzzle PNG as raw bytes."""
    url = f"{HUB_BASE}/i/solved_electricity.png"
    with httpx.Client(timeout=_TIMEOUT) as client:
        r = client.get(url)
        r.raise_for_status()
    return r.content


def reset_board() -> bytes:
    """Reset the board and return fresh PNG bytes."""
    return fetch_board_image(reset=True)


def rotate_cell(cell: str, *, retries: int = 3, backoff: float = 2.0) -> dict[str, Any]:
    """
    POST a single rotation command to the hub.

    Parameters
    ----------
    cell : str
        Address in "RowxCol" format, e.g. "2x3".

    Returns
    -------
    dict
        Parsed JSON response from the hub.
        If the puzzle is solved the response will contain a key whose value
        starts with ``{FLG:``.
    """
    key = _api_key()
    payload = {"apikey": key, "task": "electricity", "answer": {"rotate": cell}}

    for attempt in range(1, retries + 1):
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                r = client.post(f"{HUB_BASE}/verify", json=payload)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as exc:
            if attempt == retries:
                raise
            time.sleep(backoff * attempt)
        except httpx.RequestError as exc:
            if attempt == retries:
                raise
            time.sleep(backoff * attempt)

    return {}  # unreachable, keeps type-checker happy
