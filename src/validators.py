"""Server-side validation for daily entries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.scoring import missing_required_fields

FIELD_LABELS = {
    "sleep_hours": "Sleep",
    "exercise_done": "Exercise",
    "exercise_minutes": "Exercise minutes",
    "meal1_protein_fibre": "1st Meal",
    "meal2_protein_fibre": "2nd Meal",
    "meal3_protein_fibre": "3rd Meal",
    "junk_sugary_food": "Junk / Sugary Food",
    "ate_fruit": "Fruit",
    "water_liters": "Water",
    "freshened_up": "Freshened up",
    "stress_level": "Stress level",
    "stress_management": "Stress management",
    "mood": "Mood",
}


class ValidationError(ValueError):
    """Raised when a daily record fails application validation."""


def validate_daily_record(values: Mapping[str, Any]) -> None:
    missing = missing_required_fields(values)
    if missing:
        labels = ", ".join(FIELD_LABELS.get(name, name) for name in missing)
        raise ValidationError(f"Please complete: {labels}.")

    boolean_fields = (
        "exercise_done",
        "meal1_protein_fibre",
        "meal2_protein_fibre",
        "meal3_protein_fibre",
        "junk_sugary_food",
        "ate_fruit",
        "freshened_up",
        "stress_management",
    )
    for name in boolean_fields:
        if not isinstance(values[name], bool):
            raise ValidationError(f"{FIELD_LABELS[name]} must be answered YES or NO.")

    ranges = {
        "sleep_hours": (0.0, 24.0),
        "water_liters": (0.0, 10.0),
    }
    if values.get("exercise_done"):
        ranges["exercise_minutes"] = (0.0, 300.0)
    for name, (minimum, maximum) in ranges.items():
        try:
            value = float(values[name])
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"{FIELD_LABELS[name]} must be a number.") from exc
        if not minimum <= value <= maximum:
            raise ValidationError(
                f"{FIELD_LABELS[name]} must be between {minimum:g} and {maximum:g}."
            )

    if values["stress_level"] not in {"LOW", "MODERATE", "HIGH"}:
        raise ValidationError("Please choose a valid stress level.")
    if values["mood"] not in {"Happy", "Okay", "Low"}:
        raise ValidationError("Please choose a valid mood.")
    note = values.get("daily_note") or ""
    if not isinstance(note, str):
        raise ValidationError("Daily note must be text.")
    if len(note) > 2000:
        raise ValidationError("Daily note must be 2,000 characters or fewer.")
