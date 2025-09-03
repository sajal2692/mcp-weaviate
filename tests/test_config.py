"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import WeaviateConfig, _format_validation_error, load_config_from_env


class TestWeaviateConfig:
    """Test WeaviateConfig model validation and behavior."""

    def test_local_config_valid(self):
        """Test valid local configuration."""
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        assert config.connection_type == "local"
        assert config.host == "localhost"
        assert config.port == 8080
        assert config.grpc_port == 50051
        assert config.cluster_url is None
        assert config.api_key is None

    def test_cloud_config_valid(self):
        """Test valid cloud configuration."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-api-key",
        )

        assert config.connection_type == "cloud"
        assert config.cluster_url == "https://test.weaviate.network"
        assert config.api_key == "test-api-key"
        assert config.host is None
        assert config.port is None
        assert config.grpc_port is None

    def test_connection_type_required(self):
        """Test that connection_type is required."""
        with pytest.raises(ValidationError) as exc_info:
            WeaviateConfig()

        assert "connection_type is required" in str(exc_info.value)

    def test_local_config_missing_host(self):
        """Test local config validation fails without host."""
        with pytest.raises(ValidationError) as exc_info:
            WeaviateConfig(connection_type="local", port=8080, grpc_port=50051)

        assert "host is required for local connections" in str(exc_info.value)

    def test_local_config_missing_port(self):
        """Test local config validation fails without port."""
        with pytest.raises(ValidationError) as exc_info:
            WeaviateConfig(connection_type="local", host="localhost", grpc_port=50051)

        assert "port is required for local connections" in str(exc_info.value)

    def test_local_config_missing_grpc_port(self):
        """Test local config validation fails without grpc_port."""
        with pytest.raises(ValidationError) as exc_info:
            WeaviateConfig(connection_type="local", host="localhost", port=8080)

        assert "grpc_port is required for local connections" in str(exc_info.value)

    def test_cloud_config_missing_cluster_url(self):
        """Test cloud config validation fails without cluster_url."""
        with pytest.raises(ValidationError) as exc_info:
            WeaviateConfig(connection_type="cloud", api_key="test-key")

        assert "cluster_url is required for cloud connections" in str(exc_info.value)

    def test_cloud_config_missing_api_key(self):
        """Test cloud config validation fails without api_key."""
        with pytest.raises(ValidationError) as exc_info:
            WeaviateConfig(
                connection_type="cloud", cluster_url="https://test.weaviate.network"
            )

        assert "api_key is required for cloud connections" in str(exc_info.value)

    def test_local_config_clears_cloud_params(self):
        """Test that local config clears cloud-specific parameters."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            cluster_url="https://should-be-cleared.com",
            api_key="should-be-cleared",
        )

        assert config.cluster_url is None
        assert config.api_key is None

    def test_cloud_config_clears_local_params(self):
        """Test that cloud config clears local-specific parameters."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-key",
            host="should-be-cleared",
            port=9999,
            grpc_port=9998,
        )

        assert config.host is None
        assert config.port is None
        assert config.grpc_port is None

    def test_default_timeouts(self):
        """Test default timeout values."""
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        assert config.timeout_init == 30
        assert config.timeout_query == 60
        assert config.timeout_insert == 120

    def test_custom_timeouts(self):
        """Test custom timeout values."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            timeout_init=60,
            timeout_query=120,
            timeout_insert=240,
        )

        assert config.timeout_init == 60
        assert config.timeout_query == 120
        assert config.timeout_insert == 240

    def test_additional_headers(self):
        """Test additional headers handling."""
        headers = {"X-Custom-Header": "value", "Authorization": "Bearer token"}
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            additional_headers=headers,
        )

        assert config.additional_headers == headers

    def test_api_keys(self):
        """Test API key handling."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="weaviate-key",
            openai_api_key="openai-key",
            cohere_api_key="cohere-key",
        )

        assert config.api_key == "weaviate-key"
        assert config.openai_api_key == "openai-key"
        assert config.cohere_api_key == "cohere-key"

    def test_model_dump_filtered_masks_api_key(self):
        """Test that model_dump_filtered masks API keys."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="secret-key",
        )

        filtered = config.model_dump_filtered()
        assert filtered["api_key"] == "***"
        assert filtered["cluster_url"] == "https://test.weaviate.network"

    def test_model_dump_filtered_excludes_none(self):
        """Test that model_dump_filtered excludes None values."""
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        filtered = config.model_dump_filtered()
        assert "cluster_url" not in filtered
        assert "api_key" not in filtered
        assert "cohere_api_key" not in filtered
        assert "openai_api_key" not in filtered


class TestLoadConfigFromEnv:
    """Test loading configuration from environment variables."""

    def test_load_local_config_from_env(self):
        """Test loading local configuration from environment."""
        env_vars = {
            "WEAVIATE_CONNECTION_TYPE": "local",
            "WEAVIATE_HOST": "test-host",
            "WEAVIATE_PORT": "9080",
            "WEAVIATE_GRPC_PORT": "51051",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = load_config_from_env()

            assert config.connection_type == "local"
            assert config.host == "test-host"
            assert config.port == 9080
            assert config.grpc_port == 51051

    def test_load_cloud_config_from_env(self):
        """Test loading cloud configuration from environment."""
        env_vars = {
            "WEAVIATE_CONNECTION_TYPE": "cloud",
            "WEAVIATE_CLUSTER_URL": "https://env-test.weaviate.network",
            "WEAVIATE_API_KEY": "env-api-key",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = load_config_from_env()

            assert config.connection_type == "cloud"
            assert config.cluster_url == "https://env-test.weaviate.network"
            assert config.api_key == "env-api-key"

    def test_load_config_with_api_keys(self):
        """Test loading configuration with third-party API keys."""
        env_vars = {
            "WEAVIATE_CONNECTION_TYPE": "local",
            "WEAVIATE_HOST": "localhost",
            "WEAVIATE_PORT": "8080",
            "WEAVIATE_GRPC_PORT": "50051",
            "OPENAI_API_KEY": "openai-test-key",
            "COHERE_API_KEY": "cohere-test-key",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = load_config_from_env()

            assert config.openai_api_key == "openai-test-key"
            assert config.cohere_api_key == "cohere-test-key"
            assert "X-OpenAI-Api-Key" in config.additional_headers
            assert "X-Cohere-Api-Key" in config.additional_headers
            assert config.additional_headers["X-OpenAI-Api-Key"] == "openai-test-key"
            assert config.additional_headers["X-Cohere-Api-Key"] == "cohere-test-key"

    def test_load_config_with_custom_timeouts(self):
        """Test loading configuration with custom timeout values."""
        env_vars = {
            "WEAVIATE_CONNECTION_TYPE": "local",
            "WEAVIATE_HOST": "localhost",
            "WEAVIATE_PORT": "8080",
            "WEAVIATE_GRPC_PORT": "50051",
            "WEAVIATE_TIMEOUT_INIT": "45",
            "WEAVIATE_TIMEOUT_QUERY": "90",
            "WEAVIATE_TIMEOUT_INSERT": "180",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = load_config_from_env()

            assert config.timeout_init == 45
            assert config.timeout_query == 90
            assert config.timeout_insert == 180

    @patch("sys.exit")
    def test_load_config_validation_error_exits(self, mock_exit):
        """Test that validation errors cause sys.exit."""
        env_vars = {
            "WEAVIATE_CONNECTION_TYPE": "local",
            # Missing required parameters
        }

        with patch.dict(os.environ, env_vars, clear=True):
            load_config_from_env()
            mock_exit.assert_called_once_with(1)


class TestFormatValidationError:
    """Test validation error formatting."""

    def test_format_local_connection_errors(self):
        """Test formatting of local connection validation errors."""
        try:
            WeaviateConfig(connection_type="local")
        except ValidationError as e:
            formatted = _format_validation_error(e)

            assert (
                "Configuration Error: Missing required parameters for local connection"
                in formatted
            )
            # Only the first missing parameter will be reported by Pydantic
            assert "WEAVIATE_HOST: Host for local Weaviate instance" in formatted

    def test_format_cloud_connection_errors(self):
        """Test formatting of cloud connection validation errors."""
        try:
            WeaviateConfig(connection_type="cloud")
        except ValidationError as e:
            formatted = _format_validation_error(e)

            assert (
                "Configuration Error: Missing required parameters for cloud connection"
                in formatted
            )
            # Only the first missing parameter will be reported by Pydantic
            assert (
                "WEAVIATE_CLUSTER_URL: Weaviate Cloud Services cluster URL" in formatted
            )

    def test_format_connection_type_required_error(self):
        """Test formatting of missing connection type error."""
        try:
            WeaviateConfig()
        except ValidationError as e:
            formatted = _format_validation_error(e)

            assert (
                "WEAVIATE_CONNECTION_TYPE: Connection type (local or cloud)"
                in formatted
            )

    def test_format_unknown_error_fallback(self):
        """Test fallback formatting for unknown validation errors."""
        # Create a mock validation error that won't match our patterns
        error = ValidationError.from_exception_data("test", [])
        formatted = _format_validation_error(error)

        assert "Configuration Error:" in formatted
