import httpx
from fastapi import APIRouter, HTTPException, Query

from app.services.weather_service import (
    fetch_city_coordinates,
    fetch_current_weather,
    get_weather_fallback,
)

router = APIRouter()


@router.get("/weather")
async def get_weather(city: str = Query(..., description="City name")):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            result = await fetch_city_coordinates(client, city)
            w = await fetch_current_weather(client, result["latitude"], result["longitude"])
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Weather provider timed out") from None
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    return await get_weather_fallback(client, city)
            except (httpx.RequestError, httpx.HTTPStatusError):
                pass
        raise HTTPException(
            status_code=502,
            detail=f"Weather provider error: {exc.response.status_code}",
        ) from None
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach weather provider") from None

    return {
        "city": result["name"],
        "country": result.get("country"),
        "temperature_c": w["temperature"],
        "windspeed_kmh": w["windspeed"],
        "time": w["time"],
    }