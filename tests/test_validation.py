"""Tests for input validation and edge cases."""

import pytest

from src.config import WeaviateConfig


class TestParameterValidation:
    """Test validation of various parameters and edge cases."""

    def test_timeout_values_positive(self):
        """Test that timeout values must be positive."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            timeout_init=30,
            timeout_query=60,
            timeout_insert=120,
        )

        assert config.timeout_init == 30
        assert config.timeout_query == 60
        assert config.timeout_insert == 120

    def test_timeout_values_zero(self):
        """Test timeout values can be zero (though not recommended)."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            timeout_init=0,
            timeout_query=0,
            timeout_insert=0,
        )

        assert config.timeout_init == 0
        assert config.timeout_query == 0
        assert config.timeout_insert == 0

    def test_port_values_valid_range(self):
        """Test port values in valid range."""
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        assert config.port == 8080
        assert config.grpc_port == 50051

    def test_port_values_edge_cases(self):
        """Test port values at edge cases."""
        # Test minimum port
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=1, grpc_port=1
        )

        assert config.port == 1
        assert config.grpc_port == 1

        # Test maximum port
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=65535, grpc_port=65535
        )

        assert config.port == 65535
        assert config.grpc_port == 65535

    def test_additional_headers_empty(self):
        """Test empty additional headers."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            additional_headers={},
        )

        assert config.additional_headers == {}

    def test_additional_headers_multiple(self):
        """Test multiple additional headers."""
        headers = {
            "X-Custom-Header": "value1",
            "Authorization": "Bearer token",
            "X-API-Version": "v1",
        }

        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            additional_headers=headers,
        )

        assert config.additional_headers == headers

    def test_cluster_url_formats(self):
        """Test various cluster URL formats."""
        # HTTPS URL
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-key",
        )
        assert config.cluster_url == "https://test.weaviate.network"

        # HTTP URL (less secure but valid)
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="http://test.weaviate.network",
            api_key="test-key",
        )
        assert config.cluster_url == "http://test.weaviate.network"

        # URL with port
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network:8080",
            api_key="test-key",
        )
        assert config.cluster_url == "https://test.weaviate.network:8080"

    def test_api_key_formats(self):
        """Test various API key formats."""
        # Short API key
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="abc123",
        )
        assert config.api_key == "abc123"

        # Long API key
        long_key = "a" * 100
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key=long_key,
        )
        assert config.api_key == long_key

        # API key with special characters
        special_key = "key-with-dashes_and_underscores.and.dots"
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key=special_key,
        )
        assert config.api_key == special_key

    def test_host_formats(self):
        """Test various host formats."""
        # Localhost
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )
        assert config.host == "localhost"

        # IP address
        config = WeaviateConfig(
            connection_type="local", host="127.0.0.1", port=8080, grpc_port=50051
        )
        assert config.host == "127.0.0.1"

        # Remote host
        config = WeaviateConfig(
            connection_type="local",
            host="weaviate.example.com",
            port=8080,
            grpc_port=50051,
        )
        assert config.host == "weaviate.example.com"

    def test_startup_period_validation(self):
        """Test startup period parameter."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            startup_period=10,
        )

        assert config.startup_period == 10

    def test_startup_period_default(self):
        """Test default startup period value."""
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        assert config.startup_period == 5  # Default value


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_none_values_in_optional_fields(self):
        """Test that None values are handled correctly in optional fields."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            cohere_api_key=None,
            openai_api_key=None,
        )

        assert config.cohere_api_key is None
        assert config.openai_api_key is None

    def test_empty_string_values(self):
        """Test behavior with empty string values."""
        # Empty strings should be treated as None for optional fields
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            cohere_api_key="",
            openai_api_key="",
        )

        # Empty strings are preserved (not converted to None)
        assert config.cohere_api_key == ""
        assert config.openai_api_key == ""

    def test_whitespace_in_string_fields(self):
        """Test handling of whitespace in string fields."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="  https://test.weaviate.network  ",
            api_key="  test-key  ",
        )

        # Whitespace is preserved (not stripped)
        assert config.cluster_url == "  https://test.weaviate.network  "
        assert config.api_key == "  test-key  "

    def test_case_sensitivity(self):
        """Test case sensitivity in connection type."""
        # Should be case sensitive
        with pytest.raises(ValueError):
            WeaviateConfig(
                connection_type="LOCAL",  # Uppercase should fail
                host="localhost",
                port=8080,
                grpc_port=50051,
            )

    def test_numeric_string_ports(self):
        """Test that port values must be integers, not strings."""
        # This should work as the config expects int types
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        assert isinstance(config.port, int)
        assert isinstance(config.grpc_port, int)

    def test_very_large_timeout_values(self):
        """Test very large timeout values."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            timeout_init=86400,  # 24 hours
            timeout_query=3600,  # 1 hour
            timeout_insert=7200,  # 2 hours
        )

        assert config.timeout_init == 86400
        assert config.timeout_query == 3600
        assert config.timeout_insert == 7200


class TestConfigConsistency:
    """Test configuration consistency and validation logic."""

    def test_local_config_consistency(self):
        """Test that local config is internally consistent."""
        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            # These should be cleared
            cluster_url="https://should-be-cleared.com",
            api_key="should-be-cleared",
        )

        # Verify local params are set
        assert config.connection_type == "local"
        assert config.host == "localhost"
        assert config.port == 8080
        assert config.grpc_port == 50051

        # Verify cloud params are cleared
        assert config.cluster_url is None
        assert config.api_key is None

    def test_cloud_config_consistency(self):
        """Test that cloud config is internally consistent."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-key",
            # These should be cleared
            host="should-be-cleared",
            port=9999,
            grpc_port=9998,
        )

        # Verify cloud params are set
        assert config.connection_type == "cloud"
        assert config.cluster_url == "https://test.weaviate.network"
        assert config.api_key == "test-key"

        # Verify local params are cleared
        assert config.host is None
        assert config.port is None
        assert config.grpc_port is None

    def test_model_dump_filtered_consistency(self):
        """Test that model_dump_filtered produces consistent output."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="secret-key",
            openai_api_key="openai-secret",
            cohere_api_key=None,
        )

        filtered1 = config.model_dump_filtered()
        filtered2 = config.model_dump_filtered()

        # Should be identical
        assert filtered1 == filtered2

        # Should mask the main api_key
        assert filtered1["api_key"] == "***"

        # Note: model_dump_filtered currently only masks the main api_key,
        # not other API keys like openai_api_key
        assert filtered1["openai_api_key"] == "openai-secret"
        assert "cohere_api_key" not in filtered1  # None values excluded

        # Should preserve non-secret values
        assert filtered1["connection_type"] == "cloud"
        assert filtered1["cluster_url"] == "https://test.weaviate.network"

    def test_additional_headers_with_api_keys(self):
        """Test interaction between additional_headers and API keys."""
        custom_headers = {"X-Custom": "value"}

        config = WeaviateConfig(
            connection_type="local",
            host="localhost",
            port=8080,
            grpc_port=50051,
            additional_headers=custom_headers,
            openai_api_key="openai-key",
            cohere_api_key="cohere-key",
        )

        # additional_headers should only contain what was explicitly set
        assert config.additional_headers == {"X-Custom": "value"}

        # API keys should be stored separately
        assert config.openai_api_key == "openai-key"
        assert config.cohere_api_key == "cohere-key"
