"""Mobile-friendly historical record cards and edit window."""

from __future__ import annotations

import html
from datetime import date

import streamlit as st

from src.auth import current_user_id, get_supabase_client
from src.daily_form import render_daily_form
from src.database import DailyLogRepository, RepositoryError
from src.history import edit_status, record_details, relative_date_label
from src.timezone_utils import india_today, is_editable_log_date
from src.ui import page_heading, render_primary_navigation, render_settings

today = india_today()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
render_primary_navigation()
page_heading("History", "Your entries, newest first")

try:
    records = repo.list_logs()
except RepositoryError as exc:
    st.error(str(exc))
    st.stop()

if not records:
    st.info("No entries yet. Your saved days will appear here.")
    st.stop()

for record in records:
    day = date.fromisoformat(str(record["log_date"]))
    score = float(record.get("daily_score") or 0)
    completion = float(record.get("daily_completion_score") or 0)
    title = f"{relative_date_label(day, today)}  •  {score:.0f}%  •  {edit_status(day, today)}"
    with st.expander(title):
        sleep = float(record.get("sleep_hours") or 0)
        exercise = int(record.get("exercise_minutes") or 0)
        water = float(record.get("water_liters") or 0)
        glance = f"{sleep:g} h sleep · {exercise} min movement · {water:g} L water"
        st.markdown(
            f"""<div class="record-summary"><div><div class="record-date">{html.escape(day.strftime('%A · %d %B %Y').upper())}</div>
            <div class="record-glance">{html.escape(glance)} · {completion:.0f}% complete</div></div>
            <div class="record-score">{score:.0f}%</div></div>""",
            unsafe_allow_html=True,
        )
        rows = "".join(
            f'<div class="record-row"><span class="record-label">{html.escape(str(label))}</span><span class="record-value">{html.escape(str(value))}</span></div>'
            for label, value in record_details(record)
        )
        st.markdown(f'<div>{rows}</div>', unsafe_allow_html=True)
        if record.get("daily_note"):
            st.markdown("**Daily note**")
            st.write(record["daily_note"])
        if is_editable_log_date(day, today):
            if st.toggle("Edit this entry", key=f"edit_{day.isoformat()}"):
                render_daily_form(day, repo, record, heading=False)
        else:
            st.caption("This entry is read only. Only today and yesterday can be edited.")
