"""
board.py
--------
Pure-logic helpers for the cable-rotation puzzle.

Key concepts
────────────
A cell's state is fully described by its set of exits, e.g. {"E", "S"}.
Rotating a cell 90° clockwise maps  N→E, E→S, S→W, W→N.

`diff_boards(current, target)` returns, for every cell that differs,
the minimum number of clockwise 90° rotations (1-3) needed to align it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Rotation helpers
# ──────────────────────────────────────────────────────────────────────────────

_CW_MAP = {"N": "E", "E": "S", "S": "W", "W": "N"}


def rotate_exits_cw(exits: frozenset[str]) -> frozenset[str]:
    """Rotate a set of exits 90° clockwise once."""
    return frozenset(_CW_MAP[d] for d in exits)


def rotations_needed(current_exits: frozenset[str], target_exits: frozenset[str]) -> int:
    """
    Return the *minimum* number of 90° clockwise rotations (0-3) to turn
    *current_exits* into *target_exits*.

    Raises ValueError if no rotation achieves the target (shape mismatch).
    """
    state = current_exits
    for n in range(4):
        if state == target_exits:
            return n
        state = rotate_exits_cw(state)
    raise ValueError(
        f"Cannot reach {sorted(target_exits)} from {sorted(current_exits)} "
        "by rotation – shapes differ."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Board diffing
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CellPlan:
    cell: str            # e.g. "2x3"
    rotations: int       # 1, 2, or 3
    current_exits: list[str]
    target_exits: list[str]


def diff_boards(
    current: list[dict[str, Any]],
    target: list[dict[str, Any]],
) -> list[CellPlan]:
    """
    Compare two 9-cell board descriptions and return the rotation plan.

    Parameters
    ----------
    current, target : list[dict]
        Each list must have 9 dicts with keys "cell", "shape", "exits".
        The lists are matched by cell address.

    Returns
    -------
    list[CellPlan]
        Only cells that need at least one rotation, sorted by cell address.
    """
    # Index both lists by cell address
    cur_map = {c["cell"]: c for c in current}
    tgt_map = {c["cell"]: c for c in target}

    plan: list[CellPlan] = []

    for cell_addr in sorted(cur_map.keys()):
        c_exits = frozenset(cur_map[cell_addr].get("exits", []))
        t_exits = frozenset(tgt_map[cell_addr].get("exits", []))

        if c_exits == t_exits:
            continue  # already aligned

        try:
            n = rotations_needed(c_exits, t_exits)
        except ValueError:
            # Shape mismatch – log a warning but include with best-effort guess
            # (caller should log / handle this)
            n = _best_effort_rotations(c_exits, t_exits)

        if n > 0:
            plan.append(
                CellPlan(
                    cell=cell_addr,
                    rotations=n,
                    current_exits=sorted(c_exits),
                    target_exits=sorted(t_exits),
                )
            )

    return plan


def _best_effort_rotations(current: frozenset[str], target: frozenset[str]) -> int:
    """
    When shapes genuinely differ (vision error), find which single rotation
    brings the exit *count* closest to the target.  Returns 0 if unsure.
    """
    best_n, best_overlap = 0, -1
    state = current
    for n in range(4):
        overlap = len(state & target)
        if overlap > best_overlap:
            best_overlap, best_n = overlap, n
        state = rotate_exits_cw(state)
    return best_n


# ──────────────────────────────────────────────────────────────────────────────
# Pretty printing
# ──────────────────────────────────────────────────────────────────────────────

def format_board(cells: list[dict[str, Any]]) -> str:
    """Return a compact text representation of a board state."""
    lines = []
    for i, c in enumerate(cells):
        # Derive address from index if the model omitted the 'cell' key
        row, col = divmod(i, 3)
        fallback_addr = f"{row + 1}x{col + 1}"
        addr = c.get("cell") or fallback_addr
        exits_str = "".join(sorted(c.get("exits", [])))
        label = f"{addr}  {c.get('shape', '?'):9s}  [{exits_str}]"
        lines.append(label)
        if (i + 1) % 3 == 0 and i < 8:
            lines.append("─" * 35)
    return "\n".join(lines)