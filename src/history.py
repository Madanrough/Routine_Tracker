"""History presentation helpers."""

from __future__ import annotations

from datetime import date, timedelta
from collections.abc import Mapping, Sequence
from typing import Any

from src.scoring import calculate_weekly_average
from src.timezone_utils import is_editable_log_date


def relative_date_label(day: date, today: date) -> str:
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    return day.strftime("%d %b %Y")


def edit_status(day: date, today: date) -> str:
    return "Editable" if is_editable_log_date(day, today) else "Read only"


def history_summary(
    records: Sequence[Mapping[str, Any]],
) -> tuple[int, float | None, Mapping[str, Any] | None]:
    """Count entries and summarize only records with a stored daily score."""
    scored = [row for row in records if row.get("daily_score") is not None]
    average = calculate_weekly_average(scored) if scored else None
    best = max(scored, key=lambda row: float(row["daily_score"])) if scored else None
    return len(records), average, best


def record_details(record: dict[str, Any]) -> list[tuple[str, str]]:
    def yes_no(value: Any) -> str:
        if value is None:
            return "Not tracked"
        return "Yes" if value else "No"

    def measured(field: str, unit: str) -> str:
        value = record.get(field)
        return f"{float(value):g} {unit}" if value is not None else "Not tracked"

    exercise_done = record.get("exercise_done")
    if exercise_done is None:
        exercise = "Not tracked"
    elif exercise_done:
        minutes = record.get("exercise_minutes")
        exercise = f"Yes · {float(minutes):g} min" if minutes is not None else "Yes"
    else:
        exercise = "No"
    return [
        ("Sleep", measured("sleep_hours", "h")),
        ("Exercise", exercise),
        ("1st Meal · Protein + Fibre", yes_no(record.get("meal1_protein_fibre"))),
        ("2nd Meal · Protein + Fibre", yes_no(record.get("meal2_protein_fibre"))),
        ("3rd Meal · Protein + Fibre", yes_no(record.get("meal3_protein_fibre"))),
        ("Junk / Sugary Food", yes_no(record.get("junk_sugary_food"))),
        ("Fruit", yes_no(record.get("ate_fruit"))),
        ("Water", measured("water_liters", "L")),
        ("Freshened up after waking", yes_no(record.get("freshened_up"))),
        ("Stress", str(record["stress_level"]).title() if record.get("stress_level") is not None else "Not tracked"),
        ("Relaxation action", yes_no(record.get("stress_management"))),
        ("Mood", str(record["mood"]) if record.get("mood") is not None else "Not tracked"),
    ]

