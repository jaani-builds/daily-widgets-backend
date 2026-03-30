from calendar import monthrange
from datetime import date, timedelta
from typing import Literal


def subtract_months(input_date: date, months: int) -> date:
    total_months = input_date.year * 12 + input_date.month - 1 - months
    year = total_months // 12
    month = total_months % 12 + 1
    day = min(input_date.day, monthrange(year, month)[1])
    return date(year, month, day)


def subtract_years(input_date: date, years: int) -> date:
    year = input_date.year - years
    day = min(input_date.day, monthrange(year, input_date.month)[1])
    return date(year, input_date.month, day)


def get_period_start(end_date: date, period_value: int, period_unit: Literal["days", "months", "years"]) -> date:
    if period_unit == "days":
        return end_date - timedelta(days=period_value)
    if period_unit == "months":
        return subtract_months(end_date, period_value)
    return subtract_years(end_date, period_value)