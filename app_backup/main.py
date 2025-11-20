from fastapi import FastAPI
from fastmcp import FastMCP
#from fastapi_mcp import FastApiMCP

from api.v1.endpoints import llm

import uvicorn
from typing import Dict, Any

# FastAPi 앱 생성
app = FastAPI(title = "API",description="API")

# Ollama API 엔드포인트 등록
app.include_router(llm.router, prefix = "/api/v1", tags = ["llm"])


@app.get("/")
async def root():
    return {"message": "FAST API LLM is running!"}

# @app.get("/items/{item_id}")
# def read_tem(item_id: int, q: str = None):
#     return {"item_id:" item_id, "q": q}


mcp = FastMCP(
    "이름",
    instruction = "", # Instructions for the LLM on how to use this tool
    host = "0.0.0.0", # Host address (0.0.0.0 allows connections from any IP)
    port=8005, # Port number for the server
)
mcp.mount()

# -------------------------------------------------------
# 서버 실행
# -------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, log_level="info")

