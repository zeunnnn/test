"""
MCP 클라이언트 매니저 - MCP SDK SSE 클라이언트 사용
"""
import json
from pathlib import Path
from typing import Any
from dataclasses import dataclass, field

from mcp import ClientSession
from mcp.client.sse import sse_client

@dataclass 
class MCPServer:
    name: str
    url: str
    description: str = ""
    tools: list = field(default_factory=list)

class MCPClientManager:
    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.tools_cache: dict[str, dict] = {}
    
    def load_config(self, config_path: str = "mcp_config.json"):
        """JSON 설정에서 서버 로드"""
        path = Path(config_path)
        if not path.exists():
            print(f"⚠️ 설정 파일 없음: {config_path}")
            return
        
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        for name, cfg in config.get("mcpServers", {}).items():
            if cfg.get("transport") == "sse":
                host = cfg.get("host", "127.0.0.1")
                port = cfg.get("port", 8000)
                
                self.servers[name] = MCPServer(
                    name=name,
                    url=f"http://{host}:{port}/sse",
                    description=cfg.get("description", "")
                )
                print(f"📌 MCP 서버 등록: {name} ({host}:{port})")
    
    async def discover_all_tools(self) -> list[dict]:
        """모든 서버에서 도구 탐색"""
        all_tools = []
        
        for name, server in self.servers.items():
            try:
                async with sse_client(url=server.url) as streams:
                    read_stream, write_stream = streams
                    
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        
                        for tool in result.tools:
                            tool_dict = {
                                "name": tool.name,
                                "description": tool.description or "",
                                "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {}
                            }
                            server.tools.append(tool_dict)
                            self.tools_cache[tool.name] = {
                                "server": name,
                                "schema": tool_dict
                            }
                            all_tools.append(tool_dict)
                        
                        print(f"✅ {name}: {len(result.tools)}개 도구 발견")
                        
            except Exception as e:
                print(f"❌ {name} 연결 실패: {e}")
        
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """도구 호출"""
        if tool_name not in self.tools_cache:
            return {"error": f"도구 '{tool_name}'을 찾을 수 없습니다"}
        
        server_name = self.tools_cache[tool_name]["server"]
        server = self.servers[server_name]
        
        try:
            async with sse_client(url=server.url) as streams:
                read_stream, write_stream = streams
                
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)
                    
                    # 결과 추출
                    if result.content:
                        for item in result.content:
                            if hasattr(item, 'text'):
                                return {"result": item.text}
                        return {"result": str(result.content)}
                    return {"result": None}
                    
        except Exception as e:
            return {"error": str(e)}
    
    def get_tools_prompt(self) -> str:
        """LLM용 도구 설명 생성"""
        if not self.tools_cache:
            return "사용 가능한 도구가 없습니다."
        
        lines = []
        for tool_name, info in self.tools_cache.items():
            schema = info["schema"]
            desc = schema.get("description", "")
            input_schema = schema.get("inputSchema", {})
            props = input_schema.get("properties", {})
            required = input_schema.get("required", [])
            
            lines.append(f"### {tool_name}")
            lines.append(f"설명: {desc}")
            
            if props:
                lines.append("파라미터:")
                for pname, pinfo in props.items():
                    ptype = pinfo.get("type", "any")
                    pdesc = pinfo.get("description", "")
                    req = "(필수)" if pname in required else ""
                    lines.append(f"  - {pname}: {ptype} {req} {pdesc}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_tools_json_schema(self) -> list[dict]:
        """도구 스키마 JSON 반환"""
        return [info["schema"] for info in self.tools_cache.values()]