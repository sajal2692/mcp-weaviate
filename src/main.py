import click
from fastmcp import FastMCP

from src.config import WeaviateConfig
from src.tools import register_tools


@click.command()
@click.option(
    "--connection-type",
    type=click.Choice(["local", "cloud"]),
    default="local",
    help="Connection type: local for Docker/self-hosted, cloud for WCS",
)
@click.option("--host", default="localhost", help="Host for local connection")
@click.option("--port", default=8080, type=int, help="HTTP port for local connection")
@click.option(
    "--grpc-port", default=50051, type=int, help="gRPC port for local connection"
)
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
    connection_type: str,
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

    # Validate configuration
    if connection_type == "cloud" and (not cluster_url or not api_key):
        click.echo(
            "Error: --cluster-url and --api-key are required for cloud connections",
            err=True,
        )
        return

    # Initialize FastMCP server
    mcp = FastMCP("Weaviate MCP Server")

    # Register tools with the server
    register_tools(mcp, config)

    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()
