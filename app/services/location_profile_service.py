from typing import Optional

import httpx

_DEFAULT_CURRENCY = "USD"
_FRANKFURTER_CURRENCIES_URL = "https://api.frankfurter.app/currencies"
_REST_COUNTRIES_NAME_URL = "https://restcountries.com/v3.1/name"


async def _fetch_country_data(client: httpx.AsyncClient, query: str) -> dict:
    query = (query or "").strip()
    if not query:
        return {}

    try:
        # First try an exact country-name match, then a looser lookup.
        for full_text in ("true", "false"):
            resp = await client.get(
                f"{_REST_COUNTRIES_NAME_URL}/{query}",
                params={"fields": "currencies", "fullText": full_text},
            )
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and data:
                    return data[0]
    except Exception:
        pass
    return {}


async def _fetch_supported_currencies(client: httpx.AsyncClient) -> set[str]:
    try:
        resp = await client.get(_FRANKFURTER_CURRENCIES_URL)
        if resp.status_code == 200:
            payload = resp.json()
            if isinstance(payload, dict):
                return {code.upper() for code in payload.keys()}
    except Exception:
        pass
    return set()


async def build_location_profile(
    city: str,
    country: Optional[str] = None,
):
    async with httpx.AsyncClient(timeout=8.0) as client:
        country_data = await _fetch_country_data(client, country or city)
        supported_codes = await _fetch_supported_currencies(client)

    currencies = country_data.get("currencies", {}) if isinstance(country_data, dict) else {}
    currency_code = (next(iter(currencies)) if currencies else _DEFAULT_CURRENCY).upper()

    if not supported_codes:
        # If provider metadata lookup fails, keep local currency as trend base.
        return {
            "currency_code": currency_code,
            "trend_currency_code": currency_code,
            "currency_supported_for_trends": True,
        }

    is_supported = currency_code in supported_codes
    trend_currency_code = currency_code if is_supported else _DEFAULT_CURRENCY

    return {
        "currency_code": currency_code,
        "trend_currency_code": trend_currency_code,
        "currency_supported_for_trends": is_supported,
    }
