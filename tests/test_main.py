import pytest
from httpx import AsyncClient, ASGITransport

import app.routes.exchange_rates_api as exchange_rates_api
import app.routes.location_profile_api as location_profile_api
import app.routes.news_api as news_api
from app.main import app
from app.services.weather_service import _build_geocoding_queries, _pick_best_geocoding_result


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


def test_pick_best_geocoding_result_prefers_exact_country_match():
    results = [
        {"name": "Iranshahr", "country": "Iran", "latitude": 27.2, "longitude": 60.7},
        {"name": "Tehran", "country": "Iran", "latitude": 35.7, "longitude": 51.4},
    ]

    picked = _pick_best_geocoding_result(results, "iran")
    assert picked["country"] == "Iran"


def test_pick_best_geocoding_result_handles_multi_word_country_name():
    results = [
        {
            "name": "United",
            "country": "Liberia",
            "latitude": 6.3,
            "longitude": -10.7,
        },
        {
            "name": "Washington",
            "country": "United States of America",
            "latitude": 38.9,
            "longitude": -77.0,
        },
    ]

    picked = _pick_best_geocoding_result(results, "united states of america")
    assert picked["country"] == "United States of America"


def test_build_geocoding_queries_adds_united_states_alias():
    queries = _build_geocoding_queries("united states of america")
    assert queries[0] == "united states"
    assert "united states of america" in queries


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


@pytest.mark.asyncio
async def test_get_exchange_rate_historical_minutes(monkeypatch):
    async def mock_fetch_historical_exchange_rates(client, base, target, start_date, end_date):
        assert base == "USD"
        assert target == "EUR"
        assert start_date <= end_date
        return {
            "amount": 1.0,
            "base": "USD",
            "rates": {
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
            params={"base": "USD", "target": "EUR", "period_value": 90, "period_unit": "minutes"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["period"]["unit"] == "minutes"
    assert "start_at" in data["period"]
    assert "end_at" in data["period"]


@pytest.mark.asyncio
async def test_get_news_success(monkeypatch):
    async def mock_fetch_top_news(client, city=None, state=None, country=None, limit=10):
        assert city == "Dublin"
        assert state is None
        assert country == "Ireland"
        assert limit == 5
        return [
            {
                "title": "Headline 1",
                "url": "https://example.com/1",
                "source": "News",
                "published_at": "2026-03-30T10:00:00Z",
            }
        ]

    monkeypatch.setattr(news_api, "fetch_top_news", mock_fetch_top_news)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/news", params={"city": "Dublin", "country": "Ireland", "limit": 5})

    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Dublin"
    assert data["country"] == "Ireland"
    assert data["count"] == 1
    assert data["articles"][0]["title"] == "Headline 1"


@pytest.mark.asyncio
async def test_get_news_missing_city():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/news")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_news_by_state_only(monkeypatch):
    async def mock_fetch_top_news(client, city=None, state=None, country=None, limit=10):
        assert city is None
        assert state == "California"
        assert country == "United States"
        assert limit == 3
        return [
            {
                "title": "Headline 2",
                "url": "https://example.com/2",
                "source": "News",
                "published_at": "2026-03-30T11:00:00Z",
            }
        ]

    monkeypatch.setattr(news_api, "fetch_top_news", mock_fetch_top_news)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/news", params={"state": "California", "country": "United States", "limit": 3})

    assert response.status_code == 200
    data = response.json()
    assert data["city"] is None
    assert data["state"] == "California"
    assert data["country"] == "United States"
    assert data["count"] == 1


@pytest.mark.asyncio
async def test_get_location_profile_defaults(monkeypatch):
    async def mock_build_location_profile(city, country=None):
        assert city == "Dublin"
        assert country == "Ireland"
        return {"currency_code": "EUR"}

    monkeypatch.setattr(location_profile_api, "build_location_profile", mock_build_location_profile)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/location-profile", params={"city": "Dublin", "country": "Ireland"})

    assert response.status_code == 200
    data = response.json()
    assert data["currency_code"] == "EUR"
    assert "gifs" not in data


@pytest.mark.asyncio
async def test_get_location_profile_missing_city():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/location-profile")

    assert response.status_code == 422
