from fastmcp import FastMCP

from src.tools import register_tools


def main() -> None:
    """Entry point for the mcp-weaviate CLI"""
    # Initialize FastMCP server
    mcp = FastMCP("Weaviate MCP Server")

    # Register all tools
    register_tools(mcp)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
