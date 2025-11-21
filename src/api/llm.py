"""
LLM API 라우터 - LLM이 도구를 자율적으로 선택
"""
from fastapi import APIRouter
from pydantic import BaseModel
import httpx
import json
import re

router = APIRouter()

OLLAMA_API_URL = "http://localhost:11434/api/generate"

class ChatRequest(BaseModel):
    prompt: str

mcp_manager = None

def set_mcp_manager(manager):
    global mcp_manager
    mcp_manager = manager

SYSTEM_PROMPT_TEMPLATE = """/no_think
당신은 도구를 사용할 수 있는 AI 어시스턴트입니다.

{tools_description}

## 응답 규칙
1. 도구가 필요하면 반드시 아래 JSON 형식으로만 응답하세요:
{{"tool": "도구이름", "arguments": {{...}}}}

2. 도구가 필요없으면 일반 텍스트로 답변하세요.

3. 예시:
- 계산 요청: {{"tool": "add", "arguments": {{"input": {{"a": 5, "b": 3}}}}}}
- 운세 요청: {{"tool": "get_weekly_horoscope", "arguments": {{"sign": "virgo"}}}}

## 주의사항
- JSON 외의 설명을 추가하지 마세요
- 도구를 사용할 때는 오직 JSON만 출력하세요
"""

async def call_ollama(prompt: str, system: str = None) -> str:
    """Ollama API 호출"""
    full_prompt = prompt
    if system:
        full_prompt = f"{system}\n\n사용자: {prompt}\n\n어시스턴트:"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            OLLAMA_API_URL,
            json={
                "model": "qwen3:4b",
                "prompt": full_prompt,
                "stream": False
            }
        )
        data = resp.json()
        return data.get("response", "")

def extract_json(text: str) -> dict | None:
    """응답에서 JSON 추출"""
    # 코드 블록 내 JSON
    patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{[^{}]*"tool"[^{}]*"arguments"[^{}]*\{.*?\}[^{}]*\})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                continue
    
    # 전체가 JSON인 경우
    text = text.strip()
    if text.startswith("{"):
        try:
            # 첫 번째 완전한 JSON 객체 찾기
            brace_count = 0
            end_idx = 0
            for i, c in enumerate(text):
                if c == "{":
                    brace_count += 1
                elif c == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            if end_idx > 0:
                return json.loads(text[:end_idx])
        except:
            pass
    
    return None

@router.post("/llm/")
async def chat_with_llm(request: ChatRequest):
    """MCP 도구를 활용한 LLM 채팅"""
    global mcp_manager
    
    if not mcp_manager:
        return {"error": "MCP 매니저가 초기화되지 않았습니다"}
    
    # 도구 설명 생성
    tools_desc = mcp_manager.get_tools_prompt()
    system = SYSTEM_PROMPT_TEMPLATE.format(tools_description=tools_desc)
    
    # 1단계: LLM에게 질문 (도구 사용 여부 결정)
    llm_response = await call_ollama(request.prompt, system)
    print(f"📝 LLM 원본 응답: {llm_response[:200]}...")
    
    # 2단계: JSON 도구 호출 파싱
    tool_call = extract_json(llm_response)
    
    if tool_call and "tool" in tool_call:
        tool_name = tool_call["tool"]
        arguments = tool_call.get("arguments", {})
        
        print(f"🔧 도구 호출 감지: {tool_name}({arguments})")
        
        # 3단계: MCP 도구 실행
        tool_result = await mcp_manager.call_tool(tool_name, arguments)
        print(f"📦 도구 결과: {str(tool_result)[:200]}...")
        
        # 4단계: 결과로 최종 응답 생성
        follow_up = f"""/no_think
사용자 질문: {request.prompt}

도구 '{tool_name}' 실행 결과:
{json.dumps(tool_result, ensure_ascii=False, indent=2)}

위 결과를 바탕으로 사용자에게 친절하게 한국어로 답변해주세요.
운세인 경우 핵심 내용을 자연스럽게 요약해주세요."""

        final_response = await call_ollama(follow_up)
        
        return {
            "response": final_response,
            "tool_used": tool_name,
            "tool_arguments": arguments,
            "tool_result": tool_result,
            "debug_llm_raw": llm_response
        }
    
    # 도구 호출 없이 일반 응답
    return {
        "response": llm_response,
        "tool_used": None
    }

@router.get("/tools/")
async def list_tools():
    """사용 가능한 MCP 도구 목록"""
    if not mcp_manager:
        return {"error": "MCP 매니저가 초기화되지 않았습니다"}
    
    return {
        "tools": mcp_manager.get_tools_json_schema(),
        "prompt_format": mcp_manager.get_tools_prompt()
    }

@router.post("/llm/reload-tools/")
async def reload_tools():
    """MCP 도구 재탐색"""
    if not mcp_manager:
        return {"error": "MCP 매니저가 초기화되지 않았습니다"}
    
    tools = await mcp_manager.discover_all_tools()
    return {"reloaded": len(tools), "tools": [t["name"] for t in tools]}