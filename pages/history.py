"""A personal wellness journal built from saved, user-owned daily records."""

from __future__ import annotations

import html
from datetime import date

import streamlit as st

from src.auth import current_user_id, get_supabase_client
from src.daily_form import render_daily_form
from src.database import DailyLogRepository, RepositoryError
from src.history import edit_status, history_summary, record_details, relative_date_label
from src.timezone_utils import india_today, is_editable_log_date
from src.ui import (
    apply_journal_background,
    apply_journal_page_styles,
    page_heading,
    render_primary_navigation,
    render_settings,
)


DETAIL_GROUPS = (
    ("Sleep & movement", ("Sleep", "Exercise")),
    ("Food & nourishment", (
        "1st Meal · Protein + Fibre", "2nd Meal · Protein + Fibre",
        "3rd Meal · Protein + Fibre", "Junk / Sugary Food", "Fruit",
    )),
    ("Daily care", ("Water", "Freshened up after waking")),
    ("Wellbeing", ("Stress", "Relaxation action", "Mood")),
)


def _summary_cards(records: list[dict]) -> None:
    count, average, best = history_summary(records)
    best_date = date.fromisoformat(str(best["log_date"])) if best else None
    cards = (
        ("TOTAL ENTRIES", str(count), "Days saved", ""),
        ("AVERAGE SCORE", f"{average:.1f}%" if average is not None else "—", "Scored entries", "accent"),
        (
            "BEST DAY",
            best_date.strftime("%d %b %Y") if best_date else "—",
            f"{float(best['daily_score']):.0f}% daily score" if best else "No scored day yet",
            "",
        ),
    )
    markup = "".join(
        f'<div class="journal-stat journal-stat-{accent}" role="group" aria-label="{html.escape(label)}">'
        f'<div class="journal-stat-label">{html.escape(label)}</div>'
        f'<div class="journal-stat-value">{html.escape(value)}</div>'
        f'<div class="journal-stat-meta">{html.escape(meta)}</div></div>'
        for label, value, meta, accent in cards
    )
    st.html(f'<div class="journal-stat-grid">{markup}</div>')


def _detail_cards(record: dict) -> None:
    details = dict(record_details(record))
    groups = []
    for title, labels in DETAIL_GROUPS:
        rows = "".join(
            '<div class="journal-detail-row">'
            f'<span>{html.escape(label)}</span><span>{html.escape(details[label])}</span></div>'
            for label in labels
        )
        groups.append(
            f'<section class="journal-detail-group"><h3>{html.escape(title)}</h3>{rows}</section>'
        )
    st.html(f'<div class="journal-detail-grid">{"".join(groups)}</div>')
    if record.get("daily_note"):
        note = html.escape(str(record["daily_note"])).replace("\n", "<br>")
        st.html(
            '<div class="journal-note"><div class="journal-eyebrow">PERSONAL NOTE</div>'
            f'<p>{note}</p></div>'
        )


def _entry(record: dict, today: date, repo: DailyLogRepository) -> None:
    day = date.fromisoformat(str(record["log_date"]))
    editable = is_editable_log_date(day, today)
    score = record.get("daily_score")
    score_value = max(0.0, min(100.0, float(score))) if score is not None else None
    score_label = f"{score_value:.0f}%" if score_value is not None else "—"
    score_class = "" if score_value is not None else " untracked"
    ring = f"{score_value:.1f}%" if score_value is not None else "0%"
    completion = record.get("daily_completion_score")
    completion_label = (
        "Completion not tracked" if completion is None
        else "Complete" if float(completion) == 100 else "Incomplete"
    )
    status_class = "" if editable else " read-only"
    with st.container(key=f"journal_entry_{day.isoformat()}"):
        st.html(
            '<div class="journal-entry-head">'
            '<div class="journal-entry-copy">'
            f'<div class="journal-entry-date">{html.escape(relative_date_label(day, today))}</div>'
            f'<div class="journal-entry-meta">{html.escape(day.strftime("%A · %d %B %Y"))}'
            f' · {html.escape(completion_label)}</div>'
            f'<div class="journal-entry-status{status_class}">{html.escape(edit_status(day, today))}</div>'
            '</div>'
            f'<div class="journal-score-badge{score_class}" style="--score:{ring}" '
            f'role="img" aria-label="Daily score {html.escape(score_label)}">'
            f'<span>{html.escape(score_label)}</span></div></div>'
        )
        with st.expander(
            f"Read entry · {relative_date_label(day, today)}",
            key=f"journal_details_{day.isoformat()}",
        ):
            _detail_cards(record)
            if editable:
                if st.toggle("Edit this entry", key=f"edit_{day.isoformat()}"):
                    render_daily_form(day, repo, record, heading=False)
            else:
                st.caption("This entry is read only. Only today and yesterday can be edited.")


today = india_today()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
apply_journal_background()
apply_journal_page_styles()
render_primary_navigation()

with st.container(key="history_page"):
    with st.container(key="history_header"):
        page_heading("Your Journey", "Every little step is part of your story.")

    try:
        records = repo.list_logs()
    except RepositoryError as exc:
        st.error(str(exc))
        st.stop()

    _summary_cards(records)
    if not records:
        st.html(
            '<div class="journal-empty"><div class="journal-eyebrow">YOUR JOURNAL</div>'
            '<h2>Your story begins with one small step.</h2>'
            '<p>Save a daily check-in and your journey will appear here.</p></div>'
        )
        st.page_link("pages/today.py", label="Go to Today", icon=":material/arrow_forward:")
        st.stop()

    st.html(
        '<div class="journal-section-heading"><h2>Daily journal</h2>'
        '<span>Newest first</span></div>'
    )
    with st.container(key="history_timeline"):
        for record in records:
            _entry(record, today, repo)
