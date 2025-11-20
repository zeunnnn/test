import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup

# 영문 별자리 슬러그
VALID_SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]

# 한글 → 슬러그 매핑 (편의용)
KOR_TO_SLUG = {
    "양자리": "aries",
    "황소자리": "taurus",
    "쌍둥이자리": "gemini",
    "쌍둥이": "gemini",
    "게자리": "cancer",
    "사자자리": "leo",
    "처녀자리": "virgo",
    "천칭자리": "libra",
    "전갈자리": "scorpio",
    "사수자리": "sagittarius",
    "염소자리": "capricorn",
    "물병자리": "aquarius",
    "물고기자리": "pisces",
}

def create_Astrology_mcp_server() -> FastMCP:
    """
    별자리 운세
    """

    mcp = FastMCP(
    "Astrology",
    instructions="서양 12궁 별자리 운세를 가져오는 MCP입니다. "
            "항상 사용자의 별자리를 먼저 확인하고, 해당 별자리에 맞는 운세를 요약해서 전달하세요",
    host = "0.0.0.0",
    port=8006,
    )

    @mcp.tool()
    async def get_weekly_horoscope(sign: str) -> str:
        """
        이번주 별자리 운세를 가져옵니다.

        Args:
            sign: 영어 슬러그(예: 'scorpio') 또는 한글 이름(예: '전갈자리')

        Returns:
            해당 별자리의 운세 텍스트 """

        slug = sign.strip().lower()

        # 한글 별자리 → 슬러그 변환
        if slug in KOR_TO_SLUG: slug = KOR_TO_SLUG[slug]

        base_url = "https://www.astrolutely.com/forecasts/"
        url = f"{base_url}{slug}/"

        # 1) HTTP 요청
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        # 2) HTML 파싱
        soup = BeautifulSoup(response.text, "html.parser")

        # "The Week Ahead for ~" 헤딩 찾기 (h2 또는 h3)
        # "The Week Ahead" 섹션 찾기
        week_ahead_section = None
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            if 'The Week Ahead' in heading.get_text():
                week_ahead_section = heading
                break

        if not week_ahead_section:
            return "Error: 'The Week Ahead' 섹션을 찾을 수 없습니다."

        # 날짜 정보와 본문 내용 추출
        result = []
        result.append(f"=== {zodiac_en.upper()} 주간 운세 ===\n")
        
        # 제목 추가
        result.append(week_ahead_section.get_text().strip())
        
        # 다음 형제 요소들에서 날짜와 내용 찾기
        current = week_ahead_section.find_next_sibling()
        content_found = False
        
        while current and not content_found:
            text = current.get_text().strip()
            
            # 날짜 패턴 찾기 (예: Monday, 17 Nov – Sunday, 23 Nov)
            if re.search(r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday).*–.*\d{4}', text):
                result.append(f"\n{text}\n")
                
                # 날짜 다음의 본문 내용 찾기
                content = current.find_next_sibling()
                if content:
                    result.append(content.get_text().strip())
                    content_found = True
                    break
            
            # p 태그에 바로 내용이 있는 경우
            elif current.name == 'p' and len(text) > 50:
                result.append(f"\n{text}")
                content_found = True
                break
            
            current = current.find_next_sibling()

        if not content_found:
            return "Error: 운세 내용을 찾을 수 없습니다."

        return "\n".join(result)
        

    return mcp

