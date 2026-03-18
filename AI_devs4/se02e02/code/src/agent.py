"""
agent.py
--------
Orchestrator for the electricity puzzle agent.

Each round:
  1. Fetch current board PNG.
  2. Send current + target PNGs to vision model → get per-cell rotation counts.
  3. Execute rotations via hub API.
  4. Check every hub response for the flag.
  5. Repeat until flag received or MAX_ROUNDS exhausted.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import hub
import vision

load_dotenv()
console = Console()

MAX_ROUNDS   = int(os.environ.get("MAX_ROUNDS", "20"))
ROTATE_DELAY = float(os.environ.get("ROTATE_DELAY", "0.4"))


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _extract_flag(response: dict) -> str | None:
    text = str(response)
    start = text.find("{FLG:")
    if start != -1:
        end = text.find("}", start)
        if end != -1:
            return text[start : end + 1]
    return None


def _print_plan(plan: list[dict]) -> None:
    cells_needing_work = [p for p in plan if p["rotations"] > 0]
    if not cells_needing_work:
        console.print("[green]All cells already aligned (0 rotations needed).[/green]")
        return
    table = Table(title="Rotation Plan", show_lines=True)
    table.add_column("Cell",      style="cyan", justify="center")
    table.add_column("Rotations", justify="center")
    for p in cells_needing_work:
        table.add_row(p["cell"], str(p["rotations"]))
    console.print(table)


# ──────────────────────────────────────────────────────────────────────────────
# Main loop
# ──────────────────────────────────────────────────────────────────────────────

def run() -> None:
    console.print(Panel("[bold green]⚡ Electricity Puzzle Agent[/bold green]", expand=False))

    # Fetch target once – we keep the raw bytes and reuse every round
    console.print("\n[bold yellow]► Fetching target (solved) image …[/bold yellow]")
    target_png = hub.fetch_solved_image()
    Path("target.png").write_bytes(target_png)
    console.print("  Saved → target.png")

    for round_num in range(1, MAX_ROUNDS + 1):
        console.rule(f"[bold blue]Round {round_num} / {MAX_ROUNDS}[/bold blue]")

        # 1. Fetch current board
        console.print("[yellow]► Fetching current board …[/yellow]")
        current_png = hub.fetch_board_image()
        board_path  = f"board_round_{round_num:02d}.png"
        Path(board_path).write_bytes(current_png)
        console.print(f"  Saved → {board_path}")

        # 2. Vision: compare current vs target → rotation plan
        console.print("[yellow]► Asking vision model for rotation plan …[/yellow]")
        comparison_path = f"comparison_round_{round_num:02d}.png"
        try:
            plan = vision.diff_via_vision(
                current_png,
                target_png,
                label=f"round {round_num}",
                save_comparison=comparison_path,
            )
        except RuntimeError as exc:
            console.print(f"[red]Vision failed: {exc}[/red]")
            console.print("[yellow]Skipping round.[/yellow]")
            time.sleep(3)
            continue

        _print_plan(plan)

        cells_to_rotate = [p for p in plan if p["rotations"] > 0]

        # 3. Empty plan = vision says board is solved
        if not cells_to_rotate:
            console.print(
                "[bold green]✓ Vision model reports board matches target "
                "(0 rotations needed for all cells).[/bold green]"
            )
            console.print(
                "[yellow]If the puzzle is genuinely solved the flag should "
                "have been returned already. If not, consider resetting the "
                "board and rerunning — the vision model may be misreading the "
                "comparison.[/yellow]"
            )
            # Do NOT send any rotation — that would corrupt a solved board.
            # If we keep getting an all-zero plan without a flag, the comparison
            # image is saved so you can inspect it directly.
            time.sleep(2)
            continue

        # 4. Execute rotations
        total = sum(p["rotations"] for p in cells_to_rotate)
        console.print(
            f"\n[cyan]Sending {total} rotation request(s) "
            f"across {len(cells_to_rotate)} cell(s) …[/cyan]"
        )

        for p in cells_to_rotate:
            for i in range(p["rotations"]):
                console.print(
                    f"  → rotate {p['cell']}  ({i + 1}/{p['rotations']})"
                )
                resp = hub.rotate_cell(p["cell"])
                console.print(f"     hub: {resp}")

                flag = _extract_flag(resp)
                if flag:
                    console.print(
                        Panel(
                            f"[bold green]🏁 FLAG: {flag}[/bold green]",
                            expand=False,
                        )
                    )
                    return

                if ROTATE_DELAY > 0:
                    time.sleep(ROTATE_DELAY)

        console.print(f"[green]Round {round_num} complete.[/green]")

    # Exhausted
    console.print(
        Panel(
            f"[bold red]✗ Reached MAX_ROUNDS ({MAX_ROUNDS}) without a flag.[/bold red]\n"
            "• Inspect comparison_round_*.png to verify the model's reading.\n"
            "• Try a stronger VISION_MODEL (e.g. anthropic/claude-opus-4-5).\n"
            "• Increase MAX_ROUNDS in .env.",
            expand=False,
        )
    )
    sys.exit(1)


if __name__ == "__main__":
    run()