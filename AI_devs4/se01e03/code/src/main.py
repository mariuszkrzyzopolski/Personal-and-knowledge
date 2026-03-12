from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn

from .config import config
from .agent.logic import agent
from .mcp.server import get_mcp_server

# Initialize FastAPI app
app = FastAPI(
    title="Package Service Proxy",
    description="FastAPI proxy server with embedded MCP tools for package operations",
    version="0.1.0",
)

# Initialize MCP server
mcp_server = get_mcp_server()


# Pydantic models for request/response
class OperatorRequest(BaseModel):
    sessionID: str = Field(..., description="Session identifier for the operator")
    msg: str = Field(..., description="Message from the operator")


class OperatorResponse(BaseModel):
    msg: str = Field(..., description="Response message for the operator")


@app.on_event("startup")
async def startup_event():
    """Validate configuration on startup."""
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {"status": "Package Service Proxy is running", "port": config.PORT}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/operator_proxy")
async def operator_proxy_health():
    """Health check for operator proxy service."""
    return {"status": "Operator proxy is running", "port": config.PORT}


@app.post("/operator_proxy", response_model=OperatorResponse)
async def operator_proxy(request: OperatorRequest):
    """
    Main endpoint for operator interactions.

    Processes operator messages through the LLM agent with MCP tool access.
    Maintains session history and returns responses in the specified format.
    """
    try:
        # Validate input
        if not request.sessionID or not request.sessionID.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="sessionID is required and cannot be empty",
            )

        if not request.msg or not request.msg.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="msg is required and cannot be empty",
            )

        # Process message through agent
        response = await agent.process_message(request.sessionID, request.msg)

        # Print agent response to terminal logs
        print(f"[Agent Response with model {config.OPENROUTER_MODEL}] {response}")

        # Always return HTTP 200 with the response format
        return OperatorResponse(msg=response)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Handle all other errors gracefully
        print(f"Error processing request: {e}")
        # Always return HTTP 200 with friendly message
        return OperatorResponse(msg="There was an issue, please try again")


@app.get("/mcp/tools")
async def list_mcp_tools():
    """List available MCP tools (for debugging/inspection)."""
    try:
        tools = mcp_server.list_tools()
        return {"tools": tools}
    except Exception as e:
        return {"error": f"Failed to list tools: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host=config.HOST, port=config.PORT, reload=True)
