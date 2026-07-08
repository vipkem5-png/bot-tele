import httpx
from bot.config import LINK4M_API_KEY

LINK4M_API = "https://link4m.co/api-shorten/v2"

async def shorten_link(long_url: str) -> dict:
    """Rút gọn link qua link4m API — earn per click."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            LINK4M_API,
            params={"api": LINK4M_API_KEY, "url": long_url}
        )
        data = resp.json()
        return data  # {"status":"success","shortenedUrl":"https://link4m.co/xxx"}

# Danh sách link quảng cáo để user "visit"
AD_TASKS = [
    {
        "id": "ad_001",
        "title": "🎯 Xem quảng cáo #1",
        "url": "https://link4m.co/sample1",   # thay bằng link thật
        "description": "Truy cập link, chờ 15 giây để nhận điểm"
    },
    {
        "id": "ad_002", 
        "title": "🎯 Xem quảng cáo #2",
        "url": "https://link4m.co/sample2",
        "description": "Truy cập link, chờ 15 giây để nhận điểm"
    },
]

def get_ad_tasks() -> list:
    return AD_TASKS
