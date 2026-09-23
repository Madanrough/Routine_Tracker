"""Pure, testable scoring and aggregation rules.

Daily scores total exactly 100 points. Component weights are sleep 20%,
exercise 20%, food 25%, water 15%, stress-management behavior 10%, and
daily completion 10%. Mood and reported stress level are descriptive only.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any

SCORE_WEIGHTS = {
    "sleep": 0.20,
    "exercise": 0.20,
    "food": 0.25,
    "water": 0.15,
    "stress_management": 0.10,
    "daily_completion": 0.10,
}

REQUIRED_FIELDS = (
    "sleep_hours",
    "exercise_done",
    "meal1_protein_fibre",
    "meal2_protein_fibre",
    "meal3_protein_fibre",
    "junk_sugary_food",
    "water_liters",
    "stress_level",
    "stress_management",
    "mood",
)


def _bounded_ratio(value: float, target: float) -> float:
    return round(min(max(float(value), 0.0) / target * 100.0, 100.0), 2)


def calculate_sleep_score(sleep_hours: float) -> float:
    return _bounded_ratio(sleep_hours, 8.0)


def calculate_exercise_score(exercise_done: bool, exercise_minutes: float | None = None) -> float:
    if not exercise_done:
        return 0.0
    return _bounded_ratio(exercise_minutes or 0.0, 30.0)


def calculate_food_score(
    meal1_protein_fibre: bool,
    meal2_protein_fibre: bool,
    meal3_protein_fibre: bool,
    junk_sugary_food: bool,
) -> tuple[float, float, float]:
    """Return meal quality, junk control, and combined food scores."""
    meal_quality = round(
        sum(100.0 if value else 0.0 for value in (
            meal1_protein_fibre,
            meal2_protein_fibre,
            meal3_protein_fibre,
        )) / 3.0,
        2,
    )
    junk_control = 0.0 if junk_sugary_food else 100.0
    food = round(meal_quality * 0.8 + junk_control * 0.2, 2)
    return meal_quality, junk_control, food


def calculate_water_score(water_liters: float) -> float:
    return _bounded_ratio(water_liters, 2.5)


def calculate_stress_management_score(stress_management: bool) -> float:
    return 100.0 if stress_management else 0.0


def missing_required_fields(values: Mapping[str, Any]) -> list[str]:
    """List required fields missing from a proposed daily record."""
    missing = [field for field in REQUIRED_FIELDS if values.get(field) is None]
    if values.get("exercise_done") is True and values.get("exercise_minutes") is None:
        missing.append("exercise_minutes")
    return missing


def calculate_daily_completion_score(values: Mapping[str, Any]) -> float:
    return 0.0 if missing_required_fields(values) else 100.0


def calculate_daily_score(
    *,
    sleep_score: float,
    exercise_score: float,
    food_score: float,
    water_score: float,
    stress_management_score: float,
    daily_completion_score: float,
) -> float:
    components = {
        "sleep": sleep_score,
        "exercise": exercise_score,
        "food": food_score,
        "water": water_score,
        "stress_management": stress_management_score,
        "daily_completion": daily_completion_score,
    }
    return round(sum(float(components[name]) * weight for name, weight in SCORE_WEIGHTS.items()), 2)


def score_daily_record(values: Mapping[str, Any]) -> dict[str, float]:
    """Calculate every stored score from raw daily inputs."""
    sleep_score = calculate_sleep_score(float(values["sleep_hours"]))
    exercise_score = calculate_exercise_score(
        bool(values["exercise_done"]), values.get("exercise_minutes")
    )
    meal_quality, junk_control, food_score = calculate_food_score(
        bool(values["meal1_protein_fibre"]),
        bool(values["meal2_protein_fibre"]),
        bool(values["meal3_protein_fibre"]),
        bool(values["junk_sugary_food"]),
    )
    water_score = calculate_water_score(float(values["water_liters"]))
    stress_score = calculate_stress_management_score(bool(values["stress_management"]))
    completion_score = calculate_daily_completion_score(values)
    daily_score = calculate_daily_score(
        sleep_score=sleep_score,
        exercise_score=exercise_score,
        food_score=food_score,
        water_score=water_score,
        stress_management_score=stress_score,
        daily_completion_score=completion_score,
    )
    return {
        "sleep_score": sleep_score,
        "exercise_score": exercise_score,
        "meal_quality_score": meal_quality,
        "junk_control_score": junk_control,
        "food_score": food_score,
        "water_score": water_score,
        "stress_management_score": stress_score,
        "daily_completion_score": completion_score,
        "daily_score": daily_score,
    }


def calculate_weekly_average(records: Sequence[Mapping[str, Any]]) -> float:
    scores = [float(record["daily_score"]) for record in records if record.get("daily_score") is not None]
    return round(sum(scores) / len(scores), 2) if scores else 0.0


def weekly_celebration_unlocked(records: Sequence[Mapping[str, Any]]) -> bool:
    """Unlock only for seven distinct complete dates with an average >= 80%."""
    completed = {
        str(record.get("log_date")): record
        for record in records
        if float(record.get("daily_completion_score") or 0) == 100.0
    }
    if len(completed) != 7:
        return False
    dates = sorted(date.fromisoformat(value) for value in completed)
    is_monday_to_sunday = dates[0].weekday() == 0 and all(
        current == dates[0] + timedelta(days=index)
        for index, current in enumerate(dates)
    )
    return is_monday_to_sunday and calculate_weekly_average(list(completed.values())) >= 80.0


def calculate_current_streak(records: Sequence[Mapping[str, Any]], today: date) -> int:
    """Count consecutive complete dates ending today, or yesterday if today is pending."""
    completed_dates = {
        date.fromisoformat(str(record["log_date"]))
        for record in records
        if float(record.get("daily_completion_score") or 0) == 100.0
    }
    cursor = today if today in completed_dates else today - timedelta(days=1)
    streak = 0
    while cursor in completed_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def calculate_best_streak(records: Sequence[Mapping[str, Any]]) -> int:
    dates = sorted({
        date.fromisoformat(str(record["log_date"]))
        for record in records
        if float(record.get("daily_completion_score") or 0) == 100.0
    })
    best = current = 0
    previous: date | None = None
    for day in dates:
        current = current + 1 if previous and day == previous + timedelta(days=1) else 1
        best = max(best, current)
        previous = day
    return best
