"""Erumaa's Daily — private mobile-first routine tracker."""

from __future__ import annotations

import logging

import streamlit as st

from src.auth import ConfigurationError, current_user_id, get_supabase_client, render_login
from src.ui import apply_global_styles

st.set_page_config(
    page_title="Erumaa's Daily",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
apply_global_styles()

try:
    client = get_supabase_client()
except ConfigurationError as exc:
    st.error(str(exc))
    st.info("See README.md for the Supabase setup and deployment checklist.")
    st.stop()

if not current_user_id():
    render_login(client)
    st.stop()

navigation = st.navigation(
    [
        st.Page("pages/home.py", title="Home", icon="🏠", default=True),
        st.Page("pages/today.py", title="Today", icon="✅"),
        st.Page("pages/history.py", title="History", icon="🕘"),
        st.Page("pages/progress.py", title="Progress", icon="📈"),
    ],
    position="hidden",
)
navigation.run()
