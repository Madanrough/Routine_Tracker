"""Shared Streamlit presentation primitives and the minimal Settings menu."""

from __future__ import annotations

import html
from collections.abc import Iterable

import pandas as pd
import streamlit as st

from src.auth import logout
from src.database import DailyLogRepository, RepositoryError

APP_VERSION = "1.0.0"


def apply_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root { color-scheme: dark; }
        .stApp { background: #0B0614; }
        .block-container {
            max-width: 940px; padding-top: .9rem; padding-bottom: 5rem;
            padding-left: clamp(1rem, 4vw, 2rem); padding-right: clamp(1rem, 4vw, 2rem);
        }
        h1, h2, h3 { letter-spacing: -.025em; }
        h1 { font-size: clamp(1.75rem, 6vw, 2.35rem) !important; margin: .08rem 0 .2rem !important; }
        h2 { font-size: 1.22rem !important; margin: 1.2rem 0 .5rem !important; }
        h3 { font-size: 1rem !important; }
        p { line-height: 1.45; }
        [data-testid="stVerticalBlock"] { gap: .72rem; }
        div[data-testid="stForm"], div[data-testid="stExpander"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #171024; border-color: #302443; border-radius: 16px;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div { padding: .88rem 1rem; }
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
            min-height: 46px; border-radius: 13px; font-weight: 750;
        }
        div[data-testid="stNumberInput"] button { min-width: 44px; min-height: 44px; }
        [data-testid="stSidebarCollapsedControl"] button {
            min-width: 44px; min-height: 44px; border-radius: 12px;
        }
        div[role="radiogroup"] { gap: .42rem; }
        div[role="radiogroup"] label {
            min-height: 42px; border: 1px solid #302443; border-radius: 11px;
            padding: .38rem .7rem; background: #1B1329;
        }
        div[role="radiogroup"] label:has(input:checked) {
            border-color: #8B5CF6; background: #26183D;
        }
        [data-testid="stMetric"] {
            background: #171024; border: 1px solid #302443; border-radius: 15px;
            padding: .75rem .9rem;
        }
        .brand-kicker { color: #A78BFA; font-size: .69rem; font-weight: 850; letter-spacing: .15em; }
        .subtle { color: #B8AEC9; margin: 0 0 .45rem; font-size: .94rem; }
        .login-hero { padding: 9vh 0 1rem; text-align: center; }
        .login-hero p { color: #B8AEC9; }

        /* The application router stays hidden; these are real Streamlit page links. */
        .st-key-primary_navigation {
            position: sticky; top: 3.35rem; z-index: 80; margin: 3rem 0 .9rem;
            padding: .3rem; background: rgba(18, 11, 29, .94); border: 1px solid #302443;
            border-radius: 15px; backdrop-filter: blur(14px); box-shadow: 0 8px 28px rgba(0,0,0,.24);
        }
        .st-key-primary_navigation [data-testid="stHorizontalBlock"] { gap: .25rem; }
        .st-key-primary_navigation [data-testid="stColumn"] { min-width: 0 !important; width: 25% !important; flex: 1 1 0 !important; }
        .st-key-primary_navigation [data-testid="stPageLink"] a {
            min-height: 44px; padding: .35rem .2rem; border-radius: 11px;
            display: flex; justify-content: center; gap: .3rem; color: #B8AEC9;
            font-size: .79rem; font-weight: 750; text-decoration: none;
        }
        .st-key-primary_navigation [data-testid="stPageLink"] a:hover,
        .st-key-primary_navigation [data-testid="stPageLink"] a[aria-current="page"] {
            background: #2A1A43; color: #F5F3FF;
        }
        .st-key-primary_navigation [data-testid="stPageLink"] p { font-size: inherit; }

        .section-label {
            display: flex; align-items: center; gap: .5rem; margin: .05rem 0 .2rem;
            color: #F5F3FF; font-size: .94rem; font-weight: 800;
        }
        .section-label span:first-child { font-size: 1.05rem; }
        .section-note { color: #81758F; font-size: .78rem; margin-left: auto; font-weight: 600; }
        .wellness-card {
            background: #171024; border: 1px solid #302443; border-radius: 16px;
            padding: .9rem 1rem; margin: .4rem 0; box-shadow: 0 10px 30px rgba(0,0,0,.13);
        }
        .kpi-label { color: #AFA4BF; font-size: .68rem; font-weight: 800; letter-spacing: .09em; }
        .kpi-value { color: #F5F3FF; font-size: 1.24rem; font-weight: 850; margin-top: .12rem; }
        .kpi-meta { color: #81758F; font-size: .76rem; }
        .stat-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .55rem; margin: .45rem 0; }
        .stat-card { background:#171024; border:1px solid #302443; border-radius:15px; padding:.78rem .85rem; min-width:0; }
        .stat-card .kpi-value { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .metric-list { background:#171024; border:1px solid #302443; border-radius:16px; overflow:hidden; margin:.4rem 0 .75rem; }
        .metric-row { display:grid; grid-template-columns: 32px minmax(0,1fr) auto; align-items:center; gap:.6rem; padding:.72rem .85rem; border-bottom:1px solid #2B203C; }
        .metric-row:last-child { border-bottom:0; }
        .metric-icon { width:32px; height:32px; display:grid; place-items:center; border-radius:10px; background:#25183A; font-size:1rem; }
        .metric-name { color:#F5F3FF; font-size:.86rem; font-weight:780; }
        .metric-value { color:#92869F; font-size:.76rem; margin-top:.05rem; }
        .metric-score { color:#C4B5FD; font-size:.9rem; font-weight:850; }
        .progress-wrap { display: grid; place-items: center; margin: .6rem 0 .75rem; }
        .progress-ring {
            width: 158px; height: 158px; border-radius: 50%; display: grid; place-items: center;
            background: conic-gradient(#8B5CF6 var(--score), #302443 0);
            box-shadow: 0 0 34px rgba(139,92,246,.16);
        }
        .progress-inner {
            width: 130px; height: 130px; border-radius: 50%; background: #171024;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
        }
        .progress-number { font-size: 2.25rem; font-weight: 850; line-height: 1; }
        .progress-caption { color: #B8AEC9; font-size: .65rem; letter-spacing: .11em; margin-top: .42rem; }
        .message-card {
            background: linear-gradient(135deg, #201536, #171024); border: 1px solid #3A2858;
            border-radius: 16px; padding: .9rem 1rem; color: #F5F3FF; margin-top: .7rem;
        }
        .complete-card { border-color: #8B5CF6; text-align: center; }
        .record-summary { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:.75rem; align-items:center; padding:.1rem 0 .5rem; }
        .record-date { font-size:.72rem; font-weight:800; letter-spacing:.08em; color:#A78BFA; }
        .record-glance { color:#B8AEC9; font-size:.8rem; margin-top:.2rem; }
        .record-score { font-size:1.45rem; font-weight:850; color:#F5F3FF; }
        .record-row { display:flex; justify-content:space-between; gap:1rem; padding:.36rem 0; border-bottom:1px solid #2B203C; font-size:.88rem; }
        .record-row:last-child { border-bottom:0; }
        .record-label { color:#B8AEC9; }
        .record-value { color:#F5F3FF; font-weight:700; text-align:right; }
        .trend-summary { background:#171024; border:1px solid #302443; border-radius:15px; padding:.8rem .9rem; margin:.45rem 0; }
        .trend-summary-head { display:flex; justify-content:space-between; gap:1rem; align-items:baseline; }
        .trend-title { font-weight:800; color:#F5F3FF; }
        .trend-count { font-size:.72rem; color:#81758F; }
        .trend-values { color:#C4B5FD; font-size:.88rem; margin-top:.38rem; }
        .insight-panel { background:#171024; border:1px solid #302443; border-radius:15px; padding:.75rem .9rem; margin:.55rem 0; }
        .insight-panel ul { margin:.35rem 0 .1rem; padding-left:1.15rem; }
        .insight-panel li { color:#C8BED5; margin:.3rem 0; font-size:.87rem; }
        .meal-label { color:#A78BFA; font-size:.68rem; font-weight:850; letter-spacing:.09em; margin:.25rem 0 -.35rem; }

        @media (min-width: 760px) { .stat-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
        @media (max-width: 480px) {
            .block-container { padding-top: .55rem; }
            .st-key-primary_navigation { top: 3.35rem; margin-top: 3rem; margin-bottom: .7rem; }
            .st-key-primary_navigation [data-testid="stPageLink"] a { font-size: .66rem; gap: .08rem; }
            .st-key-primary_navigation [data-testid="stPageLink"] p { font-size: .66rem !important; }
            .st-key-primary_navigation [data-testid="stIconMaterial"] { font-size: .88rem !important; }
            .progress-ring { width: 148px; height: 148px; }
            .progress-inner { width: 122px; height: 122px; }
            .progress-number { font-size: 2.05rem; }
        }
        @media (max-width: 340px) {
            .st-key-primary_navigation [data-testid="stPageLink"] a { font-size: .67rem; }
            .st-key-primary_navigation [data-testid="stPageLink"] p { font-size: .67rem !important; }
            .st-key-primary_navigation [data-testid="stIconMaterial"] { display: none; }
            .metric-row { padding-left:.7rem; padding-right:.7rem; }
            h1 { font-size: 1.45rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_primary_navigation() -> None:
    """Render the visible mobile-first navigation using genuine Streamlit routes."""
    with st.container(key="primary_navigation"):
        columns = st.columns(4, gap="small")
        links = (
            ("pages/home.py", "Home", ":material/home:"),
            ("pages/today.py", "Today", ":material/check_circle:"),
            ("pages/history.py", "History", ":material/history:"),
            ("pages/progress.py", "Progress", ":material/monitoring:"),
        )
        for column, (page, label, icon) in zip(columns, links):
            with column:
                st.page_link(page, label=label, icon=icon, width="stretch")


def page_heading(title: str, subtitle: str | None = None) -> None:
    st.markdown('<div class="brand-kicker">ERUMAA\'S DAILY</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.markdown(f'<p class="subtle">{html.escape(subtitle)}</p>', unsafe_allow_html=True)


def section_label(icon: str, title: str, note: str = "") -> None:
    note_markup = f'<span class="section-note">{html.escape(note)}</span>' if note else ""
    st.markdown(
        f'<div class="section-label"><span>{html.escape(icon)}</span><span>{html.escape(title)}</span>{note_markup}</div>',
        unsafe_allow_html=True,
    )


def progress_ring(score: float, caption: str = "TODAY'S SCORE") -> None:
    score = min(max(score, 0.0), 100.0)
    st.markdown(
        f"""
        <div class="progress-wrap"><div class="progress-ring" style="--score:{score:.1f}%">
          <div class="progress-inner"><div class="progress-number">{score:.0f}%</div>
          <div class="progress-caption">{html.escape(caption)}</div></div>
        </div></div>
        """,
        unsafe_allow_html=True,
    )


def metric_list(items: Iterable[tuple[str, str, str, str]]) -> None:
    rows = "".join(
        f"""<div class="metric-row"><div class="metric-icon">{html.escape(icon)}</div>
        <div><div class="metric-name">{html.escape(label)}</div><div class="metric-value">{html.escape(value)}</div></div>
        <div class="metric-score">{html.escape(score)}</div></div>"""
        for icon, label, value, score in items
    )
    st.markdown(f'<div class="metric-list">{rows}</div>', unsafe_allow_html=True)


def stat_grid(items: Iterable[tuple[str, str, str]]) -> None:
    cards = "".join(
        f"""<div class="stat-card"><div class="kpi-label">{html.escape(label)}</div>
        <div class="kpi-value">{html.escape(value)}</div><div class="kpi-meta">{html.escape(meta)}</div></div>"""
        for label, value, meta in items
    )
    st.markdown(f'<div class="stat-grid">{cards}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, meta: str = "") -> None:
    st.markdown(
        f"""<div class="wellness-card"><div class="kpi-label">{html.escape(label)}</div>
        <div class="kpi-value">{html.escape(value)}</div>
        <div class="kpi-meta">{html.escape(meta)}</div></div>""",
        unsafe_allow_html=True,
    )


def message_card(message: str, complete: bool = False) -> None:
    css = "message-card complete-card" if complete else "message-card"
    safe_message = html.escape(message).replace("\n", "<br>")
    st.markdown(f'<div class="{css}">{safe_message}</div>', unsafe_allow_html=True)


def render_settings(repo: DailyLogRepository) -> None:
    """Settings intentionally contains only Export Data and About."""
    with st.sidebar:
        with st.expander("⚙ Settings"):
            section = st.radio(
                "Settings section",
                ["Export Data", "About"],
                label_visibility="collapsed",
                key="settings_section",
            )
            if section == "Export Data":
                if st.button("Prepare CSV", width="stretch"):
                    try:
                        rows = repo.export_rows()
                        st.session_state.export_csv = (
                            pd.DataFrame(rows).to_csv(index=False).encode("utf-8") if rows else b""
                        )
                    except RepositoryError as exc:
                        st.error(str(exc))
                if "export_csv" in st.session_state:
                    st.download_button(
                        "Download CSV",
                        data=st.session_state.export_csv,
                        file_name="erumaas_daily_export.csv",
                        mime="text/csv",
                        width="stretch",
                        disabled=not st.session_state.export_csv,
                    )
                    if not st.session_state.export_csv:
                        st.caption("No entries to export yet.")
            else:
                st.markdown(f"**Erumaa's Daily** · v{APP_VERSION}")
                st.caption("A private personal routine and wellness tracker.")
                st.caption(
                    "Your entries are stored securely in the application's database and are only intended for your account."
                )
                st.caption(
                    "This app is not medical advice, a diagnostic tool, or a replacement for professional care."
                )
        st.caption(st.session_state.get("auth_email", "Signed in"))
        if st.button("Sign out", width="stretch"):
            logout()
            st.rerun()
