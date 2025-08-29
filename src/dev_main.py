from fastmcp import FastMCP

from src.config import load_config_from_env
from src.tools import register_tools

# Load configuration from .env file
config = load_config_from_env()

# Initialize FastMCP server with standard variable name
mcp = FastMCP("Weaviate MCP Server")

# Register tools with the server
register_tools(mcp, config)

# Standard variable name for fastmcp
app = mcp
server = mcp
