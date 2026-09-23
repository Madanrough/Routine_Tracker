from datetime import date

import pytest

from src.scoring import (
    SCORE_WEIGHTS,
    calculate_daily_score,
    calculate_exercise_score,
    calculate_food_score,
    calculate_sleep_score,
    calculate_stress_management_score,
    calculate_water_score,
    score_daily_record,
    weekly_celebration_unlocked,
)


@pytest.mark.parametrize(("hours", "expected"), [(4, 50), (6, 75), (8, 100), (10, 100)])
def test_sleep_score(hours, expected):
    assert calculate_sleep_score(hours) == expected


@pytest.mark.parametrize(("minutes", "expected"), [(0, 0), (15, 50), (30, 100), (45, 100)])
def test_exercise_score(minutes, expected):
    assert calculate_exercise_score(True, minutes) == expected


def test_no_exercise_always_scores_zero():
    assert calculate_exercise_score(False, 300) == 0


@pytest.mark.parametrize(("litres", "expected"), [(1.25, 50), (2.0, 80), (2.5, 100), (3.0, 100)])
def test_water_score(litres, expected):
    assert calculate_water_score(litres) == expected


def test_food_score_all_meals_and_no_junk():
    meal, junk, food = calculate_food_score(True, True, True, False)
    assert meal == 100
    assert junk == 100
    assert food == 100


def test_junk_is_not_double_counted():
    _, _, food = calculate_food_score(True, True, True, True)
    daily = calculate_daily_score(
        sleep_score=0,
        exercise_score=0,
        food_score=food,
        water_score=0,
        stress_management_score=0,
        daily_completion_score=0,
    )
    assert food == 80
    assert daily == 20


def complete_record(**overrides):
    values = {
        "sleep_hours": 8,
        "exercise_done": True,
        "exercise_minutes": 30,
        "meal1_protein_fibre": True,
        "meal2_protein_fibre": True,
        "meal3_protein_fibre": True,
        "junk_sugary_food": False,
        "water_liters": 2.5,
        "stress_level": "HIGH",
        "stress_management": True,
        "mood": "Happy",
        "daily_note": "",
    }
    values.update(overrides)
    return values


def test_high_stress_does_not_reduce_score_when_relaxation_done():
    high = score_daily_record(complete_record(stress_level="HIGH"))
    low = score_daily_record(complete_record(stress_level="LOW"))
    assert calculate_stress_management_score(True) == 100
    assert high["daily_score"] == low["daily_score"] == 100


def test_mood_does_not_change_daily_score():
    happy = score_daily_record(complete_record(mood="Happy"))
    low = score_daily_record(complete_record(mood="Low"))
    assert happy["daily_score"] == low["daily_score"]


def test_daily_weights_total_exactly_100_percent():
    assert sum(SCORE_WEIGHTS.values()) == pytest.approx(1.0)


def week_records(scores, complete=True):
    return [
        {
            "log_date": date(2026, 9, 14 + index).isoformat(),
            "daily_score": score,
            "daily_completion_score": 100 if complete else 0,
        }
        for index, score in enumerate(scores)
    ]


def test_full_week_at_or_above_80_unlocks():
    assert weekly_celebration_unlocked(week_records([80] * 7))


@pytest.mark.parametrize("score", [85, 100])
def test_full_week_above_threshold_unlocks(score):
    assert weekly_celebration_unlocked(week_records([score] * 7))


def test_six_days_at_90_does_not_unlock():
    assert not weekly_celebration_unlocked(week_records([90] * 6))


def test_full_week_below_80_does_not_unlock():
    assert not weekly_celebration_unlocked(week_records([79.9] * 7))


def test_incomplete_days_do_not_unlock():
    assert not weekly_celebration_unlocked(week_records([100] * 7, complete=False))


def test_seven_dates_that_are_not_monday_to_sunday_do_not_unlock():
    records = week_records([100] * 7)
    records[0]["log_date"] = "2026-09-13"
    assert not weekly_celebration_unlocked(records)
