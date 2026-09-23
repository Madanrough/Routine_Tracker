"""Factual, non-medical progress insights."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.scoring import calculate_weekly_average


def weekly_insights(
    records: Sequence[Mapping[str, Any]],
    previous_records: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    if not records:
        return ["Complete a daily entry to begin seeing your weekly patterns."]
    count = len(records)
    sleep = sum(float(row.get("sleep_hours") or 0) for row in records) / count
    water = sum(float(row.get("water_liters") or 0) for row in records) / count
    exercise_days = sum(bool(row.get("exercise_done")) for row in records)
    result = [
        f"Your average sleep this week is {sleep:.1f} hours.",
        f"You exercised {exercise_days} out of {count} recorded days.",
        f"Your average water intake is {water:.1f} L.",
    ]
    if previous_records:
        difference = calculate_weekly_average(records) - calculate_weekly_average(previous_records)
        direction = "improved" if difference >= 0 else "changed"
        result.append(
            f"Your weekly score {direction} by {abs(difference):.1f} points compared with last week."
        )
    return result

