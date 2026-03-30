from calendar import monthrange
from datetime import datetime, timedelta
from typing import Literal


def subtract_months(input_datetime: datetime, months: int) -> datetime:
    total_months = input_datetime.year * 12 + input_datetime.month - 1 - months
    year = total_months // 12
    month = total_months % 12 + 1
    day = min(input_datetime.day, monthrange(year, month)[1])
    return input_datetime.replace(year=year, month=month, day=day)


def subtract_years(input_datetime: datetime, years: int) -> datetime:
    year = input_datetime.year - years
    day = min(input_datetime.day, monthrange(year, input_datetime.month)[1])
    return input_datetime.replace(year=year, day=day)


def get_period_start(
    end_datetime: datetime,
    period_value: int,
    period_unit: Literal["days", "months", "years"],
) -> datetime:
    if period_unit == "days":
        return end_datetime - timedelta(days=period_value)
    if period_unit == "months":
        return subtract_months(end_datetime, period_value)
    return subtract_years(end_datetime, period_value)