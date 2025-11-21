# mcp_client_test.py

import asyncio
from fastmcp import Client

MCP_URL = "http://127.0.0.1:8006/sse"  # temp.py 서버 주소

async def main():
    async with Client(MCP_URL) as client:
        # 1) 어떤 툴이 있는지 확인
        tools = await client.list_tools()
        print("📌 Available tools:")
        for t in tools:
            print(" -", t.name)

        # 2) get_weekly_horoscope 툴 호출
        #    sign은 "virgo" / "처녀자리" 둘 다 테스트해보기
        result = await client.call_tool(
            "get_weekly_horoscope",
            {"sign": "virgo"}
        )

        # FastMCP Client 결과 구조 참고: result.content[0].text 에 텍스트 있음:contentReference[oaicite:2]{index=2}
        if not result.content:
            print("❌ No content returned from MCP tool")
            return

        text = result.content[0].text
        print("\n🔮 MCP Tool Result:\n")
        print(text)

if __name__ == "__main__":
    asyncio.run(main())
