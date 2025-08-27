from typing import List, Dict, Optional


def register_tools(mcp):
    """Register all MCP tools with the FastMCP server."""
    
    @mcp.tool
    def greet(name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}! Welcome to the Weaviate MCP Server."

    @mcp.tool
    def search_mock(
        query: str, 
        class_name: str = "Article", 
        limit: int = 5
    ) -> Dict:
        """Mock search function that simulates Weaviate search results."""
        mock_results = [
            {
                "id": f"mock-{i}",
                "class": class_name,
                "properties": {
                    "title": f"Article {i}: {query}",
                    "content": f"This is a mock article about {query} with some sample content.",
                    "author": f"Author {i}",
                    "date": "2024-01-15"
                },
                "score": 0.9 - (i * 0.1)
            }
            for i in range(1, min(limit + 1, 6))
        ]
        
        return {
            "results": mock_results,
            "total": len(mock_results),
            "query": query,
            "class_name": class_name
        }

    @mcp.tool
    def list_classes_mock() -> List[str]:
        """List available Weaviate classes (mock data)."""
        return ["Article", "Product", "Document", "Person", "Company"]

    @mcp.tool
    def get_schema_mock(class_name: Optional[str] = None) -> Dict:
        """Get schema information for Weaviate classes (mock data)."""
        schemas = {
            "Article": {
                "class": "Article",
                "properties": [
                    {"name": "title", "dataType": ["text"]},
                    {"name": "content", "dataType": ["text"]},
                    {"name": "author", "dataType": ["text"]},
                    {"name": "date", "dataType": ["date"]}
                ]
            },
            "Product": {
                "class": "Product", 
                "properties": [
                    {"name": "name", "dataType": ["text"]},
                    {"name": "description", "dataType": ["text"]},
                    {"name": "price", "dataType": ["number"]},
                    {"name": "category", "dataType": ["text"]}
                ]
            }
        }
        
        if class_name:
            return schemas.get(class_name, {"error": f"Class {class_name} not found"})
        
        return {"classes": list(schemas.keys()), "schemas": schemas}