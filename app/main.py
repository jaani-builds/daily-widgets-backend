from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
import httpx
from urllib.parse import quote

app = FastAPI()


async def get_weather_fallback(client: httpx.AsyncClient, city: str):
    # Fallback provider for rate-limit scenarios on the primary API.
    fallback = await client.get(f"https://wttr.in/{quote(city)}", params={"format": "j1"})
    fallback.raise_for_status()
    payload = fallback.json()
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
        "time": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/time")
def get_time():
    return {"time": datetime.utcnow().isoformat() + "Z"}


@app.get("/weather")
async def get_weather(city: str = Query(..., description="City name")):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
            )
            geo.raise_for_status()
            geo_data = geo.json()
            if not geo_data.get("results"):
                raise HTTPException(status_code=404, detail=f"City '{city}' not found")

            result = geo_data["results"][0]
            lat, lon = result["latitude"], result["longitude"]

            weather = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current_weather": True,
                },
            )
            weather.raise_for_status()
            weather_data = weather.json()
            w = weather_data.get("current_weather")
            if not w:
                raise HTTPException(
                    status_code=502,
                    detail="Weather provider did not return current weather data",
                )
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
        "time": w["time"]
    }
