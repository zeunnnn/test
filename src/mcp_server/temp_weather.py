import os
from urllib.parse import urlencode
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.server.fastmcp import FastMCP


# Smithery 인증 정보 (환경변수 또는 직접 입력)
SMITHERY_API_KEY = os.getenv("SMITHERY_API_KEY", "YOUR_API_KEY_HERE")
SMITHERY_PROFILE = os.getenv("SMITHERY_PROFILE", "YOUR_PROFILE_HERE")

# Smithery 서버 URL 구성
base_url = "https://server.smithery.ai/@sunhye/mcp-korea-weather/mcp"
params = {"api_key": "58214f9b-ea5e-4f2a-80f2-ba87a40a9655", "profile": "resident-seahorse-2pAyL7"}

url = f"{base_url}?{urlencode(params)}"


def create_smithery_mcp_server() -> FastMCP:
    mcp = FastMCP(
        "smithery_korea_weather",
        instructions="",
        host="0.0.0.0",
        port=8007,
    )

    @mcp.tool()
    async def list_available_tools() -> str:
        """
        List all available tools from Smithery Korea Weather MCP server.

        Returns:
            str: Available tools list
        """
        try:
            # Connect to the server using HTTP client
            async with streamablehttp_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    
                    # List available tools
                    tools_result = await session.list_tools()
                    
                    tools_list = [f"Available tools: {', '.join([t.name for t in tools_result.tools])}"]
                    tools_list.append("\n=== Tool Details ===\n")
                    
                    for tool in tools_result.tools:
                        tools_list.append(f"• {tool.name}")
                        if hasattr(tool, 'description') and tool.description:
                            tools_list.append(f"  {tool.description}")
                        if hasattr(tool, 'inputSchema'):
                            tools_list.append(f"  Parameters: {tool.inputSchema}")
                        tools_list.append("")
                    
                    return "\n".join(tools_list)
                    
        except Exception as e:
            return f"Error: {str(e)}"

    @mcp.tool()
    async def call_tool(tool_name: str, **kwargs) -> str:
        """
        Call a specific tool from Smithery Korea Weather MCP server.

        Args:
            tool_name (str): Name of the tool to call
            **kwargs: Tool arguments as keyword arguments

        Returns:
            str: Tool execution result
        """
        try:
            # Connect to the server using HTTP client
            async with streamablehttp_client(url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize the connection
                    await session.initialize()
                    
                    # Call the tool
                    result = await session.call_tool(tool_name, arguments=kwargs)
                    
                    # Format the result
                    if result.content:
                        return "\n".join([
                            str(item.text) if hasattr(item, 'text') else str(item)
                            for item in result.content
                        ])
                    else:
                        return "No content returned from tool"
                    
        except Exception as e:
            return f"Error: {str(e)}"

    return mcp


# 서버 실행
if __name__ == "__main__":
    server = create_smithery_mcp_server()
    server.run()