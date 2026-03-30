from datetime import date

import httpx


async def fetch_latest_exchange_rate(client: httpx.AsyncClient, base: str, target: str):
    response = await client.get(
        "https://api.frankfurter.app/latest",
        params={"from": base, "to": target},
    )
    response.raise_for_status()
    return response.json()


async def fetch_historical_exchange_rates(
    client: httpx.AsyncClient,
    base: str,
    target: str,
    start_date: date,
    end_date: date,
):
    response = await client.get(
        f"https://api.frankfurter.app/{start_date.isoformat()}..{end_date.isoformat()}",
        params={"from": base, "to": target},
    )
    response.raise_for_status()
    return response.json()