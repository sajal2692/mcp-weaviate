from typing import Literal

import click
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.config import WeaviateConfig
from src.tools import register_tools


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "streamable-http"]),
    default="stdio",
    help="Transport protocol: stdio (default) for local CLI, streamable-http for remote deployment",
)
@click.option(
    "--http-host",
    default="0.0.0.0",
    help="Host for HTTP transport (default: 0.0.0.0)",
)
@click.option(
    "--http-port",
    type=int,
    default=8000,
    help="Port for HTTP transport (default: 8000)",
)
@click.option(
    "--connection-type",
    type=click.Choice(["local", "cloud"]),
    required=True,
    help="Connection type: local for Docker/self-hosted, cloud for WCS",
)
@click.option("--host", help="Host for local Weaviate connection")
@click.option("--port", type=int, help="HTTP port for local Weaviate connection")
@click.option("--grpc-port", type=int, help="gRPC port for local Weaviate connection")
@click.option(
    "--cluster-url",
    envvar="WEAVIATE_CLUSTER_URL",
    help="Weaviate Cloud Services cluster URL",
)
@click.option("--api-key", envvar="WEAVIATE_API_KEY", help="API key for authentication")
@click.option(
    "--timeout-init", default=30, type=int, help="Initialization timeout in seconds"
)
@click.option("--timeout-query", default=60, type=int, help="Query timeout in seconds")
@click.option(
    "--timeout-insert", default=120, type=int, help="Insert timeout in seconds"
)
@click.option(
    "--cohere-api-key", envvar="COHERE_API_KEY", help="Cohere API key for embeddings"
)
@click.option(
    "--openai-api-key", envvar="OPENAI_API_KEY", help="OpenAI API key for embeddings"
)
def main(
    transport: Literal["stdio", "streamable-http"],
    http_host: str,
    http_port: int,
    connection_type: Literal["local", "cloud"],
    host: str,
    port: int,
    grpc_port: int,
    cluster_url: str | None,
    api_key: str | None,
    timeout_init: int,
    timeout_query: int,
    timeout_insert: int,
    cohere_api_key: str | None,
    openai_api_key: str | None,
) -> None:
    """Weaviate MCP Server - Interact with Weaviate via MCP"""

    # Build additional headers for third-party API keys
    additional_headers = {}
    if cohere_api_key:
        additional_headers["X-Cohere-Api-Key"] = cohere_api_key
    if openai_api_key:
        additional_headers["X-OpenAI-Api-Key"] = openai_api_key

    # Create configuration from CLI arguments or environment variables
    config = WeaviateConfig(
        connection_type=connection_type,
        host=host,
        port=port,
        grpc_port=grpc_port,
        cluster_url=cluster_url,
        api_key=api_key,
        timeout_init=timeout_init,
        timeout_query=timeout_query,
        timeout_insert=timeout_insert,
        additional_headers=additional_headers,
        cohere_api_key=cohere_api_key,
        openai_api_key=openai_api_key,
    )

    # Note: Validation is now handled in WeaviateConfig constructor

    # Initialize FastMCP server with stateless_http for remote deployments
    use_stateless = transport == "streamable-http"
    mcp = FastMCP("Weaviate MCP Server", stateless_http=use_stateless)

    # Register tools with the server
    register_tools(mcp, config)

    # Add health endpoint for HTTP transport (useful for load balancers/k8s)
    if transport == "streamable-http":

        @mcp.custom_route("/health", methods=["GET"])
        async def health_check(request: Request) -> JSONResponse:
            return JSONResponse({"status": "ok"})

    # Run the server with configured transport
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=transport, host=http_host, port=http_port)


if __name__ == "__main__":
    main()
