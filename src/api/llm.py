from fastapi import APIRouter
from pydantic import BaseModel
import requests
import asyncio


router = APIRouter()

# Ollama API URL 설정
OLLAMA_API_URL = "http://localhost:11434/api/generate"

# 요청 데이터 모델 정의
class ChatRequest(BaseModel):
    prompt: str

# Ollama API 호출 엔드포인트
@router.post("/llm/")
async def chat_with_llm(request: ChatRequest):
    payload = {
        "model": "qwen3:4b",
        "prompt": request.prompt,
        "stream": False # 실시간 스트리밍 여부 (False: 일반응답)
    }
    
    response = requests.post(OLLAMA_API_URL, json=payload)
    return response.json()