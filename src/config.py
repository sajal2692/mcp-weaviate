import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator


class WeaviateConfig(BaseModel):
    """Configuration for Weaviate MCP server."""

    # Connection type
    connection_type: Literal["local", "cloud"] = "local"

    # Local connection parameters (only for local connections)
    host: str | None = None
    port: int | None = None
    grpc_port: int | None = None

    # Cloud connection parameters (only for cloud connections)
    cluster_url: str | None = None
    api_key: str | None = None

    # Common configuration
    timeout_init: int = 30
    timeout_query: int = 60
    timeout_insert: int = 120
    additional_headers: dict[str, str] = Field(default_factory=dict)
    startup_period: int = 5

    # Third-party API keys
    cohere_api_key: str | None = None
    openai_api_key: str | None = None

    @model_validator(mode="after")
    def validate_connection_params(self) -> "WeaviateConfig":
        """Ensure appropriate parameters are set based on connection type."""
        if self.connection_type == "local":
            # Set defaults for local connection if not provided
            if self.host is None:
                self.host = "localhost"
            if self.port is None:
                self.port = 8080
            if self.grpc_port is None:
                self.grpc_port = 50051
            # Clear cloud-specific parameters
            self.cluster_url = None
            self.api_key = None
        elif self.connection_type == "cloud":
            # Clear local-specific parameters
            self.host = None
            self.port = None
            self.grpc_port = None

        return self

    def model_dump_filtered(self) -> dict[str, str | int | None]:
        """Export config excluding None values."""
        data = self.model_dump(exclude_none=True)

        # Mask API key in output
        if "api_key" in data and data["api_key"]:
            data["api_key"] = "***"

        return data


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

    # Create configuration - Pydantic will handle validation and defaults
    return WeaviateConfig(
        connection_type=os.getenv("WEAVIATE_CONNECTION_TYPE", "local"),
        host=os.getenv("WEAVIATE_HOST"),
        port=int(os.getenv("WEAVIATE_PORT")) if os.getenv("WEAVIATE_PORT") else None,
        grpc_port=int(os.getenv("WEAVIATE_GRPC_PORT"))
        if os.getenv("WEAVIATE_GRPC_PORT")
        else None,
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
