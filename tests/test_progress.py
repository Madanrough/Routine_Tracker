from datetime import date

from src.insights import weekly_insights
from src.progress import latest_qualifying_week, monthly_metrics, qualifying_weeks_in_month


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

