"""
Tools for drone mission system: API interactions and utilities.
"""

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

HUB_API_KEY = os.environ["HUB_API_KEY"]
HUB_URL = os.getenv("HUB_URL", "https://hub.ag3nts.org/verify")
POWER_PLANT_CODE = os.getenv("POWER_PLANT_CODE", "PWR6132PL")


def submit_to_hub(instructions: list[str]) -> dict[str, Any]:
    """
    Submit drone instructions to the hub verify endpoint.

    Args:
        instructions: List of instruction strings for the drone

    Returns:
        API response dict (may contain {FLG:...} on success or error messages)
    """
    payload = {
        "apikey": HUB_API_KEY,
        "task": "drone",
        "answer": {"instructions": instructions},
    }
    try:
        r = requests.post(HUB_URL, json=payload, timeout=30)
        # Try to parse JSON response regardless of status code
        # The hub returns error details in the body even for 400 errors
        try:
            response_data = r.json()
        except ValueError:
            response_data = {"message": r.text}

        # Include status code info if it's an error
        if not r.ok:
            response_data["http_status"] = r.status_code
            response_data["http_error"] = f"HTTP {r.status_code}"

        return response_data
    except requests.RequestException as e:
        return {"error": str(e), "type": "request_exception"}


def hard_reset() -> dict[str, Any]:
    """
    Hard reset the drone to factory defaults.
    Useful when accumulated errors cause failures.
    """
    return submit_to_hub(["hardReset"])


def get_map_url() -> str:
    """
    Construct the map URL with API key.
    """
    return f"https://hub.ag3nts.org/data/{HUB_API_KEY}/drone.png"


def get_power_plant_code() -> str:
    """Return the power plant code."""
    return POWER_PLANT_CODE
