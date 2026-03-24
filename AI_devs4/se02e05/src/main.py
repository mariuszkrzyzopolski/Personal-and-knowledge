"""
Drone Mission System - Two-agent pipeline for analyzing map and executing mission.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from rich.console import Console

from .agents import FlightPlannerAgent, VisionAgent
from .tools import get_power_plant_code

load_dotenv()

console = Console()


def main() -> None:
    """Execute the two-agent drone mission pipeline."""
    console.print("[bold cyan]╔══════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║    DRONE MISSION SYSTEM - SE02E05    ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════╝[/bold cyan]")
    console.print()

    # Verify environment
    required_vars = ["OPENROUTER_API_KEY", "HUB_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        console.print(f"[red]Missing required environment variables: {', '.join(missing)}[/red]")
        console.print("[dim]Please set these in your .env file or environment.[/dim]")
        return

    # Phase 1: Vision Agent - Analyze map
    console.print("[bold yellow]Phase 1: Vision Analysis[/bold yellow]")
    console.print("─" * 40)

    vision_agent = VisionAgent()
    map_analysis = vision_agent.analyze_map()

    # Extract coordinates
    dam_column = map_analysis["dam_column"]
    dam_row = map_analysis["dam_row"]

    console.print()

    # Phase 2: Flight Planner Agent - Execute mission
    console.print("[bold yellow]Phase 2: Mission Execution[/bold yellow]")
    console.print("─" * 40)

    power_plant_code = get_power_plant_code()
    flight_agent = FlightPlannerAgent()
    result = flight_agent.execute_mission(dam_column, dam_row, power_plant_code)

    console.print()
    console.print("[bold cyan]══════════════════════════════════════════[/bold cyan]")
    console.print(f"[bold]Mission Complete:[/bold] {result}")
    console.print("[bold cyan]══════════════════════════════════════════[/bold cyan]")


if __name__ == "__main__":
    main()
