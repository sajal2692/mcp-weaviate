import logging
from typing import Any

from weaviate.classes.query import MetadataQuery

from src.config import WeaviateConfig
from src.weaviate_client import WeaviateClientManager


def register_tools(mcp: Any, config: WeaviateConfig) -> None:
    """Register all MCP tools with the FastMCP server.

    This function registers all available Weaviate operations as MCP tools,
    including search capabilities, collection management, schema inspection,
    and multi-tenancy operations.

    Args:
        mcp: The FastMCP server instance to register tools with.
        config: WeaviateConfig object containing connection settings.
    """

    logger = logging.getLogger(__name__)
    client_manager = WeaviateClientManager(config)

    @mcp.tool
    def get_config() -> dict[str, Any]:
        """Get the current Weaviate configuration.

        Returns the active Weaviate connection configuration with sensitive
        values (API keys, headers) masked for security.

        Returns:
            dict: Configuration details including:
                - connection_type: 'local' or 'cloud'
                - host/port or cluster_url
                - timeout settings
                - masked API keys
        """
        return {
            "connection_type": config.connection_type,
            "host": config.host,
            "port": config.port,
            "grpc_port": config.grpc_port,
            "cluster_url": config.cluster_url,
            "api_key": "***" if config.api_key else None,
            "timeout_init": config.timeout_init,
            "timeout_query": config.timeout_query,
            "timeout_insert": config.timeout_insert,
            "startup_period": config.startup_period,
            "cohere_api_key": "***" if config.cohere_api_key else None,
            "openai_api_key": "***" if config.openai_api_key else None,
            "additional_headers": dict.fromkeys(config.additional_headers.keys(), "***")
            if config.additional_headers
            else {},
        }

    @mcp.tool
    def check_connection() -> dict[str, Any]:
        """Check if the Weaviate connection is working.

        Tests the connection to the Weaviate instance and reports
        its status and connection details.

        Returns:
            dict: Connection status including:
                - connected: bool indicating if connection is successful
                - connection_type: 'local' or 'cloud'
                - host/cluster_url: connection endpoint
                - error: error message if connection failed (optional)
        """
        try:
            is_ready = client_manager.is_ready()
            result: dict[str, Any] = {
                "connected": is_ready,
                "connection_type": config.connection_type,
            }
            if config.connection_type == "local":
                result["host"] = config.host
            else:
                result["cluster_url"] = config.cluster_url
            return result
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return {
                "connected": False,
                "error": str(e),
                "connection_type": config.connection_type,
            }

    @mcp.tool
    def list_collections() -> dict[str, Any]:
        """List all available Weaviate collections.

        Retrieves a list of all collections (classes) defined in the
        Weaviate schema.

        Returns:
            dict: Collection information including:
                - collections: list of collection names
                - total: total number of collections
                - error: error message if operation failed (optional)
        """
        try:
            client = client_manager.get_client()
            collections = client.collections.list_all()
            return {"collections": list(collections), "total": len(collections)}
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return {"error": str(e), "collections": [], "total": 0}

    @mcp.tool
    def get_schema(collection_name: str | None = None) -> dict[str, Any]:
        """Get schema information for Weaviate collections.

        Retrieves detailed schema information for a specific collection
        or all collections if no name is specified.

        Args:
            collection_name: Optional name of a specific collection.
                           If None, returns schema for all collections.

        Returns:
            dict: Schema information including:
                - For specific collection:
                    - collection: collection name
                    - properties: list of property definitions
                    - multi_tenancy_enabled: bool
                    - tenant_count: number of tenants (if multi-tenant)
                - For all collections:
                    - Full schema with all collection definitions
                - error: error message if operation failed (optional)
        """
        try:
            if collection_name:
                # Get schema for specific collection
                client = client_manager.get_client()
                collection = client.collections.get(collection_name)
                config = collection.config.get()

                properties = []
                if hasattr(config, "properties") and config.properties:
                    for prop in config.properties:
                        prop_info = {
                            "name": prop.name,
                            "data_type": prop.data_type,
                        }
                        if hasattr(prop, "description") and prop.description:
                            prop_info["description"] = prop.description
                        properties.append(prop_info)

                # Add multi-tenancy information
                multi_tenancy_enabled = client_manager.is_multi_tenancy_enabled(
                    collection_name
                )
                schema_info = {
                    "collection": collection_name,
                    "properties": properties,
                    "multi_tenancy_enabled": multi_tenancy_enabled,
                }

                # Add tenant information if multi-tenancy is enabled
                if multi_tenancy_enabled:
                    tenants = client_manager.get_tenant_list(collection_name)
                    schema_info["tenant_count"] = len(tenants)

                    # Check for auto_tenant_creation if available in config
                    if hasattr(config, "multi_tenancy_config") and hasattr(
                        config.multi_tenancy_config, "auto_tenant_creation"
                    ):
                        schema_info["auto_tenant_creation"] = (
                            config.multi_tenancy_config.auto_tenant_creation
                        )

                return schema_info
            else:
                # Get full schema
                return client_manager.get_schema()

        except Exception as e:
            logger.error(
                f"Error getting schema for {collection_name or 'all collections'}: {e}"
            )
            if collection_name:
                return {
                    "error": f"Collection {collection_name} not found or error: {str(e)}"
                }
            else:
                return {"error": str(e), "collections": []}

    @mcp.tool
    def semantic_search(
        query: str,
        collection_name: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search for objects in Weaviate using vector similarity.

        Performs semantic search using vector embeddings to find objects
        similar in meaning to the query text. The query is vectorized
        and compared against stored vectors using cosine similarity.

        Args:
            query: The search query text to vectorize and match.
            collection_name: Name of the collection to search in.
            tenant_id: Optional tenant ID for multi-tenant collections.
            limit: Maximum number of results to return (default: 5).

        Returns:
            dict: Search results including:
                - results: list of matching objects with:
                    - id: object UUID
                    - collection: collection name
                    - properties: object properties
                    - score: similarity score (0-1, higher is better)
                - total: number of results returned
                - query: the original query
                - collection_name: searched collection
                - tenant_id: tenant ID if specified
                - error: error message if search failed (optional)
        """
        try:
            # Use appropriate method based on whether tenant_id is provided
            if tenant_id:
                collection = client_manager.get_collection_with_tenant(
                    collection_name, tenant_id
                )
            else:
                client = client_manager.get_client()
                collection = client.collections.get(collection_name)

            # Perform vector search using the query text
            response = collection.query.near_text(
                query=query, limit=limit, return_metadata=MetadataQuery(score=True)
            )

            results = []
            for obj in response.objects:
                result: dict[str, Any] = {
                    "id": str(obj.uuid),
                    "collection": collection_name,
                    "properties": obj.properties,
                }

                # Add score if available
                if hasattr(obj.metadata, "score") and obj.metadata.score is not None:
                    result["score"] = float(obj.metadata.score)

                results.append(result)

            return {
                "results": results,
                "total": len(results),
                "query": query,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
            }

        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "query": query,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
            }

    @mcp.tool
    def keyword_search(
        query: str,
        collection_name: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search for objects in Weaviate using BM25 keyword search.

        Performs traditional keyword-based search using the BM25 algorithm,
        which ranks documents based on term frequency and inverse document
        frequency. Best for exact term matching and keyword-based retrieval.

        Args:
            query: The keyword search query.
            collection_name: Name of the collection to search in.
            tenant_id: Optional tenant ID for multi-tenant collections.
            limit: Maximum number of results to return (default: 5).

        Returns:
            dict: Search results including:
                - results: list of matching objects with:
                    - id: object UUID
                    - collection: collection name
                    - properties: object properties
                    - score: BM25 relevance score
                - total: number of results returned
                - query: the original query
                - collection_name: searched collection
                - tenant_id: tenant ID if specified
                - error: error message if search failed (optional)
        """
        try:
            # Use appropriate method based on whether tenant_id is provided
            if tenant_id:
                collection = client_manager.get_collection_with_tenant(
                    collection_name, tenant_id
                )
            else:
                client = client_manager.get_client()
                collection = client.collections.get(collection_name)

            # Perform BM25 keyword search
            response = collection.query.bm25(
                query=query, limit=limit, return_metadata=MetadataQuery(score=True)
            )

            results = []
            for obj in response.objects:
                result: dict[str, Any] = {
                    "id": str(obj.uuid),
                    "collection": collection_name,
                    "properties": obj.properties,
                }

                # Add score if available
                if hasattr(obj.metadata, "score") and obj.metadata.score is not None:
                    result["score"] = float(obj.metadata.score)

                results.append(result)

            return {
                "results": results,
                "total": len(results),
                "query": query,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
            }

        except Exception as e:
            logger.error(
                f"Error performing BM25 search on collection {collection_name}: {e}"
            )
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "query": query,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
            }

    def _perform_hybrid_search(
        query: str,
        collection_name: str,
        tenant_id: str | None = None,
        alpha: float = 0.3,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Internal helper function to perform hybrid search.

        This function contains the actual hybrid search logic that can be
        called by both the hybrid_search and search MCP tools.
        """
        try:
            # Validate alpha parameter
            if not 0 <= alpha <= 1:
                return {
                    "error": "Alpha must be between 0 and 1",
                    "results": [],
                    "total": 0,
                    "query": query,
                    "collection_name": collection_name,
                    "tenant_id": tenant_id,
                    "alpha": alpha,
                }

            # Use appropriate method based on whether tenant_id is provided
            if tenant_id:
                collection = client_manager.get_collection_with_tenant(
                    collection_name, tenant_id
                )
            else:
                client = client_manager.get_client()
                collection = client.collections.get(collection_name)

            # Perform hybrid search
            response = collection.query.hybrid(
                query=query,
                alpha=alpha,
                limit=limit,
                return_metadata=MetadataQuery(score=True),
            )

            results = []
            for obj in response.objects:
                result: dict[str, Any] = {
                    "id": str(obj.uuid),
                    "collection": collection_name,
                    "properties": obj.properties,
                }

                # Add score if available
                if hasattr(obj.metadata, "score") and obj.metadata.score is not None:
                    result["score"] = float(obj.metadata.score)

                results.append(result)

            return {
                "results": results,
                "total": len(results),
                "query": query,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
                "alpha": alpha,
            }

        except Exception as e:
            logger.error(
                f"Error performing hybrid search on collection {collection_name}: {e}"
            )
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "query": query,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
                "alpha": alpha,
            }

    @mcp.tool
    def hybrid_search(
        query: str,
        collection_name: str,
        tenant_id: str | None = None,
        alpha: float = 0.3,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search for objects using hybrid search (BM25 + vector).

        Combines keyword-based BM25 search with semantic vector search
        using Reciprocal Rank Fusion (RRF) to leverage both exact term
        matching and semantic similarity. The alpha parameter controls
        the balance between the two approaches.

        Args:
            query: The search query text.
            collection_name: Name of the collection to search in.
            tenant_id: Optional tenant ID for multi-tenant collections.
            alpha: Balance between vector and keyword search (0.0-1.0):
                - 1.0 = pure vector search (100% semantic)
                - 0.0 = pure BM25 search (100% keyword)
                - 0.5 = equal weight (50% each)
                - 0.3 = default (30% vector, 70% keyword)
            limit: Maximum number of results to return (default: 5).

        Returns:
            dict: Search results including:
                - results: list of matching objects with:
                    - id: object UUID
                    - collection: collection name
                    - properties: object properties
                    - score: combined relevance score
                - total: number of results returned
                - query: the original query
                - collection_name: searched collection
                - tenant_id: tenant ID if specified
                - alpha: alpha value used
                - error: error message if search failed (optional)
        """
        return _perform_hybrid_search(
            query=query,
            collection_name=collection_name,
            tenant_id=tenant_id,
            alpha=alpha,
            limit=limit,
        )

    @mcp.tool
    def search(
        query: str,
        collection_name: str,
        tenant_id: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search for objects in Weaviate (uses hybrid search by default).

        A simplified search interface that uses hybrid search with
        balanced default settings (alpha=0.3). This provides good
        results for most use cases by combining keyword and semantic
        search capabilities.

        Args:
            query: The search query text.
            collection_name: Name of the collection to search in.
            tenant_id: Optional tenant ID for multi-tenant collections.
            limit: Maximum number of results to return (default: 5).

        Returns:
            dict: Search results (same format as hybrid_search).
        """
        # Use the helper function with default alpha value
        return _perform_hybrid_search(
            query=query,
            collection_name=collection_name,
            tenant_id=tenant_id,
            alpha=0.3,  # Default balanced towards keyword search
            limit=limit,
        )

    @mcp.tool
    def get_collection_objects(
        collection_name: str,
        tenant_id: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get objects from a specific collection.

        Retrieves objects from a collection with pagination support.
        Useful for browsing collection contents or implementing
        paginated displays.

        Args:
            collection_name: Name of the collection to retrieve from.
            tenant_id: Optional tenant ID for multi-tenant collections.
            limit: Maximum number of objects to return (default: 10).
            offset: Number of objects to skip for pagination (default: 0).

        Returns:
            dict: Retrieved objects including:
                - results: list of objects with:
                    - id: object UUID
                    - collection: collection name
                    - properties: object properties
                - total: number of objects returned
                - collection_name: collection name
                - tenant_id: tenant ID if specified
                - limit: limit used
                - offset: offset used
                - error: error message if retrieval failed (optional)
        """
        try:
            # Use appropriate method based on whether tenant_id is provided
            if tenant_id:
                collection = client_manager.get_collection_with_tenant(
                    collection_name, tenant_id
                )
            else:
                client = client_manager.get_client()
                collection = client.collections.get(collection_name)

            response = collection.query.fetch_objects(limit=limit, offset=offset)

            results = []
            for obj in response.objects:
                results.append(
                    {
                        "id": str(obj.uuid),
                        "collection": collection_name,
                        "properties": obj.properties,
                    }
                )

            return {
                "results": results,
                "total": len(results),
                "collection_name": collection_name,
                "tenant_id": tenant_id,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(
                f"Error getting objects from collection {collection_name}: {e}"
            )
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "collection_name": collection_name,
                "tenant_id": tenant_id,
            }

    @mcp.tool
    def is_multi_tenancy_enabled(collection_name: str) -> dict[str, Any]:
        """Check if a collection has multi-tenancy enabled.

        Determines whether a specific collection is configured for
        multi-tenancy, allowing data isolation between different tenants.

        Args:
            collection_name: Name of the collection to check.

        Returns:
            dict: Multi-tenancy status including:
                - collection_name: name of the checked collection
                - multi_tenancy_enabled: bool indicating if enabled
                - error: error message if check failed (optional)
        """
        try:
            enabled = client_manager.is_multi_tenancy_enabled(collection_name)
            return {
                "collection_name": collection_name,
                "multi_tenancy_enabled": enabled,
            }
        except Exception as e:
            logger.error(
                f"Error checking multi-tenancy status for {collection_name}: {e}"
            )
            return {
                "error": str(e),
                "collection_name": collection_name,
                "multi_tenancy_enabled": False,
            }

    @mcp.tool
    def get_tenant_list(collection_name: str) -> dict[str, Any]:
        """Get list of tenants for a collection.

        Retrieves all tenant IDs configured for a multi-tenant collection.
        Returns an empty list if multi-tenancy is not enabled.

        Args:
            collection_name: Name of the collection to list tenants for.

        Returns:
            dict: Tenant information including:
                - collection_name: name of the collection
                - multi_tenancy_enabled: bool indicating if enabled
                - tenants: list of tenant IDs
                - tenant_count: total number of tenants
                - error: error message if operation failed (optional)
        """
        try:
            tenants = client_manager.get_tenant_list(collection_name)
            multi_tenancy_enabled = client_manager.is_multi_tenancy_enabled(
                collection_name
            )
            return {
                "collection_name": collection_name,
                "multi_tenancy_enabled": multi_tenancy_enabled,
                "tenants": tenants,
                "tenant_count": len(tenants),
            }
        except Exception as e:
            logger.error(f"Error getting tenant list for {collection_name}: {e}")
            return {
                "error": str(e),
                "collection_name": collection_name,
                "tenants": [],
                "tenant_count": 0,
            }
