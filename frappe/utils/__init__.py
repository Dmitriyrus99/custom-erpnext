"""Utility helpers used by the frappe test double."""

from __future__ import annotations

import datetime as _dt
from typing import Any


def now_datetime() -> _dt.datetime:
        return _dt.datetime.now()


def now() -> _dt.datetime:
        return now_datetime()


def nowdate() -> str:
        return now_datetime().date().isoformat()


def today() -> str:
        return nowdate()


def add_to_date(
        base: _dt.datetime | str,
        *,
        years: int = 0,
        months: int = 0,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
) -> _dt.datetime:
        dt = _ensure_datetime(base)
        # Month arithmetic is intentionally very small in scope; the tests only
        # rely on the ability to add hours so we fall back to naive month
        # handling for completeness.
        month = dt.month - 1 + months
        year = dt.year + years + month // 12
        month = month % 12 + 1
        day = min(dt.day, _days_in_month(year, month))
        dt = dt.replace(year=year, month=month, day=day)
        dt += _dt.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return dt


def add_days(base: _dt.datetime | str, count: int) -> _dt.datetime:
        return _ensure_datetime(base) + _dt.timedelta(days=count)


def getdate(value: _dt.datetime | _dt.date | str) -> _dt.date:
        if isinstance(value, _dt.date) and not isinstance(value, _dt.datetime):
                return value
        if isinstance(value, str):
                return _ensure_datetime(value).date()
        return value.date()


def get_datetime(value: _dt.datetime | str) -> _dt.datetime:
        return _ensure_datetime(value)


def _ensure_datetime(value: _dt.datetime | str) -> _dt.datetime:
        if isinstance(value, _dt.datetime):
                return value
        if isinstance(value, str):
                try:
                        return _dt.datetime.fromisoformat(value)
                except ValueError:
                        pass
                return _dt.datetime.strptime(value, "%Y-%m-%d")
        raise TypeError(f"Unsupported datetime value: {value!r}")


def _days_in_month(year: int, month: int) -> int:
        if month == 12:
                next_month = _dt.date(year + 1, 1, 1)
        else:
                next_month = _dt.date(year, month + 1, 1)
        current = _dt.date(year, month, 1)
        return (next_month - current).days

