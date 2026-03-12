import os
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import yaml

from mcp_server.server import SPKMCPServer


app = FastAPI(title="SPK Package Automation API")
mcp_server = SPKMCPServer()

API_KEY = os.getenv("SPK_API_KEY", "tutaj-twój-klucz")
TASK_NAME = "sendit"


class PackageRequest(BaseModel):
    sender_id: str = Field(..., pattern=r"^\d{9}$")
    origin: str
    destination: str
    weight_kg: float = Field(..., gt=0.0, le=4000.0)
    category: str = Field(..., pattern=r"^[A-E]$")
    content: str = Field(..., max_length=200)
    special_notes: str = "brak"
    budget_pp: float = 0.0


class ProcessResponse(BaseModel):
    apikey: str
    task: str
    answer: dict


@app.get("/")
async def root():
    return {"message": "SPK Package Automation API", "version": "1.0.0"}


@app.get("/tools")
async def list_tools():
    return {"tools": mcp_server.list_tools()}


@app.post("/process-package", response_model=ProcessResponse)
async def process_package(request: PackageRequest):
    try:
        route_result = await mcp_server.handle_call_tool(
            "route_finder",
            {
                "origin": request.origin,
                "destination": request.destination,
                "category": request.category,
            },
        )

        fee_result = await mcp_server.handle_call_tool(
            "fee_calculator",
            {
                "category": request.category,
                "weight_kg": request.weight_kg,
                "distance_km": route_result["distance_km"],
                "regional_boundaries": route_result["regional_boundaries"],
            },
        )

        current_date = datetime.now().strftime("%Y-%m-%d")

        declaration_result = await mcp_server.handle_call_tool(
            "declaration_filler",
            {
                "sender_id": request.sender_id,
                "origin": request.origin,
                "destination": request.destination,
                "route_code": route_result["route_code"],
                "category": request.category,
                "content": request.content,
                "weight_kg": request.weight_kg,
                "wdp": fee_result["wdp"],
                "special_notes": request.special_notes,
                "fee": fee_result["total"],
                "date": current_date,
            },
        )

        return ProcessResponse(
            apikey=API_KEY,
            task=TASK_NAME,
            answer={"declaration": declaration_result["declaration"]},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
