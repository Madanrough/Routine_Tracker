from datetime import date

from src.insights import weekly_insights
from src.progress import (
    latest_qualifying_week,
    monthly_metrics,
    qualifying_weeks_in_month,
    weekly_habit_stats,
)


def completed_week(monday: date, score: float):
    return [
        {
            "log_date": date.fromordinal(monday.toordinal() + offset).isoformat(),
            "daily_score": score,
            "daily_completion_score": 100,
        }
        for offset in range(7)
    ]


def test_latest_celebration_remains_available_after_week_ends():
    old_week = completed_week(date(2026, 8, 31), 85)
    current_partial = completed_week(date(2026, 9, 14), 90)[:3]
    result = latest_qualifying_week(old_week + current_partial)
    assert result is not None
    assert result[0] == date(2026, 8, 31)


def test_month_counts_week_by_its_sunday():
    crossing_week = completed_week(date(2026, 8, 31), 85)
    assert qualifying_weeks_in_month(
        crossing_week, date(2026, 9, 1), date(2026, 9, 30)
    ) == 1


def test_empty_progress_data_has_safe_zero_state():
    metrics = monthly_metrics([])
    assert metrics["average_score"] == 0
    assert metrics["completed_days"] == 0
    assert weekly_insights([]) == [
        "Complete a daily entry to begin seeing your weekly patterns."
    ]


def test_missing_week_data_never_creates_achievement():
    assert latest_qualifying_week([]) is None
    assert latest_qualifying_week(completed_week(date(2026, 9, 14), 100)[:6]) is None


def test_weekly_habits_ignore_legacy_null_values():
    records = [
        {"ate_fruit": True, "freshened_up": False},
        {"ate_fruit": False, "freshened_up": True},
        {"ate_fruit": None, "freshened_up": None},
        {},
    ]
    assert weekly_habit_stats(records) == {
        "ate_fruit": (1, 2),
        "freshened_up": (1, 2),
    }


def test_weekly_insights_report_only_tracked_new_habits():
    records = [
        {
            "sleep_hours": 8,
            "water_liters": 2.5,
            "exercise_done": True,
            "ate_fruit": True,
            "freshened_up": False,
        },
        {
            "sleep_hours": 7,
            "water_liters": 2,
            "exercise_done": False,
            "ate_fruit": None,
            "freshened_up": True,
        },
    ]
    insights = weekly_insights(records)
    assert "You ate fruit on 1 out of 1 tracked days." in insights
    assert "You freshened up after waking on 1 out of 2 tracked days." in insights

