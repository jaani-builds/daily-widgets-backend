import httpx
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.news_service import fetch_top_news

router = APIRouter()


@router.get("/news")
async def get_news(
    city: Optional[str] = Query(None, description="City name"),
    state: Optional[str] = Query(None, description="State or region name"),
    country: Optional[str] = Query(None, description="Country name"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of articles"),
):
    if not any(value and value.strip() for value in (city, state, country)):
        raise HTTPException(status_code=400, detail="At least one of city, state, or country must be provided")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            articles = await fetch_top_news(client, city=city, state=state, country=country, limit=limit)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="News provider timed out") from None
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"News provider error: {exc.response.status_code}") from None
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach news provider") from None

    return {
        "city": city,
        "state": state,
        "country": country,
        "count": len(articles),
        "articles": articles,
    }
