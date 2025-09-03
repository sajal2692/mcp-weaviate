"""Shared fixtures and configuration for tests."""

import os
from unittest.mock import MagicMock

import pytest
import weaviate

from src.config import WeaviateConfig


@pytest.fixture
def local_config():
    """Fixture providing a valid local configuration."""
    return WeaviateConfig(
        connection_type="local",
        host="localhost",
        port=8080,
        grpc_port=50051,
        timeout_init=30,
        timeout_query=60,
        timeout_insert=120,
    )


@pytest.fixture
def cloud_config():
    """Fixture providing a valid cloud configuration."""
    return WeaviateConfig(
        connection_type="cloud",
        cluster_url="https://test.weaviate.network",
        api_key="test-api-key",
        timeout_init=30,
        timeout_query=60,
        timeout_insert=120,
    )


@pytest.fixture
def config_with_api_keys():
    """Fixture providing configuration with third-party API keys."""
    return WeaviateConfig(
        connection_type="cloud",
        cluster_url="https://test.weaviate.network",
        api_key="weaviate-key",
        openai_api_key="openai-test-key",
        cohere_api_key="cohere-test-key",
        additional_headers={"X-Custom-Header": "custom-value"},
    )


@pytest.fixture
def mock_weaviate_client():
    """Fixture providing a mock Weaviate client."""
    mock_client = MagicMock(spec=weaviate.WeaviateClient)
    mock_client.is_ready.return_value = True

    # Mock collections
    mock_client.collections.list_all.return_value = [
        "Articles",
        "Documents",
        "TestCollection",
    ]

    # Mock collection object
    mock_collection = MagicMock()
    mock_client.collections.get.return_value = mock_collection

    return mock_client


@pytest.fixture
def mock_search_response():
    """Fixture providing a mock search response."""
    mock_obj1 = MagicMock()
    mock_obj1.uuid = "uuid-1"
    mock_obj1.properties = {"title": "Test Article 1", "content": "Content 1"}
    mock_obj1.metadata.score = 0.95

    mock_obj2 = MagicMock()
    mock_obj2.uuid = "uuid-2"
    mock_obj2.properties = {"title": "Test Article 2", "content": "Content 2"}
    mock_obj2.metadata.score = 0.87

    mock_response = MagicMock()
    mock_response.objects = [mock_obj1, mock_obj2]

    return mock_response


@pytest.fixture
def mock_collection_config():
    """Fixture providing a mock collection configuration."""
    mock_config = MagicMock()

    # Mock properties
    mock_prop1 = MagicMock()
    mock_prop1.name = "title"
    mock_prop1.data_type = "text"
    mock_prop1.description = "Article title"

    mock_prop2 = MagicMock()
    mock_prop2.name = "content"
    mock_prop2.data_type = "text"
    mock_prop2.description = None

    mock_config.properties = [mock_prop1, mock_prop2]

    # Mock multi-tenancy config
    mock_config.multi_tenancy_config.enabled = False

    return mock_config


@pytest.fixture
def mock_multi_tenant_config():
    """Fixture providing a mock multi-tenant collection configuration."""
    mock_config = MagicMock()

    # Mock properties (same as regular config)
    mock_prop1 = MagicMock()
    mock_prop1.name = "title"
    mock_prop1.data_type = "text"

    mock_config.properties = [mock_prop1]

    # Mock multi-tenancy config - enabled
    mock_config.multi_tenancy_config.enabled = True
    mock_config.multi_tenancy_config.auto_tenant_creation = False

    return mock_config


@pytest.fixture
def env_vars_local():
    """Fixture providing local environment variables."""
    return {
        "WEAVIATE_CONNECTION_TYPE": "local",
        "WEAVIATE_HOST": "test-host",
        "WEAVIATE_PORT": "9080",
        "WEAVIATE_GRPC_PORT": "51051",
        "WEAVIATE_TIMEOUT_INIT": "45",
        "WEAVIATE_TIMEOUT_QUERY": "90",
        "WEAVIATE_TIMEOUT_INSERT": "180",
    }


@pytest.fixture
def env_vars_cloud():
    """Fixture providing cloud environment variables."""
    return {
        "WEAVIATE_CONNECTION_TYPE": "cloud",
        "WEAVIATE_CLUSTER_URL": "https://env-test.weaviate.network",
        "WEAVIATE_API_KEY": "env-api-key",
        "OPENAI_API_KEY": "env-openai-key",
        "COHERE_API_KEY": "env-cohere-key",
    }


@pytest.fixture
def clean_env():
    """Fixture that cleans environment variables before and after test."""
    # Store original values
    original_env = {}
    env_vars_to_clean = [
        "WEAVIATE_CONNECTION_TYPE",
        "WEAVIATE_HOST",
        "WEAVIATE_PORT",
        "WEAVIATE_GRPC_PORT",
        "WEAVIATE_CLUSTER_URL",
        "WEAVIATE_API_KEY",
        "OPENAI_API_KEY",
        "COHERE_API_KEY",
        "WEAVIATE_TIMEOUT_INIT",
        "WEAVIATE_TIMEOUT_QUERY",
        "WEAVIATE_TIMEOUT_INSERT",
        "WEAVIATE_STARTUP_PERIOD",
    ]

    for var in env_vars_to_clean:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var in env_vars_to_clean:
        if var in os.environ:
            del os.environ[var]
        if var in original_env:
            os.environ[var] = original_env[var]


@pytest.fixture(autouse=True)
def reset_logging():
    """Fixture to reset logging configuration between tests."""
    import logging

    # Reset root logger level
    logging.getLogger().setLevel(logging.WARNING)

    # Reset any handlers that might have been added
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)

    yield

    # Clean up after test
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)


@pytest.fixture
def mock_fastmcp():
    """Fixture providing a mock FastMCP server for tool registration tests."""

    class MockFastMCP:
        def __init__(self):
            self.tools = {}
            self._registered_tools = []

        def tool(self, func):
            """Mock tool decorator."""
            self.tools[func.__name__] = func
            self._registered_tools.append(func.__name__)
            return func

        def get_registered_tools(self):
            """Get list of registered tool names."""
            return self._registered_tools.copy()

    return MockFastMCP()


# Test markers for different categories
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "config: mark test as a configuration test")
    config.addinivalue_line("markers", "validation: mark test as a validation test")
    config.addinivalue_line("markers", "tools: mark test as a tools test")


# Skip tests that require actual Weaviate connection
def pytest_runtest_setup(item):
    """Skip tests marked as requiring real connections."""
    if hasattr(item, "get_closest_marker"):
        marker = item.get_closest_marker("requires_weaviate")
        if marker:
            pytest.skip("Test requires actual Weaviate connection")


# Utility functions for tests
def create_mock_response_with_objects(objects_data):
    """Create a mock response with specified objects data.

    Args:
        objects_data: List of dicts with 'uuid', 'properties', and optionally 'score'

    Returns:
        Mock response object
    """
    mock_objects = []

    for obj_data in objects_data:
        mock_obj = MagicMock()
        mock_obj.uuid = obj_data["uuid"]
        mock_obj.properties = obj_data["properties"]

        if "score" in obj_data:
            mock_obj.metadata.score = obj_data["score"]
        else:
            mock_obj.metadata.score = None

        mock_objects.append(mock_obj)

    mock_response = MagicMock()
    mock_response.objects = mock_objects

    return mock_response
