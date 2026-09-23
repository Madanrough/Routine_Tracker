"""History presentation helpers."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from src.timezone_utils import is_editable_log_date


def relative_date_label(day: date, today: date) -> str:
    if day == today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    return day.strftime("%d %b %Y")


def edit_status(day: date, today: date) -> str:
    return "Editable" if is_editable_log_date(day, today) else "Read only"


def record_details(record: dict[str, Any]) -> list[tuple[str, str]]:
    def yes_no(value: Any) -> str:
        return "Yes" if value else "No"

    exercise = "No"
    if record.get("exercise_done"):
        exercise = f"Yes · {float(record.get('exercise_minutes') or 0):g} min"
    return [
        ("Sleep", f"{float(record.get('sleep_hours') or 0):g} h"),
        ("Exercise", exercise),
        ("1st Meal · Protein + Fibre", yes_no(record.get("meal1_protein_fibre"))),
        ("2nd Meal · Protein + Fibre", yes_no(record.get("meal2_protein_fibre"))),
        ("3rd Meal · Protein + Fibre", yes_no(record.get("meal3_protein_fibre"))),
        ("Junk / Sugary Food", yes_no(record.get("junk_sugary_food"))),
        ("Water", f"{float(record.get('water_liters') or 0):g} L"),
        ("Stress", str(record.get("stress_level") or "—").title()),
        ("Relaxation action", yes_no(record.get("stress_management"))),
        ("Mood", str(record.get("mood") or "—")),
    ]

