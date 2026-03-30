import pytest
from httpx import AsyncClient, ASGITransport

import app.routes.exchange_rates_api as exchange_rates_api
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
    assert "local_time" in data
    assert "timezone" in data


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


@pytest.mark.asyncio
async def test_get_exchange_rate_latest(monkeypatch):
    async def mock_fetch_latest_exchange_rate(client, base, target):
        assert base == "USD"
        assert target == "EUR"
        return {"amount": 1.0, "base": "USD", "date": "2026-03-30", "rates": {"EUR": 0.92}}

    monkeypatch.setattr(exchange_rates_api, "fetch_latest_exchange_rate", mock_fetch_latest_exchange_rate)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/exchange-rates", params={"base": "usd", "target": "eur"})

    assert response.status_code == 200
    data = response.json()
    assert data == {"base": "USD", "target": "EUR", "date": "2026-03-30", "rate": 0.92}


@pytest.mark.asyncio
async def test_get_exchange_rate_historical(monkeypatch):
    async def mock_fetch_historical_exchange_rates(client, base, target, start_date, end_date):
        assert base == "USD"
        assert target == "EUR"
        assert start_date <= end_date
        return {
            "amount": 1.0,
            "base": "USD",
            "rates": {
                "2026-03-28": {"EUR": 0.91},
                "2026-03-29": {"EUR": 0.92},
                "2026-03-30": {"EUR": 0.93},
            },
        }

    monkeypatch.setattr(
        exchange_rates_api,
        "fetch_historical_exchange_rates",
        mock_fetch_historical_exchange_rates,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/exchange-rates",
            params={"base": "USD", "target": "EUR", "period_value": 7, "period_unit": "days"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["base"] == "USD"
    assert data["target"] == "EUR"
    assert data["period"]["value"] == 7
    assert data["period"]["unit"] == "days"
    assert "start_at" in data["period"]
    assert "end_at" in data["period"]
    assert len(data["rates"]) == 3
    assert data["rates"][0] == {"date": "2026-03-28", "rate": 0.91}


@pytest.mark.asyncio
async def test_get_exchange_rate_requires_complete_period():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/exchange-rates", params={"base": "USD", "target": "EUR", "period_unit": "days"})

    assert response.status_code == 400
    assert response.json()["detail"] == "period_value and period_unit must be provided together"
