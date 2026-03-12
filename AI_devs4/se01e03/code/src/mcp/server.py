from fastmcp import FastMCP
from .tools import check_package, redirect_package

# Create MCP server instance
mcp_server = FastMCP("package-service-proxy")

# Register tools with MCP server
@mcp_server.tool()
async def check_package_tool(package_id: str) -> dict:
    """Check the status of a package."""
    return await check_package(package_id)

@mcp_server.tool()
async def redirect_package_tool(package_id: str, destination: str, code: str) -> dict:
    """
    Redirect a package to a destination.
    
    Note: The system will handle the actual destination routing.
    """
    return await redirect_package(package_id, destination, code)

def get_mcp_server():
    """Get the MCP server instance."""
    return mcp_server
