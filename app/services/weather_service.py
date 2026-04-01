from urllib.parse import quote

import httpx
from fastapi import HTTPException

from app.utils.time_utils import utc_timestamp


_GEOCODING_QUERY_ALIASES = {
    "united states of america": "united states",
    "usa": "united states",
    "u.s.a.": "united states",
}


def _normalize_location_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _build_geocoding_queries(query: str) -> list[str]:
    normalized = _normalize_location_text(query)
    if not normalized:
        return []

    alias = _GEOCODING_QUERY_ALIASES.get(normalized)
    if alias:
        return [alias, query.strip()]
    return [query.strip()]


def _pick_best_geocoding_result(results: list[dict], query: str) -> dict:
    normalized_query = _normalize_location_text(query)
    if not results:
        return {}

    # Prefer exact country-name and city-name matches before fuzzy candidates.
    for result in results:
        if _normalize_location_text(result.get("country", "")) == normalized_query:
            return result

    for result in results:
        if _normalize_location_text(result.get("name", "")) == normalized_query:
            return result

    for result in results:
        country = _normalize_location_text(result.get("country", ""))
        name = _normalize_location_text(result.get("name", ""))
        admin1 = _normalize_location_text(result.get("admin1", ""))
        if normalized_query in {country, name, admin1}:
            return result

    return results[0]


async def fetch_city_coordinates(client: httpx.AsyncClient, city: str):
    for query in _build_geocoding_queries(city):
        response = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 10, "language": "en"},
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        if results:
            return _pick_best_geocoding_result(results, city)

    raise HTTPException(status_code=404, detail=f"City '{city}' not found")


async def fetch_current_weather(client: httpx.AsyncClient, latitude: float, longitude: float):
    response = await client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "timezone": "auto",
        },
    )
    response.raise_for_status()
    payload = response.json()
    current_weather = payload.get("current_weather")
    if not current_weather:
        raise HTTPException(
            status_code=502,
            detail="Weather provider did not return current weather data",
        )
    return {
        "current_weather": current_weather,
        "timezone": payload.get("timezone"),
        "timezone_abbreviation": payload.get("timezone_abbreviation"),
    }


async def get_weather_fallback(client: httpx.AsyncClient, city: str):
    response = await client.get(f"https://wttr.in/{quote(city)}", params={"format": "j1"})
    response.raise_for_status()
    payload = response.json()
    current = payload.get("current_condition", [{}])[0]
    if not current:
        raise HTTPException(status_code=502, detail="Fallback weather provider returned no data")

    temp_raw = current.get("temp_C")
    wind_raw = current.get("windspeedKmph")

    return {
        "city": city,
        "country": None,
        "temperature_c": float(temp_raw) if temp_raw is not None else None,
        "windspeed_kmh": float(wind_raw) if wind_raw is not None else None,
        "time": utc_timestamp(),
        "local_time": utc_timestamp(),
        "timezone": "UTC",
    }