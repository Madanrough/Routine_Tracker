"""Weekly/monthly trends, factual insights, streaks, and celebration."""

from __future__ import annotations

import html
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.auth import current_user_id, get_supabase_client
from src.celebrations import generate_achievement_card
from src.database import DailyLogRepository, RepositoryError
from src.insights import weekly_insights
from src.progress import (
    latest_qualifying_week,
    monthly_metrics,
    qualifying_weeks_in_month,
    weekly_habit_stats,
    weekly_series,
)
from src.scoring import calculate_current_streak, calculate_weekly_average
from src.timezone_utils import india_today, month_bounds, week_bounds
from src.ui import (
    message_card,
    page_heading,
    render_primary_navigation,
    render_settings,
    section_label,
    stat_grid,
)


def trend_chart(frame: pd.DataFrame, field: str, title: str, suffix: str = "") -> None:
    available = frame.loc[frame[field].notna(), ["day", field]]
    if len(available) < 3:
        if available.empty:
            values = "No recorded data yet"
        else:
            values = "  ·  ".join(
                f"{row['day']}: {float(row[field]):g}{suffix}" for _, row in available.iterrows()
            )
        count = f"{len(available)} recorded {'day' if len(available) == 1 else 'days'}"
        st.markdown(
            f"""<div class="trend-summary"><div class="trend-summary-head">
            <span class="trend-title">{html.escape(title)}</span><span class="trend-count">{count}</span></div>
            <div class="trend-values">{html.escape(values)}</div></div>""",
            unsafe_allow_html=True,
        )
        return

    figure = go.Figure()
    figure.add_trace(go.Scatter(
        x=frame["day"], y=frame[field], mode="lines+markers", connectgaps=False,
        line={"color": "#8B5CF6", "width": 3}, marker={"size": 8, "color": "#A78BFA"},
        hovertemplate=f"%{{x}}: %{{y:.1f}}{suffix}<extra></extra>",
    ))
    figure.update_layout(
        title={"text": title, "font": {"size": 15}}, height=225,
        margin={"l": 10, "r": 10, "t": 45, "b": 16},
        paper_bgcolor="#171024", plot_bgcolor="#171024", font={"color": "#B8AEC9"},
        xaxis={"fixedrange": True, "showgrid": False},
        yaxis={"fixedrange": True, "gridcolor": "#2C2140", "rangemode": "tozero"},
        showlegend=False,
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def consistency_chart(records: list[dict], first: date, through: date) -> None:
    completed = {
        date.fromisoformat(str(row["log_date"]))
        for row in records
        if float(row.get("daily_completion_score") or 0) == 100
    }
    if len(records) < 3:
        elapsed = (through - first).days + 1
        st.markdown(
            f"""<div class="trend-summary"><div class="trend-summary-head">
            <span class="trend-title">Habit Consistency</span><span class="trend-count">MONTH TO DATE</span></div>
            <div class="trend-values">{len(completed)} complete · {elapsed} days elapsed</div></div>""",
            unsafe_allow_html=True,
        )
        return
    dates = pd.date_range(first, through, freq="D")
    frame = pd.DataFrame({
        "date": dates,
        "status": [1 if value.date() in completed else 0 for value in dates],
        "color": ["#8B5CF6" if value.date() in completed else "#2C2140" for value in dates],
    })
    figure = go.Figure(go.Bar(
        x=frame["date"].dt.strftime("%d"),
        y=frame["status"],
        marker_color=frame["color"],
        hovertemplate="%{x}: %{customdata}<extra></extra>",
        customdata=["Complete" if value else "Not recorded" for value in frame["status"]],
    ))
    figure.update_layout(
        title={"text": "Habit Consistency", "font": {"size": 15}}, height=205,
        margin={"l": 10, "r": 10, "t": 45, "b": 16}, bargap=0.22,
        paper_bgcolor="#171024", plot_bgcolor="#171024", font={"color": "#B8AEC9"},
        xaxis={"fixedrange": True, "showgrid": False, "title": "Day of month"},
        yaxis={"fixedrange": True, "visible": False, "range": [0, 1.15]},
        showlegend=False,
    )
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


today = india_today()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
render_primary_navigation()
page_heading("Progress", "Patterns, not pressure")

try:
    all_records = repo.list_logs()
except RepositoryError as exc:
    st.error(str(exc))
    st.stop()

monday, sunday = week_bounds(today)
week_records = [row for row in all_records if monday.isoformat() <= str(row["log_date"]) <= sunday.isoformat()]
previous_records = [
    row for row in all_records
    if (monday - timedelta(days=7)).isoformat() <= str(row["log_date"]) <= (monday - timedelta(days=1)).isoformat()
]
weekly_average = calculate_weekly_average(week_records)
completed_days = sum(float(row.get("daily_completion_score") or 0) == 100 for row in week_records)
streak = calculate_current_streak(all_records, today)

section_label("◫", "This week", "WEEK TO DATE" if today < sunday or completed_days < 7 else "COMPLETE WEEK")
stat_grid(
    [
        ("WEEKLY AVERAGE", f"{weekly_average:.1f}%", "Monday → Sunday"),
        ("COMPLETED", f"{completed_days} / 7", "Complete daily entries"),
        ("CURRENT STREAK", f"{streak} {'day' if streak == 1 else 'days'}", "Consecutive complete days"),
    ]
)

habit_stats = weekly_habit_stats(week_records)
habit_cards = []
fruit_yes, fruit_tracked = habit_stats["ate_fruit"]
if fruit_tracked:
    habit_cards.append(("FRUIT", f"{fruit_yes} / {fruit_tracked}", "Tracked days with fruit"))
freshened_yes, freshened_tracked = habit_stats["freshened_up"]
if freshened_tracked:
    habit_cards.append(
        ("FRESHENED UP", f"{freshened_yes} / {freshened_tracked}", "Tracked mornings")
    )
if habit_cards:
    stat_grid(habit_cards)

series = pd.DataFrame(weekly_series(week_records, monday))
trend_chart(series, "daily_score", "Daily Score", "%")
tab_sleep, tab_exercise, tab_water = st.tabs(["Sleep", "Exercise", "Water"])
with tab_sleep:
    trend_chart(series, "sleep_hours", "Sleep Trend", " h")
with tab_exercise:
    exercise_frame = series.copy()
    exercise_frame["exercise_value"] = exercise_frame["exercise_done"].map({True: 1, False: 0})
    trend_chart(exercise_frame, "exercise_value", "Exercise Consistency")
with tab_water:
    trend_chart(series, "water_liters", "Water Trend", " L")

insights = weekly_insights(week_records, previous_records)
insight_items = "".join(f"<li>{html.escape(item)}</li>" for item in insights)
st.markdown(
    f'<div class="insight-panel"><div class="kpi-label">WEEKLY INSIGHTS</div><ul>{insight_items}</ul></div>',
    unsafe_allow_html=True,
)

achievement = latest_qualifying_week(all_records)
if achievement:
    achievement_monday, achievement_records = achievement
    achievement_average = calculate_weekly_average(achievement_records)
    st.markdown("## 🎁 A Surprise For You")
    when = "this week" if achievement_monday == monday else "in your latest qualifying week"
    st.write(f"You completed 80%+ {when}!")
    reveal_key = f"celebration_{achievement_monday.isoformat()}"
    if st.session_state.get(reveal_key) or st.button("🔒 TAP TO OPEN", type="primary", width="stretch"):
        st.session_state[reveal_key] = True
        message_card(f"🎉 AMAZING! 🎉\n\nERUMAAA ❤️\n\n{achievement_average:.0f}% THIS WEEK\n\nI'm proud of you. Keep going, Alagiii. ❤️", complete=True)
        try:
            card = generate_achievement_card(achievement_average)
            st.download_button(
                "DOWNLOAD CARD",
                data=card,
                file_name=f"erumaas-daily-week-{achievement_monday.isoformat()}.png",
                mime="image/png",
                width="stretch",
            )
        except Exception:
            st.error("We couldn't create the card right now. Please try again.")
elif completed_days == 7:
    message_card("Every week is a fresh start. ❤️ Small steps still count.")

first, last = month_bounds(today)
month_records = [row for row in all_records if first.isoformat() <= str(row["log_date"]) <= last.isoformat()]
metrics = monthly_metrics(month_records)
metrics["qualifying_weeks"] = qualifying_weeks_in_month(all_records, first, last)
section_label("▦", "This month", today.strftime("%B").upper())
metric_values = [
    ("AVERAGE SCORE", f"{metrics['average_score']:.1f}%", "Recorded days"),
    ("COMPLETED DAYS", str(metrics["completed_days"]), "This month"),
    ("EXERCISE DAYS", str(metrics["exercise_days"]), "This month"),
    ("AVERAGE SLEEP", f"{metrics['average_sleep']:.1f} h", "Recorded days"),
    ("AVERAGE WATER", f"{metrics['average_water']:.1f} L", "Recorded days"),
    ("BEST STREAK", f"{metrics['best_streak']} {'day' if metrics['best_streak'] == 1 else 'days'}", "This month"),
    ("80%+ WEEKS", str(metrics["qualifying_weeks"]), "Complete weeks"),
]
stat_grid(metric_values)

if month_records:
    monthly_frame = pd.DataFrame(sorted(month_records, key=lambda row: row["log_date"]))
    monthly_frame["day"] = pd.to_datetime(monthly_frame["log_date"]).dt.strftime("%d %b")
    trend_chart(monthly_frame, "daily_score", "Monthly Score Trend", "%")
else:
    st.info("Your monthly trend will appear after your first saved entry.")
consistency_chart(month_records, first, min(today, last))
