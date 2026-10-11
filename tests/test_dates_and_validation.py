from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from src.scoring import calculate_best_streak, calculate_current_streak
from src.messages import message_for_day
from src.timezone_utils import india_today, is_editable_log_date, week_bounds
from src.validators import ValidationError, validate_daily_record


def valid_record():
    return {
        "sleep_hours": 7.5,
        "exercise_done": False,
        "exercise_minutes": 0,
        "meal1_protein_fibre": True,
        "meal2_protein_fibre": True,
        "meal3_protein_fibre": False,
        "junk_sugary_food": False,
        "ate_fruit": True,
        "water_liters": 2.2,
        "freshened_up": True,
        "stress_level": "MODERATE",
        "stress_management": True,
        "mood": "Okay",
        "daily_note": "A normal day",
    }


def test_india_date_not_utc_date():
    utc = datetime(2026, 9, 18, 20, 0, tzinfo=ZoneInfo("UTC"))
    assert india_today(utc) == date(2026, 9, 19)


def test_monday_sunday_week():
    assert week_bounds(date(2026, 9, 19)) == (date(2026, 9, 14), date(2026, 9, 20))


def test_history_edit_window():
    today = date(2026, 9, 19)
    assert is_editable_log_date(today, today)
    assert is_editable_log_date(date(2026, 9, 18), today)
    assert not is_editable_log_date(date(2026, 9, 17), today)
    assert not is_editable_log_date(date(2026, 9, 20), today)


@pytest.mark.parametrize(
    ("field", "value"),
    [("sleep_hours", -1), ("sleep_hours", 25), ("water_liters", -0.1), ("water_liters", 11)],
)
def test_out_of_range_values_rejected(field, value):
    record = valid_record()
    record[field] = value
    with pytest.raises(ValidationError):
        validate_daily_record(record)


def test_missing_exercise_minutes_when_yes_is_rejected():
    record = valid_record()
    record["exercise_done"] = True
    record["exercise_minutes"] = None
    with pytest.raises(ValidationError):
        validate_daily_record(record)


@pytest.mark.parametrize(
    "field",
    [
        "exercise_done",
        "meal1_protein_fibre",
        "meal2_protein_fibre",
        "meal3_protein_fibre",
        "junk_sugary_food",
        "ate_fruit",
        "freshened_up",
        "stress_management",
    ],
)
def test_yes_no_fields_require_real_booleans(field):
    record = valid_record()
    record[field] = "YES"
    with pytest.raises(ValidationError):
        validate_daily_record(record)


def test_daily_note_must_be_text():
    record = valid_record()
    record["daily_note"] = 123
    with pytest.raises(ValidationError):
        validate_daily_record(record)


@pytest.mark.parametrize("field", ["ate_fruit", "freshened_up"])
def test_new_check_ins_require_explicit_answers(field):
    record = valid_record()
    record[field] = None
    with pytest.raises(ValidationError, match="Please complete"):
        validate_daily_record(record)


def test_streak_logic_uses_consecutive_complete_dates():
    records = [
        {"log_date": "2026-09-19", "daily_completion_score": 100},
        {"log_date": "2026-09-18", "daily_completion_score": 100},
        {"log_date": "2026-09-17", "daily_completion_score": 100},
        {"log_date": "2026-09-15", "daily_completion_score": 100},
    ]
    assert calculate_current_streak(records, date(2026, 9, 19)) == 3
    assert calculate_best_streak(records) == 3


def test_daily_messages_do_not_repeat_on_adjacent_days():
    first = date(2026, 9, 19)
    assert message_for_day(first) != message_for_day(date(2026, 9, 20))
