import asyncio

from fastmcp import Client


async def test_tools() -> None:
    """Test the MCP server tools"""
    client = Client("src/main.py")
    async with client:
        print("=== Testing MCP Server ===\n")

        # Test greeting tool
        print("1. Testing greet tool:")
        result = await client.call_tool("greet", {"name": "Alice"})
        print(f"   Result: {result.data}")
        print()

        # Test search mock
        print("2. Testing search_mock tool:")
        result = await client.call_tool(
            "search_mock",
            {"query": "machine learning", "class_name": "Article", "limit": 3},
        )
        search_data = result.structured_content
        print(f"   Query: {search_data['query']}")
        print(f"   Found {search_data['total']} results:")
        for article in search_data["results"][:2]:  # Show first 2
            print(f"   - {article['properties']['title']}")
        print()

        # Test list classes
        print("3. Testing list_classes_mock tool:")
        result = await client.call_tool("list_classes_mock", {})
        print(f"   Available classes: {result.structured_content}")
        print()

        # Test get schema
        print("4. Testing get_schema_mock tool:")
        result = await client.call_tool("get_schema_mock", {"class_name": "Article"})
        schema_data = result.structured_content
        print(f"   Article schema has {len(schema_data['properties'])} properties:")
        for prop in schema_data["properties"]:
            print(f"   - {prop['name']} ({prop['dataType']})")
        print()

        print("✅ All tools working correctly!")


if __name__ == "__main__":
    asyncio.run(test_tools())
