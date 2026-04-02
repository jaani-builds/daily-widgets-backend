import httpx
from fastapi import HTTPException
from typing import Optional


async def fetch_top_news(
    client: httpx.AsyncClient,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 10,
):
    # Build optimized query: prioritize city+country > state+country > country alone
    query = ""
    if city and city.strip():
        city_clean = city.strip()
        if country and country.strip():
            country_clean = country.strip()
            # City, Country format is more specific
            query = f"{city_clean} {country_clean}"
        elif state and state.strip():
            query = f"{city_clean} {state.strip()}"
        else:
            query = city_clean
    elif state and state.strip():
        state_clean = state.strip()
        if country and country.strip():
            query = f"{state_clean} {country.strip()}"
        else:
            query = state_clean
    elif country and country.strip():
        query = country.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="At least one of city, state, or country must be provided")

    # GDELT provides free, no-key recent global news search.
    endpoint = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(limit * 3),  # Fetch more to filter duplicates
        "sort": "DateDesc",
    }

    response = await client.get(endpoint, params=params)
    response.raise_for_status()
    payload = response.json()

    articles = payload.get("articles") or []
    
    # Filter results by country if country was specified (deduplicate global results)
    filtered_articles = []
    country_lower = country.lower() if country else None
    
    for article in articles:
        if country_lower:
            source_country = (article.get("sourcecountry") or "").lower()
            # Basic matching - check if source country matches or contains the search country code
            if country_lower in source_country or source_country.startswith(country_lower[:2]):
                filtered_articles.append(article)
        else:
            filtered_articles.append(article)
        
        if len(filtered_articles) >= limit:
            break
    
    # If filtering removed too many results, fall back to unfiltered
    if not filtered_articles:
        filtered_articles = articles

    return [
        {
            "title": article.get("title") or "Untitled",
            "url": article.get("url") or "",
            "source": article.get("sourcecountry") or article.get("domain") or "News",
            "published_at": article.get("seendate") or "",
        }
        for article in filtered_articles[:limit]
    ]
