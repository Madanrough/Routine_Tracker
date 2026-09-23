"""Home dashboard."""

from __future__ import annotations

import streamlit as st

from src.auth import current_user_id, get_supabase_client
from src.database import DailyLogRepository, RepositoryError
from src.messages import greeting, message_for_day
from src.scoring import calculate_current_streak, calculate_weekly_average
from src.timezone_utils import india_now, india_today, week_bounds
from src.ui import (
    message_card,
    metric_list,
    page_heading,
    progress_ring,
    render_primary_navigation,
    render_settings,
    section_label,
    stat_grid,
)

today = india_today()
now = india_now()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
render_primary_navigation()
page_heading(greeting(now), "Your day at a glance")

try:
    logs = repo.list_logs()
except RepositoryError as exc:
    st.error(str(exc))
    st.stop()

today_record = next((row for row in logs if str(row.get("log_date")) == today.isoformat()), None)
monday, sunday = week_bounds(today)
week_records = [row for row in logs if monday.isoformat() <= str(row.get("log_date")) <= sunday.isoformat()]
score = float(today_record.get("daily_score") or 0) if today_record else 0.0

section_label("✦", "Today's progress", today.strftime("%a, %d %b"))
progress_ring(score)

if today_record:
    cards = [
        ("☾", "Sleep", f"{float(today_record.get('sleep_hours') or 0):g} hours", f"{float(today_record.get('sleep_score') or 0):.0f}%"),
        ("↗", "Exercise", f"{float(today_record.get('exercise_minutes') or 0):g} minutes" if today_record.get("exercise_done") else "Rest day", f"{float(today_record.get('exercise_score') or 0):.0f}%"),
        ("◒", "Food", f"{sum(bool(today_record.get(f'meal{i}_protein_fibre')) for i in range(1, 4))}/3 balanced meals", f"{float(today_record.get('food_score') or 0):.0f}%"),
        ("◇", "Water", f"{float(today_record.get('water_liters') or 0):g} L", f"{float(today_record.get('water_score') or 0):.0f}%"),
    ]
else:
    cards = [
        ("☾", "Sleep", "Not entered", "—"),
        ("↗", "Exercise", "Not entered", "—"),
        ("◒", "Food", "Not entered", "—"),
        ("◇", "Water", "Not entered", "—"),
    ]

metric_list(cards)

streak = calculate_current_streak(logs, today)
weekly_score = calculate_weekly_average(week_records)
streak_unit = "DAY" if streak == 1 else "DAYS"
stat_grid(
    [
        ("CURRENT STREAK", f"{streak} {streak_unit}", "Consecutive complete days"),
        ("WEEKLY SCORE", f"{weekly_score:.0f}%", f"{len(week_records)} of 7 days"),
    ]
)

complete = bool(today_record and float(today_record.get("daily_completion_score") or 0) == 100)
if complete:
    message_card("✨ TODAY COMPLETE ✨\n\nYou showed up today. ❤️", complete=True)
else:
    message_card(message_for_day(today))
    st.caption("Still to complete: Sleep · Exercise · Food · Water · Stress management · Mood")
    if st.button("Complete Today", type="primary", width="stretch"):
        st.switch_page("pages/today.py")
