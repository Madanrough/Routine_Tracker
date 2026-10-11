"""Daily entry screen."""

from __future__ import annotations

import base64
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image

from src.auth import current_user_id, get_supabase_client
from src.daily_form import render_daily_form
from src.database import DailyLogRepository, RepositoryError
from src.timezone_utils import india_today
from src.ui import apply_today_styles, page_heading, render_primary_navigation, render_settings


@lru_cache(maxsize=1)
def _today_artwork_uri() -> str:
    """Reuse a lightweight copy of the approved Home art in Today's header."""
    artwork = Path(__file__).resolve().parents[1] / "assets" / "home-fairy-twilight.png"
    with Image.open(artwork) as image:
        image.thumbnail((900, 400))
        output = BytesIO()
        image.save(output, format="WEBP", quality=68, method=4)
    return "data:image/webp;base64," + base64.b64encode(output.getvalue()).decode("ascii")


today = india_today()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
render_primary_navigation()
apply_today_styles()
st.html(
    '<style>.st-key-today_header::before {'
    'background-image: linear-gradient(90deg, #080411 4%, rgba(8,4,17,.3) 67%, transparent),'
    f'url("{_today_artwork_uri()}");'
    '}</style>'
)

with st.container(key="today_page"):
    with st.container(key="today_header"):
        page_heading("Today")
        st.caption(today.strftime("%A, %d %B %Y"))
        st.markdown('<p class="subtle">A few simple check-ins for your day</p>', unsafe_allow_html=True)

    try:
        existing = repo.get_log(today)
    except RepositoryError as exc:
        st.error(str(exc))
        st.stop()

    if existing:
        st.info("Today's entry is saved. Update anything below and save again—no duplicate will be created.")
    render_daily_form(today, repo, existing, heading=False, today_style=True)
