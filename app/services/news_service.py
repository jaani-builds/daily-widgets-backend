import httpx
from fastapi import HTTPException
from typing import Optional


async def fetch_top_news(client: httpx.AsyncClient, city: str, country: Optional[str] = None, limit: int = 10):
    query_parts = [city.strip()]
    if country and country.strip():
        query_parts.append(country.strip())
    query = " ".join(part for part in query_parts if part)
    if not query:
        raise HTTPException(status_code=400, detail="city must not be empty")

    # GDELT provides free, no-key recent global news search.
    endpoint = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(limit),
        "sort": "DateDesc",
    }

    response = await client.get(endpoint, params=params)
    response.raise_for_status()
    payload = response.json()

    articles = payload.get("articles") or []
    return [
        {
            "title": article.get("title") or "Untitled",
            "url": article.get("url") or "",
            "source": article.get("sourcecountry") or article.get("domain") or "News",
            "published_at": article.get("seendate") or "",
        }
        for article in articles[:limit]
    ]
