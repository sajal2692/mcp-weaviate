"""Tests for WeaviateClientManager."""

from unittest.mock import MagicMock, patch

import pytest
import weaviate

from src.config import WeaviateConfig
from src.weaviate_client import WeaviateClientManager


class TestWeaviateClientManager:
    """Test WeaviateClientManager initialization and behavior."""

    def test_init_with_local_config(self):
        """Test initialization with local configuration."""
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)
        assert manager.config == config
        assert manager._client is None

    def test_init_with_cloud_config(self):
        """Test initialization with cloud configuration."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-key",
        )

        manager = WeaviateClientManager(config)
        assert manager.config == config
        assert manager._client is None

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_create_local_client(self, mock_connect_local):
        """Test creating a local client."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local",
            host="test-host",
            port=9080,
            grpc_port=51051,
            timeout_init=45,
            timeout_query=90,
            timeout_insert=180,
            additional_headers={"X-Test": "value"},
        )

        manager = WeaviateClientManager(config)
        client = manager.get_client()

        assert client == mock_client
        mock_connect_local.assert_called_once_with(
            host="test-host", port=9080, grpc_port=51051, headers={"X-Test": "value"}
        )

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_create_local_client_with_defaults(self, mock_connect_local):
        """Test creating a local client with default host/port values."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local",
            host="localhost",  # Valid config first
            port=8080,
            grpc_port=50051,
        )

        manager = WeaviateClientManager(config)

        # Test the default logic in _create_local_client directly
        with (
            patch.object(manager.config, "host", None),
            patch.object(manager.config, "port", None),
            patch.object(manager.config, "grpc_port", None),
        ):
            manager.get_client()

            # Verify defaults are used in the call
            mock_connect_local.assert_called_once_with(
                host="localhost",  # Default
                port=8080,  # Default
                grpc_port=50051,  # Default
                headers={},
            )

    @patch("src.weaviate_client.weaviate.connect_to_weaviate_cloud")
    def test_create_cloud_client(self, mock_connect_cloud):
        """Test creating a cloud client."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_connect_cloud.return_value = mock_client

        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-api-key",
            additional_headers={"X-Test": "value"},
        )

        manager = WeaviateClientManager(config)
        client = manager.get_client()

        assert client == mock_client
        mock_connect_cloud.assert_called_once_with(
            cluster_url="https://test.weaviate.network",
            auth_credentials="test-api-key",
            headers={"X-Test": "value"},
        )

    @patch("src.weaviate_client.weaviate.connect_to_weaviate_cloud")
    def test_create_cloud_client_missing_params_raises_error(self, mock_connect_cloud):
        """Test that cloud client creation raises error with missing parameters."""
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-key",
        )

        # Simulate missing parameters after validation
        config.cluster_url = None

        manager = WeaviateClientManager(config)

        with pytest.raises(ValueError, match="cluster_url and api_key are required"):
            manager.get_client()

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_get_client_caches_instance(self, mock_connect_local):
        """Test that get_client caches the client instance."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)

        client1 = manager.get_client()
        client2 = manager.get_client()

        assert client1 == client2
        assert client1 == mock_client
        mock_connect_local.assert_called_once()  # Should only be called once

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_close_client(self, mock_connect_local):
        """Test closing the client connection."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)
        manager.get_client()

        manager.close()

        mock_client.close.assert_called_once()
        assert manager._client is None

    def test_close_client_when_none(self):
        """Test closing client when no client exists."""
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)
        manager.close()  # Should not raise an error

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_is_ready_true(self, mock_connect_local):
        """Test is_ready returns True when client is ready."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_client.is_ready.return_value = True
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)

        assert manager.is_ready() is True
        mock_client.is_ready.assert_called_once()

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_is_ready_false(self, mock_connect_local):
        """Test is_ready returns False when client is not ready."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_client.is_ready.return_value = False
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)

        assert manager.is_ready() is False

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_is_ready_exception(self, mock_connect_local):
        """Test is_ready returns False when exception occurs."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_client.is_ready.side_effect = Exception("Connection error")
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)

        with patch("src.weaviate_client.logger") as mock_logger:
            assert manager.is_ready() is False
            mock_logger.error.assert_called_once()

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_context_manager(self, mock_connect_local):
        """Test context manager behavior."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        with WeaviateClientManager(config) as manager:
            assert isinstance(manager, WeaviateClientManager)
            client = manager.get_client()
            assert client == mock_client

        mock_client.close.assert_called_once()

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_get_collection(self, mock_connect_local):
        """Test getting a collection without tenant context."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_collections = MagicMock()
        mock_collection = MagicMock()
        mock_collections.get.return_value = mock_collection
        mock_client.collections = mock_collections
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)
        collection = manager.get_collection("TestCollection")

        assert collection == mock_collection
        mock_client.collections.get.assert_called_once_with("TestCollection")

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_get_collection_with_tenant(self, mock_connect_local):
        """Test getting a collection with tenant context."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_collections = MagicMock()
        mock_base_collection = MagicMock()
        mock_tenant_collection = MagicMock()
        mock_base_collection.with_tenant.return_value = mock_tenant_collection
        mock_collections.get.return_value = mock_base_collection
        mock_client.collections = mock_collections
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)
        collection = manager.get_collection_with_tenant("TestCollection", "tenant1")

        assert collection == mock_tenant_collection
        mock_client.collections.get.assert_called_once_with("TestCollection")
        mock_base_collection.with_tenant.assert_called_once_with("tenant1")

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_is_multi_tenancy_enabled_true(self, mock_connect_local):
        """Test checking multi-tenancy when enabled."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_collections = MagicMock()
        mock_collection = MagicMock()
        mock_config = MagicMock()
        mock_config.multi_tenancy_config.enabled = True
        mock_collection.config.get.return_value = mock_config
        mock_collections.get.return_value = mock_collection
        mock_client.collections = mock_collections
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)

        assert manager.is_multi_tenancy_enabled("TestCollection") is True

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_is_multi_tenancy_enabled_false(self, mock_connect_local):
        """Test checking multi-tenancy when disabled."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_collections = MagicMock()
        mock_collection = MagicMock()
        mock_config = MagicMock()
        mock_config.multi_tenancy_config.enabled = False
        mock_collection.config.get.return_value = mock_config
        mock_collections.get.return_value = mock_collection
        mock_client.collections = mock_collections
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)

        assert manager.is_multi_tenancy_enabled("TestCollection") is False

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_is_multi_tenancy_enabled_no_config(self, mock_connect_local):
        """Test checking multi-tenancy when no multi_tenancy_config exists."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_collections = MagicMock()
        mock_collection = MagicMock()
        mock_config = MagicMock(spec=[])  # No multi_tenancy_config attribute
        mock_collection.config.get.return_value = mock_config
        mock_collections.get.return_value = mock_collection
        mock_client.collections = mock_collections
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)

        assert manager.is_multi_tenancy_enabled("TestCollection") is False

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_get_tenant_list_enabled(self, mock_connect_local):
        """Test getting tenant list when multi-tenancy is enabled."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_collections = MagicMock()
        mock_collection = MagicMock()
        mock_config = MagicMock()
        mock_config.multi_tenancy_config.enabled = True
        mock_collection.config.get.return_value = mock_config
        mock_collection.tenants.get.return_value = {"tenant1": {}, "tenant2": {}}
        mock_collections.get.return_value = mock_collection
        mock_client.collections = mock_collections
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)
        tenants = manager.get_tenant_list("TestCollection")

        assert set(tenants) == {"tenant1", "tenant2"}

    @patch("src.weaviate_client.weaviate.connect_to_local")
    def test_get_tenant_list_disabled(self, mock_connect_local):
        """Test getting tenant list when multi-tenancy is disabled."""
        mock_client = MagicMock(spec=weaviate.WeaviateClient)
        mock_collections = MagicMock()
        mock_collection = MagicMock()
        mock_config = MagicMock(spec=[])  # No multi_tenancy_config
        mock_collection.config.get.return_value = mock_config
        mock_collections.get.return_value = mock_collection
        mock_client.collections = mock_collections
        mock_connect_local.return_value = mock_client

        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        manager = WeaviateClientManager(config)
        tenants = manager.get_tenant_list("TestCollection")

        assert tenants == []
