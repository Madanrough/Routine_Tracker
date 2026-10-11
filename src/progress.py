"""Weekly and monthly aggregation helpers."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Any

from src.scoring import calculate_best_streak, calculate_weekly_average, weekly_celebration_unlocked


def records_by_date(records: Sequence[dict[str, Any]]) -> dict[date, dict[str, Any]]:
    return {date.fromisoformat(str(row["log_date"])): row for row in records}


def weekly_series(records: Sequence[dict[str, Any]], monday: date) -> list[dict[str, Any]]:
    lookup = records_by_date(records)
    return [
        {
            "date": monday + timedelta(days=offset),
            "day": (monday + timedelta(days=offset)).strftime("%a"),
            "daily_score": lookup.get(monday + timedelta(days=offset), {}).get("daily_score"),
            "sleep_hours": lookup.get(monday + timedelta(days=offset), {}).get("sleep_hours"),
            "exercise_done": lookup.get(monday + timedelta(days=offset), {}).get("exercise_done"),
            "water_liters": lookup.get(monday + timedelta(days=offset), {}).get("water_liters"),
            "ate_fruit": lookup.get(monday + timedelta(days=offset), {}).get("ate_fruit"),
            "freshened_up": lookup.get(monday + timedelta(days=offset), {}).get("freshened_up"),
        }
        for offset in range(7)
    ]


def weekly_habit_stats(records: Sequence[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    """Count Yes answers and tracked days without treating legacy NULLs as No."""
    result: dict[str, tuple[int, int]] = {}
    for field in ("ate_fruit", "freshened_up"):
        tracked = [row for row in records if row.get(field) is not None]
        result[field] = (sum(row.get(field) is True for row in tracked), len(tracked))
    return result


def monthly_metrics(records: Sequence[dict[str, Any]]) -> dict[str, float | int]:
    if not records:
        return {
            "average_score": 0.0,
            "completed_days": 0,
            "exercise_days": 0,
            "average_sleep": 0.0,
            "average_water": 0.0,
            "best_streak": 0,
            "qualifying_weeks": 0,
        }
    completed = [row for row in records if float(row.get("daily_completion_score") or 0) == 100]
    count = len(records)
    grouped: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        day = date.fromisoformat(str(row["log_date"]))
        grouped[day - timedelta(days=day.weekday())].append(row)
    return {
        "average_score": calculate_weekly_average(records),
        "completed_days": len(completed),
        "exercise_days": sum(bool(row.get("exercise_done")) for row in records),
        "average_sleep": round(sum(float(row.get("sleep_hours") or 0) for row in records) / count, 1),
        "average_water": round(sum(float(row.get("water_liters") or 0) for row in records) / count, 1),
        "best_streak": calculate_best_streak(records),
        "qualifying_weeks": sum(weekly_celebration_unlocked(group) for group in grouped.values()),
    }


def latest_qualifying_week(
    records: Sequence[dict[str, Any]],
) -> tuple[date, list[dict[str, Any]]] | None:
    """Return the most recent complete Monday–Sunday week scoring 80%+."""
    grouped: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        day = date.fromisoformat(str(row["log_date"]))
        grouped[day - timedelta(days=day.weekday())].append(row)
    qualifying = [
        (monday, rows)
        for monday, rows in grouped.items()
        if weekly_celebration_unlocked(rows)
    ]
    return max(qualifying, key=lambda item: item[0]) if qualifying else None


def qualifying_weeks_in_month(
    records: Sequence[dict[str, Any]], first: date, last: date
) -> int:
    """Count qualifying weeks whose Sunday falls inside the selected month."""
    grouped: dict[date, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        day = date.fromisoformat(str(row["log_date"]))
        grouped[day - timedelta(days=day.weekday())].append(row)
    return sum(
        weekly_celebration_unlocked(rows) and first <= monday + timedelta(days=6) <= last
        for monday, rows in grouped.items()
    )
