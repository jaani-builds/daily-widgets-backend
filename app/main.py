from fastapi import FastAPI, Query
from datetime import datetime
import httpx

app = FastAPI()


@app.get("/time")
def get_time():
    return {"time": datetime.utcnow().isoformat() + "Z"}


@app.get("/weather")
async def get_weather(city: str = Query(..., description="City name")):
    async with httpx.AsyncClient() as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1}
        )
        geo_data = geo.json()
        if not geo_data.get("results"):
            return {"error": f"City '{city}' not found"}

        result = geo_data["results"][0]
        lat, lon = result["latitude"], result["longitude"]

        weather = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True
            }
        )
        w = weather.json()["current_weather"]

    return {
        "city": result["name"],
        "country": result.get("country"),
        "temperature_c": w["temperature"],
        "windspeed_kmh": w["windspeed"],
        "time": w["time"]
    }
