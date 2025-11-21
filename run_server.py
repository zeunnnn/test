"""
MCP + API 서버 동시 실행
"""
import asyncio
import sys
import threading
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.mcp_client.manager import MCPClientManager
from src.config import settings

# MCP 매니저
mcp_manager = MCPClientManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 MCP 초기화"""
    # JSON 설정에서 서버 로드
    mcp_manager.load_config("mcp_config.json")
    
    # MCP 서버 시작 대기
    await asyncio.sleep(3)
    
    # 도구 탐색
    await mcp_manager.discover_all_tools()
    
    # LLM 라우터에 매니저 주입
    from src.api import llm
    llm.set_mcp_manager(mcp_manager)
    
    print("✅ MCP 클라이언트 준비 완료")
    print(f"🔧 발견된 도구: {list(mcp_manager.tools_cache.keys())}")
    yield

app = FastAPI(
    title="MCP + LLM API",
    description="MCP 도구를 활용하는 LLM API",
    lifespan=lifespan
)

from src.api import llm
app.include_router(llm.router, prefix="/api/v1", tags=["llm"])

@app.get("/")
async def root():
    return {"message": "MCP + LLM API 실행 중"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "servers": list(mcp_manager.servers.keys()),
        "tools": list(mcp_manager.tools_cache.keys())
    }


def run_api_server():
    uvicorn.run(
        "run_server:app",
        host=settings.host,
        port=settings.port,
        log_level="info"
    )

async def run_mcp_servers():
    """MCP 서버들 실행 (FastMCP)"""
    from src.mcp_server.calculator import create_calculator_mcp_server
    from src.mcp_server.temp import create_temp_mcp_server
    
    calc_mcp = create_calculator_mcp_server()
    horoscope_mcp = create_temp_mcp_server()
    
    print("🔧 MCP 서버 시작...")
    
    await asyncio.gather(
        calc_mcp.run_sse_async(),
        horoscope_mcp.run_sse_async()
    )

async def main():
    print("🚀 서버 시작...")
    print(f"📍 API: http://{settings.host}:{settings.port}")
    print(f"📚 문서: http://{settings.host}:{settings.port}/docs")
    print("-" * 50)
    
    # API 서버 (별도 스레드)
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # MCP 서버 (메인 스레드)
    await run_mcp_servers()

if __name__ == "__main__":
    asyncio.run(main())