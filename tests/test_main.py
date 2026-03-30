import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_time():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/time")
    assert response.status_code == 200
    data = response.json()
    assert "time" in data
    assert data["time"].endswith("Z")


@pytest.mark.asyncio
async def test_get_weather_valid_city():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/weather", params={"city": "London"})
    assert response.status_code == 200
    data = response.json()
    assert "london" in data["city"].lower()
    assert "temperature_c" in data
    assert "windspeed_kmh" in data
    assert "time" in data


@pytest.mark.asyncio
async def test_get_weather_invalid_city():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/weather", params={"city": "NotARealCityXYZ123"})
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_weather_missing_city():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/weather")
    assert response.status_code == 422  # FastAPI validation error
