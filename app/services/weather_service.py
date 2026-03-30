from urllib.parse import quote

import httpx
from fastapi import HTTPException

from app.utils.time_utils import utc_timestamp


async def fetch_city_coordinates(client: httpx.AsyncClient, city: str):
    response = await client.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
    )
    response.raise_for_status()
    payload = response.json()
    if not payload.get("results"):
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")
    return payload["results"][0]


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