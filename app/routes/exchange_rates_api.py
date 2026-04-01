from datetime import datetime, timezone
from typing import Literal, Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.services.exchange_rate_service import (
    fetch_historical_exchange_rates,
    fetch_latest_exchange_rate,
)
from app.utils.date_utils import get_period_start

router = APIRouter()


def to_utc_minute_timestamp(value: datetime) -> str:
    return value.replace(second=0, microsecond=0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/exchange-rates")
async def get_exchange_rates(
    base: str = Query(..., min_length=3, max_length=3, description="Base currency code, for example USD"),
    target: str = Query(..., min_length=3, max_length=3, description="Target currency code, for example EUR"),
    period_value: Optional[int] = Query(
        None,
        ge=1,
        le=525600,
        description="Historical lookback amount. Use together with period_unit.",
    ),
    period_unit: Optional[Literal["minutes", "days", "months", "years"]] = Query(
        None,
        description="Historical lookback unit. Use together with period_value.",
    ),
):
    base = base.upper()
    target = target.upper()

    if not base.isalpha() or not target.isalpha():
        raise HTTPException(status_code=400, detail="Currency codes must contain only letters")

    if (period_value is None) != (period_unit is None):
        raise HTTPException(
            status_code=400,
            detail="period_value and period_unit must be provided together",
        )

    end_at = datetime.utcnow().replace(second=0, microsecond=0)
    end_date = end_at.date()

    if base == target:
        if period_value is None:
            return {"base": base, "target": target, "date": end_date.isoformat(), "rate": 1.0}

        start_at = get_period_start(end_at, period_value, period_unit)
        start_date = start_at.date()
        return {
            "base": base,
            "target": target,
            "period": {
                "value": period_value,
                "unit": period_unit,
                "start_at": to_utc_minute_timestamp(start_at),
                "end_at": to_utc_minute_timestamp(end_at),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "rates": [
                {"date": start_date.isoformat(), "rate": 1.0},
                {"date": end_date.isoformat(), "rate": 1.0},
            ],
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            if period_value is None:
                payload = await fetch_latest_exchange_rate(client, base, target)
                rate = payload.get("rates", {}).get(target)
                if rate is None:
                    raise HTTPException(status_code=404, detail="Exchange rate not found")

                return {
                    "base": payload.get("base", base),
                    "target": target,
                    "date": payload.get("date"),
                    "rate": rate,
                }

            start_at = get_period_start(end_at, period_value, period_unit)
            start_date = start_at.date()
            payload = await fetch_historical_exchange_rates(client, base, target, start_date, end_date)
            raw_rates = payload.get("rates", {})
            history = [
                {"date": rate_date, "rate": values[target]}
                for rate_date, values in sorted(raw_rates.items())
                if target in values
            ]
            if not history:
                raise HTTPException(status_code=404, detail="Historical exchange rates not found")

            return {
                "base": payload.get("base", base),
                "target": target,
                "period": {
                    "value": period_value,
                    "unit": period_unit,
                    "start_at": to_utc_minute_timestamp(start_at),
                    "end_at": to_utc_minute_timestamp(end_at),
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "rates": history,
            }
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Exchange rate provider timed out") from None
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Exchange rate provider error: {exc.response.status_code}",
        ) from None
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not reach exchange rate provider") from None