import os
import re
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP
import httpx
from bs4 import BeautifulSoup

def create_temp_mcp_server() -> FastMCP:
    """
    별자리 운세
    """

    mcp = FastMCP(
    "Horoscope manager",
    instructions="별자리 운세를 가져오는 MCP입니다. "
            "항상 사용자의 별자리를 먼저 확인하고, 해당 별자리에 맞는 운세를 전달하세요",
    host = "127.0.0.1",
    port=8006,
    )

    VALID_SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
    ]

    KOR_TO_SLUG = {
    "양자리": "aries", "황소자리": "taurus", "쌍둥이자리": "gemini",
    "쌍둥이": "gemini", "게자리": "cancer", "사자자리": "leo",
    "처녀자리": "virgo", "천칭자리": "libra", "전갈자리": "scorpio",
    "사수자리": "sagittarius", "염소자리": "capricorn",
    "물병자리": "aquarius", "물고기자리": "pisces",
    }

    @mcp.tool()
    async def get_weekly_horoscope(sign: str) -> str:
        """
        이번주 별자리 운세를 가져옵니다.

        Args:
            sign: 영어 슬러그(예: 'scorpio') 또는 한글 이름(예: '전갈자리')

        Returns:
            해당 별자리의 운세 텍스트
        """
        slug = sign.strip().lower()
        
        if slug in KOR_TO_SLUG:
            slug = KOR_TO_SLUG[slug]
        
        if slug not in VALID_SIGNS:
            return f"Error: '{sign}'은(는) 유효한 별자리가 아닙니다."

        url = f"https://www.astrolutely.com/forecasts/{slug}/"
        kor_name = KOR_TO_SLUG.get(slug, slug.upper())

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(15.0, connect=5.0),
                follow_redirects=True,
                verify=False
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.TimeoutException:
            return "Error: 운세 서버 응답 시간 초과."
        except httpx.HTTPStatusError as e:
            return f"Error: HTTP {e.response.status_code}"
        except httpx.RequestError as e:
            return f"Error: 네트워크 오류 - {str(e)}"

        soup = BeautifulSoup(response.text, "html.parser")

        # "The Week Ahead" h2 태그 찾기
        week_heading = None
        for h2 in soup.find_all('h2'):
            if 'Week Ahead' in h2.get_text():
                week_heading = h2
                break

        if not week_heading:
            return "Error: 'The Week Ahead' 섹션을 찾을 수 없습니다."

        # find_next()로 다음 요소들 탐색
        date_text = ""
        horoscope_text = ""
        
        current = week_heading.find_next()
        seen_texts = set()
        
        while current:
            text = current.get_text().strip()
            
            # 다음 섹션에 도달하면 중단
            if current.name == 'h2':
                break
            
            # 날짜 패턴 찾기
            if not date_text and re.search(r'Monday.*–.*Sunday', text):
                date_text = text
            
            # 운세 본문 찾기 (길이가 100자 이상)
            elif len(text) > 100 and text not in seen_texts:
                if not re.search(r'Monday.*–.*Sunday', text):
                    horoscope_text = text
                    seen_texts.add(text)
                    break
            
            current = current.find_next()

        if not horoscope_text:
            return "Error: 운세 내용을 찾을 수 없습니다."

        # 불필요한 문구 제거
        remove_phrases = [
        "See last week's forecast below.",
        "See last week’s forecast below.",  # (기울어진 따옴표)
        "Click here for my YouTube videos.",
        "See the month ahead forecast below.",
    ]
        for phrase in remove_phrases:
            horoscope_text = horoscope_text.replace(phrase, "")
        
        # 줄바꿈 정리
        horoscope_text = re.sub(r'\n\s*\n', '\n', horoscope_text).strip()

        # 결과 포맷팅
        result = f"🔮 {kor_name} 주간 운세\n"
        result += f"📅 {date_text}\n\n" if date_text else "\n"
        result += horoscope_text

        return result

    return mcp

