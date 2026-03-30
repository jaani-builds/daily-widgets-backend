from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
import httpx

app = FastAPI()


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
