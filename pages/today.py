"""Daily entry screen."""

from __future__ import annotations

import streamlit as st

from src.auth import current_user_id, get_supabase_client
from src.daily_form import render_daily_form
from src.database import DailyLogRepository, RepositoryError
from src.timezone_utils import india_today
from src.ui import page_heading, render_primary_navigation, render_settings

today = india_today()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
render_primary_navigation()
page_heading("Today", "A few simple check-ins for your day")

try:
    existing = repo.get_log(today)
except RepositoryError as exc:
    st.error(str(exc))
    st.stop()

if existing:
    st.info("Today's entry is saved. Update anything below and save again—no duplicate will be created.")
render_daily_form(today, repo, existing)
