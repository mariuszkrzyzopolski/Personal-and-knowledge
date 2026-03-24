"""
DSPy signatures for the two-agent drone mission system.
"""

import dspy


class VisionAnalyzer(dspy.Signature):
    """
    You are a precision map analyst with vision capabilities.

    Your task is to analyze a terrain map image and identify:
    1. The total number of grid columns
    2. The total number of grid rows
    3. The exact sector (column, row) containing the DAM

    Critical rules:
    - Grid coordinates use 1-based indexing (top-left is 1,1)
    - Map is divided into a grid of columns and rows 3x4
    - The dam is marked with enhanced blue water color intensity, on the bottom of the map
    - The dam is the water barrier structure, not the main building complex

    Output the dam's location as exact grid coordinates.
    """

    image_url: str = dspy.InputField(desc="URL of the terrain map image with grid overlay")
    power_plant_code: str = dspy.InputField(desc="Code of the target power plant (for reference only, not the actual target)")

    grid_columns: int = dspy.OutputField(desc="Total number of columns in the grid")
    grid_rows: int = dspy.OutputField(desc="Total number of rows in the grid")
    dam_column: int = dspy.OutputField(desc="Column coordinate of the DAM sector (1-indexed)")
    dam_row: int = dspy.OutputField(desc="Row coordinate of the DAM sector (1-indexed)")
    reasoning: str = dspy.OutputField(desc="Explanation of how you identified the grid dimensions and dam location")


class FlightPlanner(dspy.Signature):
    """
    You are a drone mission programmer for the DRN-BMB7 drone system.

    Your task is to generate the exact sequence of instructions to bomb the dam

    Mission objective: Destroy the dam to flood the cooling system.
    Target object: The power plant (PWR6132PL) - BUT landing sector must be the dam.

    Required instruction sequence based on API documentation:

    1. Set destination object: setDestinationObject(PWR6132PL)
    2. Set landing sector to dam coordinates: set({dam_column-1},{dam_row-1})
    3. Enable engines: set(engineON)
    4. Set engine power to maximum: set(100%)
    5. Set flight altitude: set(50m) [or any value 1m-100m]
    6. Set mission objective to destroy: set(destroy)
    7. Set return to base: set(return)
    8. Execute flight: flyToLocation

    Rules:
    - Use exactly the format shown in the examples
    - Parameters must match the required patterns
    - Instructions must be in logical execution order
    """

    initial_dam_column: int = dspy.InputField(desc="Initial column coordinate of the dam from vision analysis (1-indexed)")
    initial_dam_row: int = dspy.InputField(desc="Initial row coordinate of the dam from vision analysis (1-indexed)")
    power_plant_code: str = dspy.InputField(desc="Power plant code for setDestinationObject")
    error_feedback: str = dspy.InputField(desc="Error feedback from previous attempt (if any). Use this to correct coordinates and instructions.", default="")
    attempt_history: str = dspy.InputField(desc="History of previous attempts as 'Attempt N: coordinates (col,row) -> result' format. Use this to avoid repeating failed coordinates.", default="")

    dam_column: int = dspy.OutputField(desc="Corrected column coordinate to use in set() command (1-indexed). Adjust based on error feedback and attempt history - NEVER repeat coordinates from failed attempts.")
    dam_row: int = dspy.OutputField(desc="Corrected row coordinate to use in set() command (1-indexed). Adjust based on error feedback and attempt history - NEVER repeat coordinates from failed attempts.")

    instruction_list: str = dspy.OutputField(desc="Instructions as newline-separated strings, one instruction per line. Example: setDestinationObject(PWR6132PL)\\nset(5,3)\\nset(engineON)\\nflyToLocation")
    reasoning: str = dspy.OutputField(desc="Explanation of instruction choices")
