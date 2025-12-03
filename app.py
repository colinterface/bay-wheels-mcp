"""
HTTP server wrapper for Bay Wheels MCP server.
This module creates a Starlette app with health checks for container deployment.
"""
import os
import logging
import sys
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route, Mount
import uvicorn

# Import the MCP server
from server import mcp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Health check endpoint for container orchestration
async def health_check(request):
    """Health check endpoint for load balancers and orchestrators."""
    return JSONResponse({
        "status": "healthy",
        "service": "bay-wheels-mcp",
        "version": "0.1.0"
    })

# Create the StreamableHTTP app from FastMCP
mcp_app = mcp.streamable_http_app()

# Wrap with health check route
app = Starlette(
    debug=False,
    routes=[
        Route("/health", health_check),
        Mount("/", app=mcp_app),
    ]
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Bay Wheels MCP HTTP server on {host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
