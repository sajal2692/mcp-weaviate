import os
import sys
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, model_validator


class WeaviateConfig(BaseModel):
    """Configuration for Weaviate MCP server."""

    # Connection type
    connection_type: Literal["local", "cloud"] | None = None

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
        # Require explicit connection type
        if self.connection_type is None:
            raise ValueError("connection_type is required")

        if self.connection_type == "local":
            # Require all local connection parameters
            if self.host is None:
                raise ValueError("host is required for local connections")
            if self.port is None:
                raise ValueError("port is required for local connections")
            if self.grpc_port is None:
                raise ValueError("grpc_port is required for local connections")
            # Clear cloud-specific parameters
            self.cluster_url = None
            self.api_key = None
        elif self.connection_type == "cloud":
            # Require cloud connection parameters
            if self.cluster_url is None:
                raise ValueError("cluster_url is required for cloud connections")
            if self.api_key is None:
                raise ValueError("api_key is required for cloud connections")
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


def _format_validation_error(error: ValidationError) -> str:
    """Format Pydantic validation error into user-friendly message."""
    connection_type = "local"  # Default assumption
    missing_params = []

    for err in error.errors():
        if err["type"] == "value_error":
            msg = str(err["msg"])
            if "host is required for local connections" in msg:
                missing_params.append("WEAVIATE_HOST: Host for local Weaviate instance")
            elif "port is required for local connections" in msg:
                missing_params.append("WEAVIATE_PORT: HTTP port for local connection")
            elif "grpc_port is required for local connections" in msg:
                missing_params.append(
                    "WEAVIATE_GRPC_PORT: gRPC port for local connection"
                )
            elif "cluster_url is required for cloud connections" in msg:
                connection_type = "cloud"
                missing_params.append(
                    "WEAVIATE_CLUSTER_URL: Weaviate Cloud Services cluster URL"
                )
            elif "api_key is required for cloud connections" in msg:
                connection_type = "cloud"
                missing_params.append("WEAVIATE_API_KEY: API key for authentication")
            elif "connection_type is required" in msg:
                missing_params.append(
                    "WEAVIATE_CONNECTION_TYPE: Connection type (local or cloud)"
                )

    if missing_params:
        params_list = "\n".join(f"  - {param}" for param in missing_params)
        return f"""Configuration Error: Missing required parameters for {connection_type} connection

Required parameters not found in environment:
{params_list}

Please set these in your .env file or as environment variables.
See .env.example for configuration template."""

    # Fallback to original error if we can't parse it
    return f"Configuration Error: {error}"


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

    # Create configuration with proper error handling
    try:
        return WeaviateConfig(
            connection_type=os.getenv("WEAVIATE_CONNECTION_TYPE"),
            host=os.getenv("WEAVIATE_HOST"),
            port=int(os.getenv("WEAVIATE_PORT"))
            if os.getenv("WEAVIATE_PORT")
            else None,
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
    except ValidationError as e:
        print(_format_validation_error(e), file=sys.stderr)
        sys.exit(1)
