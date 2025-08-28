import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class WeaviateConfig:
    """Configuration dataclass for Weaviate MCP server."""

    # Connection type
    connection_type: str = "local"  # "local" or "cloud"

    # Local connection parameters
    host: str = "localhost"
    port: int = 8080
    grpc_port: int = 50051

    # Cloud connection parameters
    cluster_url: str | None = None

    # Authentication
    api_key: str | None = None

    # Additional configuration
    timeout_init: int = 30
    timeout_query: int = 60
    timeout_insert: int = 120
    additional_headers: dict[str, str] = field(default_factory=dict)
    startup_period: int = 5

    # Third-party API keys
    cohere_api_key: str | None = None
    openai_api_key: str | None = None


def load_config_from_env() -> WeaviateConfig:
    """Load configuration from environment variables."""
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Build additional headers for third-party API keys
    additional_headers = {}

    cohere_key = os.getenv("COHERE_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if cohere_key:
        additional_headers["X-Cohere-Api-Key"] = cohere_key
    if openai_key:
        additional_headers["X-OpenAI-Api-Key"] = openai_key

    return WeaviateConfig(
        connection_type=os.getenv("WEAVIATE_CONNECTION_TYPE", "local"),
        host=os.getenv("WEAVIATE_HOST", "localhost"),
        port=int(os.getenv("WEAVIATE_PORT", "8080")),
        grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT", "50051")),
        cluster_url=os.getenv("WEAVIATE_CLUSTER_URL"),
        api_key=os.getenv("WEAVIATE_API_KEY"),
        timeout_init=int(os.getenv("WEAVIATE_TIMEOUT_INIT", "30")),
        timeout_query=int(os.getenv("WEAVIATE_TIMEOUT_QUERY", "60")),
        timeout_insert=int(os.getenv("WEAVIATE_TIMEOUT_INSERT", "120")),
        startup_period=int(os.getenv("WEAVIATE_STARTUP_PERIOD", "5")),
        additional_headers=additional_headers,
        cohere_api_key=cohere_key,
        openai_api_key=openai_key,
    )
