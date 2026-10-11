"""A personal growth dashboard with real, user-owned wellness trends."""

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
    PERIOD_OPTIONS,
    habit_status_counts,
    latest_qualifying_week,
    monthly_metrics,
    period_bounds,
    period_overview,
    period_series,
    qualifying_weeks_in_month,
    records_in_period,
    tracked_average,
    weekly_habit_stats,
)
from src.scoring import calculate_current_streak, calculate_weekly_average
from src.timezone_utils import india_today, month_bounds, week_bounds
from src.ui import (
    apply_journal_background,
    apply_journal_page_styles,
    message_card,
    page_heading,
    render_primary_navigation,
    render_settings,
    stat_grid,
)


def _section_heading(title: str, note: str = "") -> None:
    st.html(
        '<div class="journal-section-heading">'
        f'<h2>{html.escape(title)}</h2><span>{html.escape(note)}</span></div>'
    )


def _chart_heading(title: str, description: str) -> None:
    st.html(
        '<div class="journal-chart-heading">'
        f'<h2>{html.escape(title)}</h2><p>{html.escape(description)}</p></div>'
    )


def _chart_empty(message: str) -> None:
    st.html(f'<div class="journal-chart-empty">{html.escape(message)}</div>')


def _chart_layout(figure: go.Figure, *, height: int = 250) -> None:
    figure.update_layout(
        height=height,
        margin={"l": 8, "r": 8, "t": 15, "b": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Segoe UI, sans-serif", "color": "#C9C0D7", "size": 12},
        hoverlabel={"bgcolor": "#25183B", "bordercolor": "#A78BFA", "font": {"color": "#FAF8FF"}},
        showlegend=False,
    )


def _trend_chart(
    series: list[dict], field: str, title: str, description: str, unit: str,
    *, color: str = "#A78BFA", reference: float | None = None,
) -> None:
    with st.container(key=f"journal_chart_{field}"):
        _chart_heading(title, description)
        if not any(row.get(field) is not None for row in series):
            _chart_empty("Your trend will appear as you record more days.")
            return
        figure = go.Figure(go.Scatter(
            x=[row["date"] for row in series],
            y=[row.get(field) for row in series],
            mode="lines+markers",
            connectgaps=False,
            line={"color": color, "width": 2.5},
            marker={"color": color, "size": 8, "line": {"color": "#160B26", "width": 1}},
            hovertemplate=f"%{{x|%d %b %Y}}<br><b>%{{y:.1f}}{unit}</b><extra></extra>",
        ))
        if reference is not None:
            figure.add_hline(
                y=reference, line_color="rgba(196,181,253,.55)", line_dash="dot",
                annotation_text="80% marker", annotation_position="top left",
                annotation_font_color="#C4B5FD", annotation_font_size=11,
            )
        figure.update_xaxes(
            type="date", tickformat="%d %b", nticks=5, showgrid=False,
            linecolor="rgba(196,181,253,.2)", automargin=True, fixedrange=True,
        )
        figure.update_yaxes(
            ticksuffix=unit, showgrid=True, gridcolor="rgba(196,181,253,.11)",
            zeroline=False, automargin=True, fixedrange=True,
            range=[0, 105] if field == "daily_score" else None,
            rangemode="tozero",
        )
        _chart_layout(figure)
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def _habit_chart(records: list[dict]) -> None:
    with st.container(key="journal_chart_habits"):
        _chart_heading(
            "Little Habits, Big Progress",
            "Yes, No, and untracked answers among saved entries.",
        )
        if not records:
            _chart_empty("Habit patterns will appear after your first saved day.")
            return
        counts = habit_status_counts(records)
        labels = ("Exercise", "Fruit", "Freshened up")
        fields = ("exercise_done", "ate_fruit", "freshened_up")
        figure = go.Figure()
        for index, (status, color) in enumerate((
            ("Yes", "#A78BFA"), ("No", "#6D4B9C"), ("Not tracked", "#454052"),
        )):
            figure.add_trace(go.Bar(
                y=labels,
                x=[counts[field][index] for field in fields],
                orientation="h",
                name=status,
                marker_color=color,
                hovertemplate=f"%{{y}}<br>{status}: %{{x}} saved days<extra></extra>",
            ))
        figure.update_layout(barmode="stack", bargap=.35, showlegend=True)
        _chart_layout(figure, height=255)
        figure.update_layout(
            showlegend=True,
            legend={"orientation": "h", "y": 1.12, "x": 0, "font": {"size": 11}},
            margin={"l": 8, "r": 8, "t": 38, "b": 12},
        )
        figure.update_xaxes(
            title="Saved entries", rangemode="tozero", dtick=1 if len(records) <= 10 else None,
            gridcolor="rgba(196,181,253,.11)", zeroline=False, fixedrange=True,
        )
        figure.update_yaxes(autorange="reversed", fixedrange=True)
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def _monthly_completion_chart(records: list[dict], first: date, through: date) -> None:
    """Keep the established calendar-month completion view available, but compact."""
    if not records:
        _chart_empty("The monthly pattern will appear after your first saved entry.")
        return
    lookup = {date.fromisoformat(str(row["log_date"])): row for row in records}
    dates = pd.date_range(first, through, freq="D")
    labels = []
    colors = []
    values = []
    for day in dates:
        row = lookup.get(day.date())
        if row is None:
            labels.append("No entry")
            colors.append("#342941")
            values.append(0)
        elif row.get("daily_completion_score") is None:
            labels.append("Completion not tracked")
            colors.append("#55466A")
            values.append(.35)
        elif float(row["daily_completion_score"]) == 100:
            labels.append("Complete")
            colors.append("#A78BFA")
            values.append(1)
        else:
            labels.append("Not complete")
            colors.append("#6D4B9C")
            values.append(.5)
    figure = go.Figure(go.Bar(
        x=dates,
        y=values,
        marker_color=colors,
        customdata=labels,
        hovertemplate="%{x|%d %b %Y}<br>%{customdata}<extra></extra>",
    ))
    _chart_layout(figure, height=190)
    figure.update_xaxes(tickformat="%d %b", nticks=6, showgrid=False, fixedrange=True)
    figure.update_yaxes(visible=False, range=[0, 1.1], fixedrange=True)
    st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})


def _reflection(week_records: list[dict], previous_records: list[dict], monday: date, sunday: date) -> None:
    scored = [row for row in week_records if row.get("daily_score") is not None]
    average = calculate_weekly_average(scored) if scored else None
    complete = sum(float(row.get("daily_completion_score") or 0) == 100 for row in week_records)
    insights = weekly_insights(week_records, previous_records)
    week_label = f"{monday.strftime('%d %b')}–{sunday.strftime('%d %b')}"
    score_text = (
        f"{average:.1f}% average · {complete} of 7 complete" if average is not None
        else f"{complete} of 7 complete · no scored entries" if week_records
        else "A new week to begin"
    )
    items = "".join(
        f'<div class="journal-reflection-item">{html.escape(item)}</div>' for item in insights
    )
    st.html(
        '<div class="journal-reflection">'
        f'<div class="journal-reflection-head"><h2>Weekly Reflection</h2><span>{html.escape(week_label)}</span></div>'
        f'<div class="journal-entry-meta">{html.escape(score_text)}</div>{items}</div>'
    )


today = india_today()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
apply_journal_background()
apply_journal_page_styles()
render_primary_navigation()

with st.container(key="progress_page"):
    with st.container(key="progress_header"):
        page_heading("Your Growth Garden", "Small habits. Beautiful progress.")

    try:
        all_records = repo.list_logs()
    except RepositoryError as exc:
        st.error(str(exc))
        st.stop()

    period = st.segmented_control(
        "Time period", PERIOD_OPTIONS, default="Last 7 days",
        key="progress_period", width="stretch", wrap=False,
    ) or "Last 7 days"
    first_day, last_day = period_bounds(today, period)
    selected_records = records_in_period(all_records, first_day, last_day)
    overview = period_overview(selected_records)
    series = period_series(selected_records, first_day, last_day)
    streak = calculate_current_streak(all_records, today)
    habits = weekly_habit_stats(selected_records)

    _section_heading("At a glance", f"{first_day.strftime('%d %b')} – {last_day.strftime('%d %b')}")
    stat_grid([
        ("AVERAGE SCORE", f"{overview['average_score']:.1f}%" if overview["average_score"] is not None else "—", "Scored entries"),
        ("COMPLETED", str(overview["completed_days"]), f"Of {overview['recorded_days']} saved days"),
        ("CURRENT STREAK", f"{streak} {'day' if streak == 1 else 'days'}", "Across all saved days"),
    ])
    _section_heading("Everyday rhythms")
    stat_grid([
        ("AVERAGE SLEEP", f"{overview['average_sleep']:.1f} h" if overview["average_sleep"] is not None else "—", "Tracked days"),
        ("EXERCISE", f"{overview['exercise_days']} / {overview['exercise_tracked']}" if overview["exercise_tracked"] else "—", "Tracked days exercised"),
        ("AVERAGE WATER", f"{overview['average_water']:.1f} L" if overview["average_water"] is not None else "—", "Tracked days"),
    ])
    fruit_yes, fruit_tracked = habits["ate_fruit"]
    fresh_yes, fresh_tracked = habits["freshened_up"]
    stat_grid([
        ("FRUIT", f"{fruit_yes} / {fruit_tracked}" if fruit_tracked else "—", "Tracked days with fruit"),
        ("FRESHENED UP", f"{fresh_yes} / {fresh_tracked}" if fresh_tracked else "—", "Tracked mornings"),
    ])

    _section_heading("Your patterns", "Based on saved entries")
    _trend_chart(series, "daily_score", "Your Daily Rhythm", "Daily scores over the selected period.", "%", reference=80)
    _habit_chart(selected_records)
    tab_sleep, tab_water, *optional_exercise = st.tabs(
        ["Sleep", "Water"]
        + (["Exercise"] if sum(
            row.get("exercise_done") is True and row.get("exercise_minutes") is not None
            for row in selected_records
        ) >= 2 else [])
    )
    with tab_sleep:
        _trend_chart(series, "sleep_hours", "Rest & Recharge", "Recorded sleep duration.", " h")
    with tab_water:
        _trend_chart(series, "water_liters", "Hydration Journey", "Recorded water intake.", " L", color="#B967FF")
    if optional_exercise:
        exercise_series = [
            {**row, "exercise_minutes": row["exercise_minutes"] if row.get("exercise_done") is True else None}
            for row in series
        ]
        with optional_exercise[0]:
            _trend_chart(
                exercise_series, "exercise_minutes", "Movement Minutes",
                "Recorded minutes on exercise days.", " min",
            )

    monday, sunday = week_bounds(today)
    week_records = records_in_period(all_records, monday, sunday)
    previous_records = records_in_period(all_records, monday - timedelta(days=7), monday - timedelta(days=1))
    _reflection(week_records, previous_records, monday, sunday)

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
            message_card(
                f"🎉 AMAZING! 🎉\n\nERUMAAA ❤️\n\n{achievement_average:.0f}% THIS WEEK\n\n"
                "I'm proud of you. Keep going, Alagiii. ❤️",
                complete=True,
            )
            try:
                card = generate_achievement_card(achievement_average)
                st.download_button(
                    "DOWNLOAD CARD", data=card,
                    file_name=f"erumaas-daily-week-{achievement_monday.isoformat()}.png",
                    mime="image/png", width="stretch",
                )
            except Exception:
                st.error("We couldn't create the card right now. Please try again.")
    elif sum(float(row.get("daily_completion_score") or 0) == 100 for row in week_records) == 7:
        message_card("Every week is a fresh start. ❤️ Small steps still count.")

    month_first, month_last = month_bounds(today)
    month_records = records_in_period(all_records, month_first, month_last)
    monthly = monthly_metrics(month_records)
    monthly["qualifying_weeks"] = qualifying_weeks_in_month(all_records, month_first, month_last)
    _section_heading("This month", today.strftime("%B %Y"))
    if month_records:
        stat_grid([
            ("AVERAGE SCORE", f"{monthly['average_score']:.1f}%" if any(
                row.get("daily_score") is not None for row in month_records
            ) else "—", "Scored days"),
            ("COMPLETED DAYS", str(monthly["completed_days"]), "Calendar month"),
            ("EXERCISE DAYS", str(monthly["exercise_days"]), "Calendar month"),
            ("AVERAGE SLEEP", f"{tracked_average(month_records, 'sleep_hours'):.1f} h" if tracked_average(
                month_records, "sleep_hours"
            ) is not None else "—", "Tracked days"),
            ("AVERAGE WATER", f"{tracked_average(month_records, 'water_liters'):.1f} L" if tracked_average(
                month_records, "water_liters"
            ) is not None else "—", "Tracked days"),
            ("BEST STREAK", f"{monthly['best_streak']} {'day' if monthly['best_streak'] == 1 else 'days'}", "This month"),
            ("80%+ WEEKS", str(monthly["qualifying_weeks"]), "Complete weeks"),
        ])
        with st.expander("Monthly completion pattern"):
            _monthly_completion_chart(month_records, month_first, min(today, month_last))
    else:
        _chart_empty("Your monthly picture will grow as you save daily entries.")
