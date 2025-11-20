from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP (
    "Calculator",
    instruction = "Calculator", # Instructions for the LLM on how to use this tool
    #host = "0.0.0.0", # Host address (0.0.0.0 allows connections from any IP)
    #port=8005, # Port number for the server
)

class CalculatorInput(BaseModel):
    a: float
    b: float

@mcp.tool()
def add(input: CalculatorInput) -> float:
    """두 숫자를 더합니다."""
    return input.a + input.b

@mcp.tool()
def substract(input: CalculatorInput) -> int:
    """a에서 b를 뺍니다다."""
    return input.a - input.b

# 리소스 정의???? 이게 뭐지
# @mcp.resource()
# def get_config() ->    

#@mcp.prompt()
def calculator_prompt() -> str:
    """계산기를 사용하기 위한 프롬프트"""
    return """
    You are a helpful calculator assistant.
    You can add and substract numbers using the available tools.     
    """


if __name__ == "__main__":
     mcp.run(transport="stdio")
