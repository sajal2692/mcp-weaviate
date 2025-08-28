#!/usr/bin/env python3
"""Test script to verify configuration management."""

import os
import sys
from pathlib import Path

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

from src.config import WeaviateConfig, load_config_from_env


def test_default_config():
    """Test default configuration."""
    config = WeaviateConfig()

    print("Default Configuration:")
    print(f"  Connection Type: {config.connection_type}")
    print(f"  Host: {config.host}")
    print(f"  Port: {config.port}")
    print(f"  gRPC Port: {config.grpc_port}")
    print(f"  Cluster URL: {config.cluster_url}")
    print(f"  API Key: {'***' if config.api_key else None}")
    print(
        f"  Timeouts: init={config.timeout_init}s, query={config.timeout_query}s, insert={config.timeout_insert}s"
    )
    print()


def test_env_config():
    """Test loading configuration from environment variables."""
    # Set some test environment variables
    os.environ["WEAVIATE_CONNECTION_TYPE"] = "cloud"
    os.environ["WEAVIATE_CLUSTER_URL"] = "https://test.weaviate.network"
    os.environ["WEAVIATE_API_KEY"] = "test-api-key-123"
    os.environ["COHERE_API_KEY"] = "cohere-test-key"
    os.environ["OPENAI_API_KEY"] = "openai-test-key"

    config = load_config_from_env()

    print("Environment Configuration:")
    print(f"  Connection Type: {config.connection_type}")
    print(f"  Cluster URL: {config.cluster_url}")
    print(f"  API Key: {'***' if config.api_key else None}")
    print(f"  Cohere API Key: {'***' if config.cohere_api_key else None}")
    print(f"  OpenAI API Key: {'***' if config.openai_api_key else None}")
    print(f"  Additional Headers: {list(config.additional_headers.keys())}")
    print()

    # Clean up
    for key in [
        "WEAVIATE_CONNECTION_TYPE",
        "WEAVIATE_CLUSTER_URL",
        "WEAVIATE_API_KEY",
        "COHERE_API_KEY",
        "OPENAI_API_KEY",
    ]:
        os.environ.pop(key, None)


def test_custom_config():
    """Test custom configuration."""
    config = WeaviateConfig(
        connection_type="cloud",
        cluster_url="https://custom.weaviate.network",
        api_key="custom-api-key",
        timeout_init=60,
        timeout_query=120,
        cohere_api_key="custom-cohere-key",
    )

    print("Custom Configuration:")
    print(f"  Connection Type: {config.connection_type}")
    print(f"  Cluster URL: {config.cluster_url}")
    print(f"  Timeouts: init={config.timeout_init}s, query={config.timeout_query}s")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("Testing Weaviate Configuration Management")
    print("=" * 50)
    print()

    test_default_config()
    test_env_config()
    test_custom_config()

    print("All configuration tests completed!")
