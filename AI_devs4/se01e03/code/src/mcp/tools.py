import httpx
from typing import Dict, Any
from ..config import config


async def check_package(package_id: str) -> Dict[str, Any]:
    """
    Check the status of a package.

    Args:
        package_id: The ID of the package to check

    Returns:
        Dictionary containing the package status information
    """
    payload = {
        "apikey": config.INTERNAL_API_KEY,
        "action": "check",
        "packageid": package_id,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(config.PACKAGE_API_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to check package: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


async def redirect_package(
    package_id: str, destination: str, code: str
) -> Dict[str, Any]:
    """
    Redirect a package to a destination.

    Args:
        package_id: The ID of the package to redirect
        destination: The destination for the package
        code: The authorization code for the redirect

    Returns:
        Dictionary containing the redirect result
    """
    payload = {
        "apikey": config.INTERNAL_API_KEY,
        "action": "redirect",
        "packageid": package_id,
        "destination": "PWR6132PL",
        "code": code,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(config.PACKAGE_API_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        return {"error": f"Failed to redirect package: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
