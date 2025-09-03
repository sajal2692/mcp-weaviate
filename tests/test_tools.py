"""Tests for MCP tools registration and behavior."""

from unittest.mock import MagicMock, patch

from src.config import WeaviateConfig
from src.tools import register_tools


class MockMCP:
    """Mock FastMCP server for testing tool registration."""

    def __init__(self):
        self.tools = {}

    def tool(self, func):
        """Mock tool decorator that stores the function."""
        self.tools[func.__name__] = func
        return func


class TestToolRegistration:
    """Test that all tools are properly registered."""

    def test_all_tools_registered(self):
        """Test that all 11 expected tools are registered."""
        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)

        expected_tools = {
            "get_config",
            "check_connection",
            "list_collections",
            "get_schema",
            "semantic_search",
            "keyword_search",
            "hybrid_search",
            "search",
            "get_collection_objects",
            "is_multi_tenancy_enabled",
            "get_tenant_list",
        }

        assert set(mock_mcp.tools.keys()) == expected_tools
        assert len(mock_mcp.tools) == 11


class TestGetConfigTool:
    """Test get_config tool behavior."""

    def test_get_config_local(self):
        """Test get_config with local configuration."""
        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local",
            host="test-host",
            port=9080,
            grpc_port=51051,
            timeout_init=45,
            openai_api_key="secret-key",
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["get_config"]()

        assert result["connection_type"] == "local"
        assert result["host"] == "test-host"
        assert result["port"] == 9080
        assert result["grpc_port"] == 51051
        assert result["cluster_url"] is None
        assert result["api_key"] is None
        assert result["timeout_init"] == 45
        assert result["openai_api_key"] == "***"  # Masked

    def test_get_config_cloud(self):
        """Test get_config with cloud configuration."""
        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="secret-api-key",
            cohere_api_key="secret-cohere-key",
            additional_headers={"X-Test": "value"},
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["get_config"]()

        assert result["connection_type"] == "cloud"
        assert result["cluster_url"] == "https://test.weaviate.network"
        assert result["api_key"] == "***"  # Masked
        assert result["host"] is None
        assert result["port"] is None
        assert result["grpc_port"] is None
        assert result["cohere_api_key"] == "***"  # Masked
        assert result["additional_headers"] == {"X-Test": "***"}  # Masked


class TestCheckConnectionTool:
    """Test check_connection tool behavior."""

    @patch("src.tools.WeaviateClientManager")
    def test_check_connection_success_local(self, mock_manager_class):
        """Test successful connection check for local setup."""
        mock_manager = MagicMock()
        mock_manager.is_ready.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["check_connection"]()

        assert result["connected"] is True
        assert result["connection_type"] == "local"
        assert result["host"] == "localhost"
        assert "cluster_url" not in result

    @patch("src.tools.WeaviateClientManager")
    def test_check_connection_success_cloud(self, mock_manager_class):
        """Test successful connection check for cloud setup."""
        mock_manager = MagicMock()
        mock_manager.is_ready.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="cloud",
            cluster_url="https://test.weaviate.network",
            api_key="test-key",
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["check_connection"]()

        assert result["connected"] is True
        assert result["connection_type"] == "cloud"
        assert result["cluster_url"] == "https://test.weaviate.network"
        assert "host" not in result

    @patch("src.tools.WeaviateClientManager")
    def test_check_connection_failure(self, mock_manager_class):
        """Test connection check failure."""
        mock_manager = MagicMock()
        mock_manager.is_ready.side_effect = Exception("Connection failed")
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["check_connection"]()

        assert result["connected"] is False
        assert result["error"] == "Connection failed"
        assert result["connection_type"] == "local"


class TestListCollectionsTool:
    """Test list_collections tool behavior."""

    @patch("src.tools.WeaviateClientManager")
    def test_list_collections_success(self, mock_manager_class):
        """Test successful collection listing."""
        mock_client = MagicMock()
        mock_client.collections.list_all.return_value = [
            "Collection1",
            "Collection2",
            "Articles",
        ]

        mock_manager = MagicMock()
        mock_manager.get_client.return_value = mock_client
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["list_collections"]()

        assert result["collections"] == ["Collection1", "Collection2", "Articles"]
        assert result["total"] == 3

    @patch("src.tools.WeaviateClientManager")
    def test_list_collections_error(self, mock_manager_class):
        """Test collection listing with error."""
        mock_client = MagicMock()
        mock_client.collections.list_all.side_effect = Exception("Access denied")

        mock_manager = MagicMock()
        mock_manager.get_client.return_value = mock_client
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["list_collections"]()

        assert result["error"] == "Access denied"
        assert result["collections"] == []
        assert result["total"] == 0


class TestSearchTools:
    """Test search-related tools."""

    @patch("src.tools.WeaviateClientManager")
    def test_semantic_search_success(self, mock_manager_class):
        """Test successful semantic search."""
        # Mock search results
        mock_obj1 = MagicMock()
        mock_obj1.uuid = "uuid-1"
        mock_obj1.properties = {"title": "Article 1", "content": "Content 1"}
        mock_obj1.metadata.score = 0.95

        mock_obj2 = MagicMock()
        mock_obj2.uuid = "uuid-2"
        mock_obj2.properties = {"title": "Article 2", "content": "Content 2"}
        mock_obj2.metadata.score = 0.87

        mock_response = MagicMock()
        mock_response.objects = [mock_obj1, mock_obj2]

        mock_collection = MagicMock()
        mock_collection.query.near_text.return_value = mock_response

        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection

        mock_manager = MagicMock()
        mock_manager.get_client.return_value = mock_client
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["semantic_search"](
            query="machine learning", collection_name="Articles", limit=2
        )

        assert result["total"] == 2
        assert result["query"] == "machine learning"
        assert result["collection_name"] == "Articles"
        assert result["tenant_id"] is None

        results = result["results"]
        assert len(results) == 2
        assert results[0]["id"] == "uuid-1"
        assert results[0]["collection"] == "Articles"
        assert results[0]["properties"]["title"] == "Article 1"
        assert results[0]["score"] == 0.95

    @patch("src.tools.WeaviateClientManager")
    def test_search_with_tenant(self, mock_manager_class):
        """Test search with tenant ID."""
        mock_response = MagicMock()
        mock_response.objects = []

        mock_collection = MagicMock()
        mock_collection.query.near_text.return_value = mock_response

        mock_manager = MagicMock()
        mock_manager.get_collection_with_tenant.return_value = mock_collection
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["semantic_search"](
            query="test query", collection_name="Articles", tenant_id="tenant1"
        )

        mock_manager.get_collection_with_tenant.assert_called_once_with(
            "Articles", "tenant1"
        )
        assert result["tenant_id"] == "tenant1"

    def test_hybrid_search_alpha_validation(self):
        """Test hybrid search alpha parameter validation."""
        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)

        # Test invalid alpha values
        result = mock_mcp.tools["hybrid_search"](
            query="test",
            collection_name="Articles",
            alpha=1.5,  # Invalid: > 1
        )
        assert "error" in result
        assert "Alpha must be between 0 and 1" in result["error"]

        result = mock_mcp.tools["hybrid_search"](
            query="test",
            collection_name="Articles",
            alpha=-0.1,  # Invalid: < 0
        )
        assert "error" in result
        assert "Alpha must be between 0 and 1" in result["error"]

    @patch("src.tools.WeaviateClientManager")
    def test_search_uses_default_alpha(self, mock_manager_class):
        """Test that search tool uses default alpha of 0.3."""
        mock_response = MagicMock()
        mock_response.objects = []

        mock_collection = MagicMock()
        mock_collection.query.hybrid.return_value = mock_response

        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection

        mock_manager = MagicMock()
        mock_manager.get_client.return_value = mock_client
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["search"](
            query="test query", collection_name="Articles"
        )

        # Verify hybrid search was called with alpha=0.3
        mock_collection.query.hybrid.assert_called_once()
        call_args = mock_collection.query.hybrid.call_args
        assert call_args.kwargs["alpha"] == 0.3
        assert result["alpha"] == 0.3


class TestMultiTenancyTools:
    """Test multi-tenancy related tools."""

    @patch("src.tools.WeaviateClientManager")
    def test_is_multi_tenancy_enabled_true(self, mock_manager_class):
        """Test multi-tenancy check when enabled."""
        mock_manager = MagicMock()
        mock_manager.is_multi_tenancy_enabled.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["is_multi_tenancy_enabled"](collection_name="Articles")

        assert result["collection_name"] == "Articles"
        assert result["multi_tenancy_enabled"] is True

    @patch("src.tools.WeaviateClientManager")
    def test_get_tenant_list_success(self, mock_manager_class):
        """Test successful tenant list retrieval."""
        mock_manager = MagicMock()
        mock_manager.get_tenant_list.return_value = ["tenant1", "tenant2", "tenant3"]
        mock_manager.is_multi_tenancy_enabled.return_value = True
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["get_tenant_list"](collection_name="Articles")

        assert result["collection_name"] == "Articles"
        assert result["multi_tenancy_enabled"] is True
        assert result["tenants"] == ["tenant1", "tenant2", "tenant3"]
        assert result["tenant_count"] == 3

    @patch("src.tools.WeaviateClientManager")
    def test_get_tenant_list_error(self, mock_manager_class):
        """Test tenant list retrieval with error."""
        mock_manager = MagicMock()
        mock_manager.get_tenant_list.side_effect = Exception("Collection not found")
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["get_tenant_list"](collection_name="Articles")

        assert result["error"] == "Collection not found"
        assert result["collection_name"] == "Articles"
        assert result["tenants"] == []
        assert result["tenant_count"] == 0


class TestGetCollectionObjectsTool:
    """Test get_collection_objects tool."""

    @patch("src.tools.WeaviateClientManager")
    def test_get_collection_objects_success(self, mock_manager_class):
        """Test successful object retrieval."""
        mock_obj1 = MagicMock()
        mock_obj1.uuid = "obj-1"
        mock_obj1.properties = {"title": "Object 1"}

        mock_obj2 = MagicMock()
        mock_obj2.uuid = "obj-2"
        mock_obj2.properties = {"title": "Object 2"}

        mock_response = MagicMock()
        mock_response.objects = [mock_obj1, mock_obj2]

        mock_collection = MagicMock()
        mock_collection.query.fetch_objects.return_value = mock_response

        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection

        mock_manager = MagicMock()
        mock_manager.get_client.return_value = mock_client
        mock_manager_class.return_value = mock_manager

        mock_mcp = MockMCP()
        config = WeaviateConfig(
            connection_type="local", host="localhost", port=8080, grpc_port=50051
        )

        register_tools(mock_mcp, config)
        result = mock_mcp.tools["get_collection_objects"](
            collection_name="Articles", limit=10, offset=0
        )

        assert result["total"] == 2
        assert result["collection_name"] == "Articles"
        assert result["limit"] == 10
        assert result["offset"] == 0

        results = result["results"]
        assert len(results) == 2
        assert results[0]["id"] == "obj-1"
        assert results[0]["properties"]["title"] == "Object 1"

        mock_collection.query.fetch_objects.assert_called_once_with(limit=10, offset=0)
