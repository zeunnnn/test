"""
MCP + API 서버 동시 실행 스크립트
"""

import asyncio
import sys
import time
import threading
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0,str(project_root))

# path setup
import uvicorn
from fastapi import FastAPI
from src.api import llm

# FastAPi 앱 생성
app = FastAPI(title = "API",description="API")

# Ollama API 엔드포인트 등록
app.include_router(llm.router, prefix = "/api/v1", tags = ["llm"])

@app.get("/")
async def root():
    return {"message": "FAST API LLM is running!"}


from src.mcp_server.calculator import create_calculator_mcp_server
from src.mcp_server.temp import create_temp_mcp_server

from src.config import settings

async def main():
    """
    두 서버 동시에 실행
    """
    # print to console for visibility
    print("🚀 MCP + API 서버를 시작합니다...")
    print(f"📍 API 서버: http://{settings.host}:{settings.port}")
    print(f"📚 API 문서: http://{settings.host}:{settings.port}/docs")
    # print(f"📍 MCP 서버: http://{settings.mcp_host}:{settings.mcp_port}/sse")
    print("⏹️  종료하려면 Ctrl+C를 누르세요")
    print("-" * 50)

    # API 서버를 별도 스레드에서 실행
    api_thread = threading.Thread(target=run_api_server,daemon=True)
    api_thread.start()

    await asyncio.sleep(2)
    # MCP 서버 실행 (메인스레드???)
    await run_mcp_servers()



def run_api_server():
    uvicorn.run(
        "run_server:app",
        host= settings.host,
        port= settings.port,
        log_level="info"
    )

async def run_mcp_servers():
    """
    MCP 서버 실행
    """
    calc_mcp = create_calculator_mcp_server() 
    temp_mcp = create_temp_mcp_server()

    task1 = asyncio.create_task(
        calc_mcp.run_sse_async(
            # host=settings.mcp1_host,
            # port=settings.mcp1_port
        )
    )
    task2 = asyncio.create_task(
        temp_mcp.run_sse_async(
            #host=settings.mcp2_host,
            #port=settings.mcp2_port
        )
    )
    await asyncio.gather(task1,task2)
    
    # server = create_mcp_server()
    # await server.run_sse_async(
    #     host=settings.mcp_host,
    #     port=settings.mcp_port
    #)


# -------------------------------------------------------
# 서버 실행
# -------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())
    #uvicorn.run("main:app", port=8000, log_level="info")

