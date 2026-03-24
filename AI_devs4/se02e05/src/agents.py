"""
Agent implementations for the drone mission system.
"""

from __future__ import annotations

import os

import dspy
from dotenv import load_dotenv
from rich.console import Console

from .signatures import FlightPlanner, VisionAnalyzer
from .tools import get_map_url, get_power_plant_code, hard_reset, submit_to_hub

load_dotenv()

VISION_MODEL = os.getenv("VISION_MODEL", "openai/gpt-4o")
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
MAX_RETRIES = 5

console = Console()


class VisionAgent:
    """
    Agent that analyzes the terrain map to locate the dam.
    Uses a vision-capable model to count grid columns/rows and identify dam sector.
    """

    def __init__(self) -> None:
        self.lm = dspy.LM(
            model=VISION_MODEL,
            api_key=OPENROUTER_API_KEY,
            api_base="https://openrouter.ai/api/v1",
        )
        dspy.configure(lm=self.lm)
        self.analyzer = dspy.Predict(VisionAnalyzer)

    def analyze_map(self) -> dict:
        """
        Analyze the drone map image and return dam location coordinates.

        Returns:
            Dict with grid_columns, grid_rows, dam_column, dam_row, reasoning
        """
        image_url = get_map_url()
        power_plant_code = get_power_plant_code()

        console.print(f"[blue]VisionAgent:[/blue] Analyzing map at {image_url}")

        result = self.analyzer(
            image_url=image_url,
            power_plant_code=power_plant_code,
        )

        console.print(f"[green]VisionAgent:[/green] Found dam at sector ({result.dam_column}, {result.dam_row})")
        console.print(f"[dim]Grid size: {result.grid_columns} x {result.grid_rows}[/dim]")
        console.print(f"[dim]Reasoning: {result.reasoning}[/dim]")

        return {
            "grid_columns": result.grid_columns,
            "grid_rows": result.grid_rows,
            "dam_column": result.dam_column,
            "dam_row": result.dam_row,
            "reasoning": result.reasoning,
        }


class FlightPlannerAgent:
    """
    Agent that generates drone flight instructions and executes the mission.
    Uses iterative feedback from the hub API to correct errors.
    """

    def __init__(self) -> None:
        self.lm = dspy.LM(
            model=PLANNER_MODEL,
            api_key=OPENROUTER_API_KEY,
            api_base="https://openrouter.ai/api/v1",
        )
        dspy.configure(lm=self.lm)
        self.planner = dspy.Predict(FlightPlanner)

    def generate_instructions(
        self, dam_column: int, dam_row: int, power_plant_code: str, attempt_history: str = ""
    ) -> tuple[list[str], int, int]:
        """Generate the instruction sequence for the drone mission."""
        result = self.planner(
            initial_dam_column=dam_column,
            initial_dam_row=dam_row,
            power_plant_code=power_plant_code,
            error_feedback="",
            attempt_history=attempt_history,
        )
        # Use corrected coordinates from the planner output
        actual_column = result.dam_column
        actual_row = result.dam_row
        # Parse the instruction_list string into a list
        instructions_str = result.instruction_list
        # Split by newlines and filter out empty lines
        instructions = [instr.strip() for instr in instructions_str.split('\n') if instr.strip()]
        return instructions, actual_column, actual_row

    def execute_mission(
        self, dam_column: int, dam_row: int, power_plant_code: str
    ) -> dict:
        """
        Execute the drone mission with retry logic based on API feedback.

        Args:
            dam_column: Column coordinate of the dam
            dam_row: Row coordinate of the dam
            power_plant_code: Power plant object code

        Returns:
            Final API response (should contain {FLG:...} on success)
        """
        console.print(f"\n[blue]FlightPlannerAgent:[/blue] Planning mission to dam at ({dam_column}, {dam_row})")

        # Track attempt history to avoid repeating failed coordinates
        attempt_history = []
        instructions, actual_column, actual_row = self.generate_instructions(
            dam_column, dam_row, power_plant_code
        )
        console.print(f"[dim]Generated instructions:[/dim]")
        for i, instr in enumerate(instructions, 1):
            console.print(f"  {i}. {instr}")

        for attempt in range(MAX_RETRIES):
            console.print(f"\n[cyan]Attempt {attempt + 1}/{MAX_RETRIES}:[/cyan] Submitting to hub...")

            response = submit_to_hub(instructions)
            console.print(f"[dim]Response: {response}[/dim]")

            # Check for success flag
            response_str = str(response)
            if "{FLG:" in response_str or "FLG:" in response_str:
                console.print(f"[green bold]Success! Flag received:[/green bold] {response}")
                return response

            # Check for errors and adjust if needed
            is_error = (
                "error" in response
                or "Error" in response_str
                or ("code" in response and isinstance(response.get("code"), int) and response.get("code") < 0)
                or ("http_status" in response and response.get("http_status") >= 400)
            )
            if is_error:
                console.print(f"[red]Error detected:[/red] {response}")

                if attempt < MAX_RETRIES - 1:
                    console.print("[yellow]Adjusting instructions based on error feedback...[/yellow]")
                    # Record this failed attempt in history
                    attempt_history.append(
                        f"Attempt {attempt + 1}: coordinates ({actual_column},{actual_row}) -> FAILED: {response}"
                    )
                    # Re-generate with error context and full history
                    history_str = "\n".join(attempt_history)
                    error_context = f"Previous attempt failed with: {response}. Generate corrected instructions. DO NOT use coordinates from failed attempts in history."
                    instructions = self._regenerate_with_context(
                        dam_column, dam_row, power_plant_code, error_context, history_str
                    )
                    # Update coordinates from regenerated result
                    actual_column = instructions['dam_column']
                    actual_row = instructions['dam_row']
                    instructions = instructions['instructions']
                    console.print(f"[dim]New instructions:[/dim]")
                    for i, instr in enumerate(instructions, 1):
                        console.print(f"  {i}. {instr}")

                    # Hard reset if things got messy
                    if attempt == 1:
                        console.print("[yellow]Performing hard reset...[/yellow]")
                        hard_reset()
            else:
                # No error but also no flag - might need adjustment
                console.print(f"[yellow]No error but no flag either. Response: {response}[/yellow]")
                if attempt < MAX_RETRIES - 1:
                    attempt_history.append(
                        f"Attempt {attempt + 1}: coordinates ({actual_column},{actual_row}) -> UNCLEAR: {response}"
                    )
                    history_str = "\n".join(attempt_history)
                    instructions = self._regenerate_with_context(
                        dam_column, dam_row, power_plant_code,
                        f"Response was: {response}. Ensure all required setup steps are included.",
                        history_str
                    )
                    actual_column = instructions['dam_column']
                    actual_row = instructions['dam_row']
                    instructions = instructions['instructions']

        console.print(f"[red]Max retries reached. Final response: {response}[/red]")
        return response

    def _regenerate_with_context(
        self, dam_column: int, dam_row: int, power_plant_code: str, context: str, attempt_history: str = ""
    ) -> dict:
        """Regenerate instructions with additional error context and attempt history."""
        # Use ChainOfThought for better reasoning with error context
        cot_planner = dspy.ChainOfThought(FlightPlanner)
        result = cot_planner(
            initial_dam_column=dam_column,
            initial_dam_row=dam_row,
            power_plant_code=power_plant_code,
            error_feedback=context,
            attempt_history=attempt_history,
        )
        # Parse the instruction_list string into a list
        instructions_str = result.instruction_list
        # Split by newlines and filter out empty lines
        instructions = [instr.strip() for instr in instructions_str.split('\n') if instr.strip()]
        return {
            'dam_column': result.dam_column,
            'dam_row': result.dam_row,
            'instructions': instructions,
        }
