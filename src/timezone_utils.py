"""India-local date and time helpers used by every date-sensitive feature."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

INDIA_TZ = ZoneInfo("Asia/Kolkata")


def india_now() -> datetime:
    """Return the current timezone-aware time in India."""
    return datetime.now(INDIA_TZ)


def india_today(now: datetime | None = None) -> date:
    """Return the current India-local calendar date."""
    instant = now or india_now()
    if instant.tzinfo is None:
        instant = instant.replace(tzinfo=INDIA_TZ)
    return instant.astimezone(INDIA_TZ).date()


def week_bounds(day: date | None = None) -> tuple[date, date]:
    """Return Monday and Sunday for the India-local week containing ``day``."""
    target = day or india_today()
    monday = target - timedelta(days=target.weekday())
    return monday, monday + timedelta(days=6)


def month_bounds(day: date | None = None) -> tuple[date, date]:
    """Return first and last date of the month containing ``day``."""
    target = day or india_today()
    first = target.replace(day=1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, next_month - timedelta(days=1)


def is_editable_log_date(log_date: date, today: date | None = None) -> bool:
    """Records are editable only for today and yesterday in India time."""
    local_today = today or india_today()
    return local_today - timedelta(days=1) <= log_date <= local_today

