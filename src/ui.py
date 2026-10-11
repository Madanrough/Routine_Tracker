"""Shared Streamlit presentation primitives and the minimal Settings menu."""

from __future__ import annotations

import base64
import html
from collections.abc import Iterable
from functools import lru_cache
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

from src.auth import logout
from src.database import DailyLogRepository, RepositoryError

APP_VERSION = "1.0.0"

# Shared visual tokens for the Minimal Neon + Glass Serenity design system.
# Keeping them in one CSS block makes every native and custom component use
# the same palette, spacing, radii, shadows, and motion rules.
DESIGN_TOKENS = """
:root {
    color-scheme: dark;
    --canvas-0: #050208;
    --canvas-1: #0A0512;
    --canvas-2: #130923;
    --surface-solid: #171024;
    --surface-raised: #1D142C;
    --surface-soft: #211630;
    --glass: rgba(24, 15, 38, .78);
    --glass-strong: rgba(29, 18, 46, .9);
    --glass-highlight: rgba(255, 255, 255, .045);
    --border-subtle: rgba(196, 181, 253, .16);
    --border-strong: rgba(167, 139, 250, .42);
    --divider: rgba(196, 181, 253, .1);
    --violet-300: #C4B5FD;
    --violet-400: #A78BFA;
    --violet-500: #8B5CF6;
    --violet-600: #7C3AED;
    --neon-violet: #B967FF;
    --text-primary: #FAF8FF;
    --text-secondary: #C9C0D7;
    --text-muted: #91869E;
    --success: #86EFAC;
    --danger: #FDA4AF;
    --radius-sm: 10px;
    --radius-md: 14px;
    --radius-lg: 18px;
    --radius-xl: 24px;
    --space-1: .25rem;
    --space-2: .5rem;
    --space-3: .75rem;
    --space-4: 1rem;
    --space-5: 1.25rem;
    --shadow-soft: 0 14px 38px rgba(0, 0, 0, .24);
    --shadow-raised: 0 18px 48px rgba(0, 0, 0, .32);
    --glow-soft: 0 0 28px rgba(139, 92, 246, .13);
    --glow-focus: 0 0 0 3px rgba(167, 139, 250, .18);
    --blur: 18px;
    --content-width: 940px;
    --motion-fast: 160ms;
    --motion-normal: 280ms;
    --ease-out: cubic-bezier(.22, 1, .36, 1);
    --font-system: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
"""


def apply_global_styles() -> None:
    st.markdown(
        "<style>" + DESIGN_TOKENS + """
        html { background: var(--canvas-0); }
        body, .stApp {
            font-family: var(--font-system);
            color: var(--text-primary);
        }
        .stApp {
            background-color: var(--canvas-0);
            background-image:
                radial-gradient(circle at 12% -8%, rgba(124, 58, 237, .22), transparent 34rem),
                radial-gradient(circle at 94% 10%, rgba(139, 92, 246, .12), transparent 30rem),
                linear-gradient(160deg, var(--canvas-0) 0%, var(--canvas-1) 48%, #08030E 100%);
            background-attachment: fixed;
        }
        .block-container {
            max-width: var(--content-width);
            padding-top: .9rem;
            padding-bottom: 5rem;
            padding-left: clamp(1rem, 4vw, 2rem);
            padding-right: clamp(1rem, 4vw, 2rem);
        }

        /* Typography */
        h1, h2, h3, p, label, button, input, textarea { font-family: var(--font-system); }
        h1, h2, h3 { color: var(--text-primary); letter-spacing: -.028em; }
        h1 {
            font-size: clamp(1.75rem, 6vw, 2.4rem) !important;
            font-weight: 760 !important;
            line-height: 1.12 !important;
            margin: .08rem 0 .25rem !important;
        }
        h2 { font-size: 1.22rem !important; margin: 1.25rem 0 .55rem !important; }
        h3 { font-size: 1rem !important; }
        p { line-height: 1.5; }
        a { color: var(--violet-300); }
        a:hover { color: var(--text-primary); }
        [data-testid="stCaptionContainer"] { color: var(--text-muted); }
        [data-testid="stVerticalBlock"] { gap: .72rem; }

        /* Accessible focus is deliberately visible on the dark canvas. */
        :where(button, a, input, textarea, [role="radio"], [role="tab"], [role="switch"]):focus-visible {
            outline: 2px solid var(--violet-300) !important;
            outline-offset: 2px !important;
            box-shadow: var(--glow-focus) !important;
        }

        /* Glass fallback: fully usable without backdrop-filter support. */
        div[data-testid="stForm"],
        div[data-testid="stExpander"],
        div[data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stMetric"],
        [data-testid="stPlotlyChart"],
        .wellness-card,
        .stat-card,
        .metric-list,
        .message-card,
        .trend-summary,
        .insight-panel {
            background: var(--surface-solid);
            border: 1px solid var(--border-subtle);
            box-shadow: var(--shadow-soft);
        }
        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
            div[data-testid="stForm"],
            div[data-testid="stExpander"],
            div[data-testid="stVerticalBlockBorderWrapper"],
            [data-testid="stMetric"],
            [data-testid="stPlotlyChart"],
            .wellness-card,
            .stat-card,
            .metric-list,
            .message-card,
            .trend-summary,
            .insight-panel {
                background: linear-gradient(145deg, var(--glass-highlight), transparent 42%), var(--glass);
                -webkit-backdrop-filter: blur(var(--blur)) saturate(125%);
                backdrop-filter: blur(var(--blur)) saturate(125%);
            }
        }
        div[data-testid="stForm"],
        div[data-testid="stExpander"],
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: var(--radius-lg);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] > div { padding: .9rem 1rem; }
        div[data-testid="stExpander"] details > summary {
            min-height: 48px;
            border-radius: var(--radius-md);
            color: var(--text-primary);
        }
        div[data-testid="stExpander"] details[open] > summary {
            border-bottom: 1px solid var(--divider);
        }

        /* Native controls */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
            min-height: 46px;
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-md);
            background: linear-gradient(135deg, rgba(139, 92, 246, .2), rgba(29, 18, 46, .9));
            color: var(--text-primary);
            font-weight: 720;
            box-shadow: 0 8px 24px rgba(0, 0, 0, .18), inset 0 1px 0 rgba(255, 255, 255, .05);
            transition:
                border-color var(--motion-fast) ease,
                background var(--motion-fast) ease,
                box-shadow var(--motion-fast) ease,
                transform var(--motion-fast) ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
            border-color: var(--violet-300);
            background: linear-gradient(135deg, rgba(167, 139, 250, .3), rgba(43, 25, 68, .94));
            box-shadow: var(--glow-soft), 0 10px 28px rgba(0, 0, 0, .24);
            transform: translateY(-1px);
        }
        .stButton > button:active, .stDownloadButton > button:active, .stFormSubmitButton > button:active {
            transform: translateY(0);
        }
        .stButton > button:disabled, .stDownloadButton > button:disabled {
            opacity: .48;
            transform: none;
        }
        div[data-testid="stNumberInput"] button { min-width: 44px; min-height: 44px; }
        [data-testid="stSidebarCollapsedControl"] button {
            min-width: 44px;
            min-height: 44px;
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            background: var(--glass-strong);
        }
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            color: var(--text-primary);
            caret-color: var(--violet-300);
        }
        div[role="radiogroup"] { gap: .42rem; }
        div[role="radiogroup"] label {
            min-height: 42px;
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-sm);
            padding: .4rem .72rem;
            background: var(--surface-raised);
            color: var(--text-secondary);
            transition: border-color var(--motion-fast) ease, background var(--motion-fast) ease, color var(--motion-fast) ease;
        }
        div[role="radiogroup"] label:hover {
            border-color: var(--border-strong);
            color: var(--text-primary);
        }
        @supports selector(label:has(input:checked)) {
            div[role="radiogroup"] label:has(input:checked) {
                border-color: var(--violet-400);
                background: linear-gradient(135deg, rgba(139, 92, 246, .27), rgba(38, 24, 61, .94));
                color: var(--text-primary);
                box-shadow: inset 0 0 0 1px rgba(196, 181, 253, .08), 0 0 20px rgba(139, 92, 246, .09);
            }
        }
        [data-testid="stAlert"] {
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            background: var(--surface-raised);
        }
        [data-baseweb="tab-list"] { gap: var(--space-2); }
        [data-baseweb="tab"] {
            min-height: 44px;
            color: var(--text-secondary);
        }
        [data-baseweb="tab"][aria-selected="true"] { color: var(--violet-300); }

        /* Sidebar keeps its behavior while sharing the same visual language. */
        section[data-testid="stSidebar"] > div {
            background:
                radial-gradient(circle at 10% 0%, rgba(124, 58, 237, .17), transparent 20rem),
                var(--canvas-1);
            border-right: 1px solid var(--border-subtle);
        }
        .st-key-settings_menu summary p {
            position: absolute;
            width: 1px;
            height: 1px;
            margin: -1px;
            overflow: hidden;
            clip-path: inset(50%);
            white-space: nowrap;
        }
        .st-key-settings_menu summary [data-testid="stIconMaterial"] {
            color: var(--violet-300);
            font-size: 1.4rem;
        }

        .brand-kicker {
            color: var(--violet-400);
            font-size: .68rem;
            font-weight: 800;
            letter-spacing: .17em;
            text-shadow: 0 0 16px rgba(167, 139, 250, .2);
        }
        .subtle { color: var(--text-secondary); margin: 0 0 .5rem; font-size: .94rem; }
        .st-key-login_panel {
            max-width: 490px;
            margin: clamp(1.4rem, 7vh, 4.5rem) auto 2rem;
            padding: clamp(1.5rem, 4vw, 2.35rem);
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-xl);
            background:
                radial-gradient(circle at 85% 0%, rgba(143, 77, 232, .18), transparent 16rem),
                var(--surface-solid);
            box-shadow: var(--shadow-raised), 0 0 50px rgba(139, 92, 246, .14), inset 0 1px 0 rgba(255, 255, 255, .07);
        }
        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
            .st-key-login_panel {
                background:
                    radial-gradient(circle at 85% 0%, rgba(143, 77, 232, .18), transparent 16rem),
                    var(--glass-strong);
                -webkit-backdrop-filter: blur(var(--blur)) saturate(125%);
                backdrop-filter: blur(var(--blur)) saturate(125%);
            }
        }
        .login-hero { padding: .15rem 0 1.65rem; text-align: center; }
        .login-mark {
            display: grid;
            place-items: center;
            width: 2.75rem;
            height: 2.75rem;
            margin: 0 auto 1.25rem;
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-md);
            background: linear-gradient(145deg, rgba(167, 139, 250, .29), rgba(74, 33, 130, .42));
            box-shadow: 0 0 24px rgba(167, 139, 250, .18);
            color: var(--violet-300);
            font-size: 1.3rem;
        }
        .login-hero .brand-kicker { margin-bottom: .65rem; }
        .login-hero h1 {
            margin: .35rem 0 .55rem !important;
            font-size: clamp(2rem, 6vw, 2.5rem) !important;
            background: linear-gradient(100deg, var(--text-primary), var(--violet-300));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .login-hero p { margin: 0; color: var(--text-secondary); font-size: .94rem; }
        .st-key-login_panel div[data-testid="stForm"] {
            padding: 0;
            border: 0;
            background: transparent;
            box-shadow: none;
            -webkit-backdrop-filter: none;
            backdrop-filter: none;
        }
        .st-key-login_panel [data-testid="stTextInput"] label {
            color: var(--text-secondary);
            font-size: .84rem;
            font-weight: 700;
        }
        .st-key-login_panel [data-testid="stTextInput"] [data-baseweb="input"] {
            min-height: 49px;
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            background: rgba(8, 4, 18, .72);
            transition: border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
        }
        .st-key-login_panel [data-testid="stTextInput"] [data-baseweb="input"]:focus-within {
            border-color: var(--violet-400);
            box-shadow: var(--glow-focus);
        }
        .st-key-login_panel .stFormSubmitButton > button {
            min-height: 51px;
            margin-top: .55rem;
            border-color: rgba(196, 181, 253, .65);
            background: linear-gradient(115deg, #8652e8, #a56af2 58%, #8050dd);
            box-shadow: 0 12px 30px rgba(113, 55, 205, .29), inset 0 1px 0 rgba(255, 255, 255, .22);
            color: #fff;
            font-size: .95rem;
            letter-spacing: .01em;
        }
        .st-key-login_panel .stFormSubmitButton > button:hover {
            background: linear-gradient(115deg, #9c68f3, #b783f7 58%, #9563eb);
            box-shadow: 0 14px 34px rgba(137, 70, 229, .37);
        }

        /* The four real Streamlit routes share a prominent glass navigation bar. */
        .st-key-primary_navigation {
            position: sticky;
            top: 3.35rem;
            z-index: 80;
            margin: 2.2rem 0 1.35rem;
            padding: .46rem;
            background: var(--surface-solid);
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-raised), 0 0 32px rgba(139, 92, 246, .17);
        }
        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
            .st-key-primary_navigation {
                background: var(--glass-strong);
                -webkit-backdrop-filter: blur(var(--blur)) saturate(130%);
                backdrop-filter: blur(var(--blur)) saturate(130%);
            }
        }
        .st-key-primary_navigation [data-testid="stHorizontalBlock"] { gap: .45rem; }
        .st-key-primary_navigation [data-testid="stColumn"] {
            min-width: 0 !important;
            width: 25% !important;
            flex: 1 1 0 !important;
        }
        .st-key-primary_navigation [data-testid="stPageLink"] a {
            min-height: 54px;
            padding: .55rem .45rem;
            border: 1px solid transparent;
            border-radius: var(--radius-md);
            display: flex;
            justify-content: center;
            align-items: center;
            gap: .5rem;
            color: var(--text-secondary);
            font-size: .96rem;
            font-weight: 780;
            text-decoration: none;
            transition: color var(--motion-fast) ease, background var(--motion-fast) ease, border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
        }
        .st-key-primary_navigation [data-testid="stIconMaterial"] { font-size: 1.2rem !important; }
        .st-key-primary_navigation [data-testid="stPageLink"] a:hover {
            color: var(--text-primary);
            background: rgba(139, 92, 246, .11);
            border-color: var(--border-subtle);
        }
        .st-key-primary_navigation [data-testid="stPageLink"] a[aria-current="page"] {
            color: var(--text-primary);
            background: linear-gradient(135deg, rgba(165, 112, 255, .6), rgba(108, 54, 202, .62));
            border-color: var(--border-strong);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, .12), 0 0 24px rgba(163, 93, 255, .27);
        }
        .st-key-primary_navigation [data-testid="stPageLink"] p { font-size: inherit; }

        .section-label {
            display: flex;
            align-items: center;
            gap: .5rem;
            margin: .05rem 0 .22rem;
            color: var(--text-primary);
            font-size: .94rem;
            font-weight: 760;
        }
        .section-label span:first-child {
            color: var(--violet-300);
            font-size: 1.05rem;
            filter: drop-shadow(0 0 7px rgba(167, 139, 250, .2));
        }
        .section-note { color: var(--text-muted); font-size: .76rem; margin-left: auto; font-weight: 600; }
        .wellness-card {
            border-radius: var(--radius-lg);
            padding: .95rem 1rem;
            margin: .42rem 0;
        }
        .kpi-label { color: var(--text-secondary); font-size: .67rem; font-weight: 800; letter-spacing: .1em; }
        .kpi-value { color: var(--text-primary); font-size: 1.25rem; font-weight: 800; margin-top: .14rem; }
        .kpi-meta { color: var(--text-muted); font-size: .76rem; }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: .6rem;
            margin: .48rem 0;
        }
        .stat-card {
            border-radius: var(--radius-lg);
            padding: .82rem .88rem;
            min-width: 0;
            transition: border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease, transform var(--motion-fast) ease;
        }
        .stat-card:hover {
            border-color: var(--border-strong);
            box-shadow: var(--shadow-soft), var(--glow-soft);
            transform: translateY(-1px);
        }
        .stat-card .kpi-value { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .metric-list {
            border-radius: var(--radius-lg);
            overflow: hidden;
            margin: .42rem 0 .78rem;
        }
        .metric-row {
            display: grid;
            grid-template-columns: 34px minmax(0, 1fr) auto;
            align-items: center;
            gap: .65rem;
            padding: .76rem .9rem;
            border-bottom: 1px solid var(--divider);
            transition: background var(--motion-fast) ease;
        }
        .metric-row:hover { background: rgba(167, 139, 250, .045); }
        .metric-row:last-child { border-bottom: 0; }
        .metric-icon {
            width: 34px;
            height: 34px;
            display: grid;
            place-items: center;
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-sm);
            background: linear-gradient(145deg, rgba(139, 92, 246, .18), rgba(29, 18, 46, .8));
            color: var(--violet-300);
            font-size: 1rem;
        }
        .metric-name { color: var(--text-primary); font-size: .86rem; font-weight: 740; }
        .metric-value { color: var(--text-muted); font-size: .76rem; margin-top: .06rem; }
        .metric-score { color: var(--violet-300); font-size: .9rem; font-weight: 800; }

        .progress-wrap { display: grid; place-items: center; margin: .65rem 0 .8rem; }
        .progress-ring {
            width: 158px;
            height: 158px;
            border-radius: 50%;
            display: grid;
            place-items: center;
            background: conic-gradient(from -20deg, var(--neon-violet), var(--violet-500) var(--score), rgba(196, 181, 253, .12) 0);
            box-shadow: 0 0 38px rgba(139, 92, 246, .2), inset 0 0 18px rgba(255, 255, 255, .05);
            animation: neon-breathe 5s ease-in-out infinite alternate;
        }
        .progress-inner {
            width: 130px;
            height: 130px;
            border-radius: 50%;
            background: radial-gradient(circle at 45% 35%, var(--surface-soft), var(--canvas-1) 72%);
            border: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: inset 0 8px 24px rgba(0, 0, 0, .24);
        }
        .progress-number { color: var(--text-primary); font-size: 2.25rem; font-weight: 820; line-height: 1; }
        .progress-caption { color: var(--text-secondary); font-size: .64rem; letter-spacing: .12em; margin-top: .45rem; }
        .message-card {
            border-color: var(--border-strong);
            border-radius: var(--radius-lg);
            padding: .95rem 1.05rem;
            color: var(--text-primary);
            margin-top: .72rem;
        }
        .complete-card {
            border-color: rgba(185, 103, 255, .54);
            text-align: center;
            box-shadow: var(--shadow-soft), 0 0 30px rgba(139, 92, 246, .13);
        }

        .record-summary {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: .75rem;
            align-items: center;
            padding: .1rem 0 .55rem;
        }
        .record-date { font-size: .71rem; font-weight: 800; letter-spacing: .09em; color: var(--violet-400); }
        .record-glance { color: var(--text-secondary); font-size: .8rem; margin-top: .2rem; }
        .record-score { font-size: 1.45rem; font-weight: 820; color: var(--text-primary); }
        .record-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: .38rem 0;
            border-bottom: 1px solid var(--divider);
            font-size: .88rem;
        }
        .record-row:last-child { border-bottom: 0; }
        .record-label { color: var(--text-secondary); }
        .record-value { color: var(--text-primary); font-weight: 700; text-align: right; }
        .trend-summary {
            border-radius: var(--radius-lg);
            padding: .85rem .95rem;
            margin: .48rem 0;
        }
        .trend-summary-head { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }
        .trend-title { font-weight: 780; color: var(--text-primary); }
        .trend-count { font-size: .71rem; color: var(--text-muted); }
        .trend-values { color: var(--violet-300); font-size: .88rem; margin-top: .4rem; }
        .insight-panel { border-radius: var(--radius-lg); padding: .8rem .95rem; margin: .58rem 0; }
        .insight-panel ul { margin: .38rem 0 .12rem; padding-left: 1.15rem; }
        .insight-panel li { color: var(--text-secondary); margin: .32rem 0; font-size: .87rem; }
        .insight-panel li::marker { color: var(--violet-400); }
        .meal-label {
            color: var(--violet-400);
            font-size: .67rem;
            font-weight: 800;
            letter-spacing: .1em;
            margin: .28rem 0 -.34rem;
        }
        [data-testid="stMetric"], [data-testid="stPlotlyChart"] { border-radius: var(--radius-lg); }
        [data-testid="stPlotlyChart"] { overflow: hidden; }

        @keyframes glass-enter {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes neon-breathe {
            from { filter: saturate(.96); box-shadow: 0 0 28px rgba(139, 92, 246, .15); }
            to { filter: saturate(1.08); box-shadow: 0 0 42px rgba(139, 92, 246, .24); }
        }
        .metric-list, .stat-card, .message-card, .trend-summary, .insight-panel,
        div[data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stExpander"] {
            animation: glass-enter var(--motion-normal) var(--ease-out) both;
        }

        @media (min-width: 760px) {
            .stat-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        }
        @media (max-width: 480px) {
            .block-container {
                padding-top: .55rem;
                padding-left: .9rem;
                padding-right: .9rem;
            }
            .st-key-login_panel { margin: 3.75rem auto 1.25rem; padding: 1.35rem 1.15rem 1.5rem; }
            .login-hero { padding-bottom: 1.25rem; }
            .st-key-primary_navigation { top: 3.35rem; margin-top: 2.1rem; margin-bottom: 1rem; padding: .3rem; border-radius: var(--radius-lg); }
            .st-key-primary_navigation [data-testid="stHorizontalBlock"] { gap: .15rem; }
            .st-key-primary_navigation [data-testid="stPageLink"] a { min-height: 48px; padding: .38rem .12rem; font-size: .75rem; gap: .18rem; }
            .st-key-primary_navigation [data-testid="stPageLink"] p { font-size: .75rem !important; }
            .st-key-primary_navigation [data-testid="stIconMaterial"] { font-size: 1rem !important; }
            .stat-grid { gap: .5rem; }
            .stat-card { padding: .74rem .78rem; }
            .progress-ring { width: 148px; height: 148px; }
            .progress-inner { width: 122px; height: 122px; }
            .progress-number { font-size: 2.05rem; }
            .record-row { gap: .65rem; }
        }
        @media (max-width: 340px) {
            .st-key-primary_navigation [data-testid="stPageLink"] a { font-size: .69rem; }
            .st-key-primary_navigation [data-testid="stPageLink"] p { font-size: .69rem !important; }
            .st-key-primary_navigation [data-testid="stIconMaterial"] { display: none; }
            .metric-row { padding-left: .7rem; padding-right: .7rem; }
            h1 { font-size: 1.45rem !important; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after {
                scroll-behavior: auto !important;
                animation-duration: .01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: .01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@lru_cache(maxsize=1)
def _journal_background_uri() -> str:
    """Encode one mobile-sized copy of the supplied History/Progress artwork."""
    artwork = Path(__file__).resolve().parents[1] / "assets" / "fairy-night-history-progress.png"
    with Image.open(artwork) as image:
        image.thumbnail((1200, 800))
        output = BytesIO()
        image.save(output, format="WEBP", quality=70, method=4)
    return "data:image/webp;base64," + base64.b64encode(output.getvalue()).decode("ascii")


def apply_journal_background() -> None:
    """Opt-in moonlit backdrop for History and Progress, never other pages."""
    st.html(
        '<span class="erumaa-journal-background-marker" hidden aria-hidden="true"></span>'
        '<style>'
        '.stApp:has(.erumaa-journal-background-marker) {'
        'background: var(--canvas-0); isolation: isolate;'
        '}'
        '.stApp:has(.erumaa-journal-background-marker)::before {'
        'content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none;'
        'background-image: '
        'linear-gradient(90deg, rgba(5,2,8,.46), rgba(5,2,8,.78) 25%, '
        'rgba(5,2,8,.88) 55%, rgba(5,2,8,.74) 80%, rgba(5,2,8,.44)),'
        'linear-gradient(180deg, rgba(5,2,8,.12), rgba(5,2,8,.34) 55%, rgba(5,2,8,.68)),'
        f'url("{_journal_background_uri()}");'
        'background-size: cover; background-position: right top; background-repeat: no-repeat;'
        '}'
        '</style>'
    )


def apply_journal_page_styles() -> None:
    """Opt-in journal and analytics components, scoped away from Home and Today."""
    st.html("""
    <style>
    .st-key-history_page, .st-key-progress_page { gap: .85rem; }
    .st-key-history_header, .st-key-progress_header {
        padding: .35rem 0 .75rem;
        border-bottom: 1px solid var(--border-subtle);
    }
    .st-key-history_header h1, .st-key-progress_header h1 {
        font-size: clamp(1.9rem, 5vw, 2.65rem) !important;
        margin: .22rem 0 .25rem !important;
        background: linear-gradient(100deg, var(--text-primary) 28%, var(--violet-300));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .st-key-history_header .subtle, .st-key-progress_header .subtle {
        font-size: .96rem;
        margin: 0;
    }
    .journal-eyebrow {
        color: var(--violet-300);
        font-size: .73rem;
        font-weight: 800;
        letter-spacing: .15em;
        text-transform: uppercase;
    }
    .journal-section-heading {
        display: flex;
        align-items: baseline;
        justify-content: space-between;
        gap: .8rem;
        margin: .45rem 0 .2rem;
    }
    .journal-section-heading h2 {
        margin: 0 !important;
        font-size: 1.17rem !important;
        font-weight: 760;
    }
    .journal-section-heading span { color: var(--text-secondary); font-size: .81rem; }
    .journal-stat-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .65rem;
        margin: .18rem 0 .35rem;
    }
    .journal-stat {
        min-width: 0;
        padding: .9rem .95rem;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        background: linear-gradient(145deg, rgba(36, 23, 57, .9), rgba(13, 8, 24, .94));
        box-shadow: var(--shadow-soft), inset 0 1px 0 var(--glass-highlight);
        transition: border-color var(--motion-fast) ease, transform var(--motion-fast) ease;
    }
    .journal-stat:hover { border-color: var(--border-strong); transform: translateY(-2px); }
    .journal-stat-label { color: var(--text-secondary); font-size: .74rem; font-weight: 750; letter-spacing: .055em; }
    .journal-stat-value {
        margin-top: .28rem;
        color: var(--text-primary);
        font-size: clamp(1.35rem, 3vw, 1.75rem);
        font-weight: 800;
        line-height: 1.15;
        overflow-wrap: anywhere;
    }
    .journal-stat-meta { margin-top: .2rem; color: var(--text-secondary); font-size: .77rem; }
    .journal-stat-accent { border-color: var(--border-strong); }
    .journal-stat-accent .journal-stat-value { color: var(--violet-300); }
    .st-key-history_timeline {
        margin: .15rem 0 .6rem .32rem;
        padding-left: 1rem;
        border-left: 1px solid var(--border-strong);
    }
    .st-key-history_page [class*="st-key-journal_entry_"] {
        position: relative;
        padding: .68rem .78rem .72rem;
        margin: 0 0 .66rem;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        background: linear-gradient(145deg, rgba(32, 20, 50, .95), rgba(12, 8, 23, .96));
        box-shadow: var(--shadow-soft);
        gap: .28rem;
    }
    .st-key-history_page [class*="st-key-journal_entry_"]::before {
        content: "";
        position: absolute;
        top: 1.28rem;
        left: -1.39rem;
        width: .55rem;
        height: .55rem;
        border: 2px solid var(--violet-300);
        border-radius: 50%;
        background: var(--canvas-1);
        box-shadow: 0 0 12px rgba(167, 139, 250, .3);
    }
    .journal-entry-head { display: flex; align-items: center; gap: .7rem; min-width: 0; }
    .journal-entry-copy { min-width: 0; flex: 1; }
    .journal-entry-date { color: var(--text-primary); font-size: 1rem; font-weight: 780; line-height: 1.25; }
    .journal-entry-meta { color: var(--text-secondary); font-size: .78rem; margin-top: .16rem; }
    .journal-entry-status { color: var(--violet-300); font-size: .76rem; font-weight: 700; margin-top: .3rem; }
    .journal-entry-status.read-only { color: var(--text-secondary); }
    .journal-score-badge {
        display: grid;
        place-items: center;
        flex: 0 0 58px;
        width: 58px;
        height: 58px;
        border-radius: 50%;
        background: conic-gradient(var(--violet-300) var(--score), rgba(196, 181, 253, .14) 0);
    }
    .journal-score-badge > span {
        display: grid;
        place-items: center;
        width: 49px;
        height: 49px;
        border-radius: 50%;
        background: var(--canvas-1);
        color: var(--text-primary);
        font-size: .85rem;
        font-weight: 800;
    }
    .journal-score-badge.untracked { background: var(--surface-soft); border: 1px dashed var(--border-strong); }
    .st-key-history_page [data-testid="stExpander"] {
        margin-top: .18rem;
        border-color: var(--border-subtle);
        border-radius: var(--radius-md);
        box-shadow: none;
        background: rgba(10, 5, 18, .68);
    }
    .st-key-history_page [data-testid="stExpander"] details > summary {
        min-height: 44px;
        color: var(--violet-300);
        font-size: .87rem;
        font-weight: 720;
    }
    .journal-detail-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: .55rem;
        margin: .2rem 0 .65rem;
    }
    .journal-detail-group {
        min-width: 0;
        padding: .72rem .78rem;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        background: rgba(15, 9, 27, .75);
    }
    .journal-detail-group h3 { margin: 0 0 .4rem !important; color: var(--violet-300); font-size: .81rem !important; }
    .journal-detail-row {
        display: flex;
        justify-content: space-between;
        gap: .65rem;
        padding: .26rem 0;
        border-top: 1px solid var(--divider);
        font-size: .79rem;
    }
    .journal-detail-row span:first-child { color: var(--text-secondary); }
    .journal-detail-row span:last-child { color: var(--text-primary); font-weight: 700; text-align: right; }
    .journal-note, .journal-empty, .journal-reflection {
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        background: linear-gradient(145deg, rgba(31, 19, 49, .93), rgba(12, 7, 23, .95));
        box-shadow: var(--shadow-soft);
    }
    .journal-note { padding: .75rem .85rem; margin: .4rem 0; }
    .journal-note p { color: var(--text-primary); font-size: .88rem; margin: .32rem 0 0; }
    .journal-empty { padding: 1.2rem; margin: .55rem 0; }
    .journal-empty h2 { font-size: 1.25rem !important; margin: .2rem 0 .4rem !important; }
    .journal-empty p { color: var(--text-secondary); font-size: .9rem; margin: 0; }
    .st-key-progress_page [role="radiogroup"][aria-label="Time period"] {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .2rem;
        width: 100%;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        background: rgba(10, 5, 18, .85);
        padding: .22rem;
    }
    .st-key-progress_page [role="radiogroup"][aria-label="Time period"] button {
        min-width: 0;
        width: 100%;
        min-height: 42px;
        padding: .25rem .2rem;
        border-radius: var(--radius-sm);
        font-size: .82rem;
    }
    .st-key-progress_page [role="radiogroup"][aria-label="Time period"] button p {
        font-size: inherit;
        line-height: 1.15;
        white-space: normal;
        text-align: center;
    }
    .st-key-progress_page [role="radiogroup"][aria-label="Time period"] button[data-selected="true"] {
        border-color: var(--violet-400);
        background: linear-gradient(120deg, rgba(125, 58, 221, .7), rgba(88, 43, 160, .85));
        color: var(--text-primary);
    }
    .st-key-progress_page .stat-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .55rem; }
    .st-key-progress_page .stat-card {
        padding: .84rem .9rem;
        background: linear-gradient(145deg, rgba(32, 20, 50, .94), rgba(12, 7, 23, .95));
    }
    .st-key-progress_page .stat-card .kpi-label { font-size: .71rem; }
    .st-key-progress_page .stat-card .kpi-value { font-size: 1.43rem; white-space: normal; }
    .st-key-progress_page .stat-card .kpi-meta { font-size: .77rem; }
    .st-key-progress_page [class*="st-key-journal_chart_"] {
        padding: .75rem .82rem;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        background: rgba(19, 11, 32, .9);
        box-shadow: var(--shadow-soft);
        gap: .35rem;
    }
    .journal-chart-heading h2 { font-size: 1.1rem !important; margin: 0 !important; }
    .journal-chart-heading p { color: var(--text-secondary); font-size: .79rem; margin: .13rem 0 0; }
    .journal-chart-empty { padding: 1.35rem .35rem; color: var(--text-secondary); font-size: .87rem; }
    .st-key-progress_page [data-testid="stPlotlyChart"] { border: 0; background: transparent; box-shadow: none; }
    .st-key-progress_page [data-testid="stTabs"] [role="tab"] { min-height: 44px; font-size: .85rem; }
    .journal-reflection { padding: .9rem 1rem; }
    .journal-reflection-head { display: flex; justify-content: space-between; gap: .6rem; align-items: baseline; }
    .journal-reflection h2 { font-size: 1.12rem !important; margin: 0 !important; }
    .journal-reflection-head span { color: var(--violet-300); font-size: .76rem; font-weight: 750; }
    .journal-reflection-item { padding: .5rem 0; color: var(--text-secondary); font-size: .86rem; border-top: 1px solid var(--divider); }
    .journal-reflection-item:first-of-type { margin-top: .55rem; }
    @media (max-width: 600px) {
        .journal-stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .journal-stat-grid .journal-stat:last-child { grid-column: 1 / -1; }
        .journal-detail-grid { grid-template-columns: minmax(0, 1fr); }
        .st-key-progress_page .stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .st-key-progress_page .stat-grid > .stat-card:last-child:nth-child(odd) { grid-column: 1 / -1; }
    }
    @media (max-width: 360px) {
        .journal-entry-date { font-size: .93rem; }
        .journal-score-badge { flex-basis: 54px; width: 54px; height: 54px; }
        .journal-score-badge > span { width: 45px; height: 45px; font-size: .8rem; }
        .st-key-progress_page [role="radiogroup"][aria-label="Time period"] button { font-size: .78rem; }
    }
    </style>
    """)


def apply_today_styles() -> None:
    """Style the opt-in Today surface without affecting History's edit form."""
    st.html("""
    <style>
    .st-key-today_page { gap: .75rem; }
    .st-key-today_header {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        min-height: 130px;
        padding: .7rem .75rem .8rem;
        border-bottom: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        background:
            radial-gradient(circle at 84% 22%, rgba(184, 122, 255, .18), transparent 9rem),
            var(--canvas-1);
        margin-bottom: .1rem;
        gap: .2rem;
    }
    .st-key-today_header::before {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        background-size: cover, auto 225px;
        background-position: center, right center;
        background-repeat: no-repeat;
        opacity: .22;
    }
    .st-key-today_header > * { position: relative; z-index: 1; }
    .st-key-today_header .brand-kicker { margin-bottom: .15rem; }
    .st-key-today_header .subtle {
        margin: .18rem 0 0;
        color: var(--text-secondary);
        font-size: .88rem;
    }
    .st-key-today_header h1 {
        font-size: clamp(1.9rem, 7vw, 2.75rem) !important;
        margin: .12rem 0 .15rem !important;
    }
    .st-key-today_header [data-testid="stCaptionContainer"] {
        color: var(--violet-300);
        font-size: .87rem;
        font-weight: 650;
    }
    .st-key-today_page [class*="_section"] {
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-lg);
        padding: .95rem 1.05rem;
        background: linear-gradient(135deg, var(--surface-raised), var(--canvas-2));
        box-shadow: var(--shadow-soft), inset 0 1px 0 var(--glass-highlight);
        gap: .58rem;
        animation: none;
    }
    @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {
        .st-key-today_page [class*="_section"] {
            background: linear-gradient(135deg, var(--glass-highlight), transparent 65%), var(--glass-strong);
            -webkit-backdrop-filter: blur(var(--blur));
            backdrop-filter: blur(var(--blur));
        }
    }
    .today-card-heading {
        display: flex;
        align-items: center;
        gap: .6rem;
        margin-bottom: .1rem;
    }
    .today-card-heading h2 {
        font-size: 1.08rem !important;
        margin: 0 !important;
        line-height: 1.3;
        font-weight: 750;
    }
    .today-card-icon {
        display: grid;
        place-items: center;
        flex: 0 0 32px;
        height: 32px;
        border-radius: var(--radius-sm);
        border: 1px solid var(--border-subtle);
        background: var(--surface-soft);
        color: var(--violet-300);
        box-shadow: var(--glow-soft);
    }
    .today-card-glyph {
        width: 19px;
        height: 19px;
        background: currentColor;
        -webkit-mask: var(--habit-icon) center / contain no-repeat;
        mask: var(--habit-icon) center / contain no-repeat;
    }
    .today-card-note {
        margin-left: auto;
        color: var(--text-secondary);
        font-size: .8rem;
    }
    .st-key-today_page [data-testid="stWidgetLabel"] p {
        color: var(--text-secondary);
        font-size: .91rem;
        line-height: 1.35;
    }
    .st-key-today_page [data-testid="stNumberInput"] [data-baseweb="input"],
    .st-key-today_page [data-testid="stTextArea"] [data-baseweb="textarea"] {
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        background: var(--canvas-1);
        transition: border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
    }
    .st-key-today_page [data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
    .st-key-today_page [data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within {
        border-color: var(--violet-300);
        box-shadow: var(--glow-focus);
    }
    .st-key-today_page [data-testid="stNumberInput"] input {
        min-height: 44px;
        color: var(--violet-300);
        font-size: 1.08rem;
        font-weight: 700;
    }
    .st-key-today_page [data-testid="stNumberInput"] button {
        min-height: 44px;
        min-width: 44px;
        color: var(--violet-300);
        border-left: 1px solid var(--divider);
    }
    .st-key-today_page input:disabled { opacity: .48; }
    .st-key-today_page [data-testid="stElementContainer"]:has(> [data-testid="stRadio"]) {
        width: 100%;
    }
    .st-key-today_page [role="radiogroup"] {
        display: flex;
        width: 100%;
        flex-wrap: nowrap;
        gap: .25rem;
        padding: .22rem;
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        background: var(--canvas-1);
    }
    .st-key-today_page [role="radiogroup"] > div {
        flex: 1 1 0;
        min-width: 0;
    }
    .st-key-today_page [role="radiogroup"] label {
        flex: 1 1 0;
        width: 100%;
        min-width: 0;
        min-height: 42px;
        justify-content: center;
        margin: 0;
        padding: .3rem .45rem;
        border: 1px solid transparent;
        border-radius: var(--radius-sm);
        background: transparent;
        color: var(--text-secondary);
    }
    .st-key-today_page [data-testid="stRadioOption"] > div {
        justify-content: center;
        width: 100%;
    }
    /* Hide the decorative dot, retaining the native input and keyboard behavior. */
    @supports selector(label:has(input:checked)) {
        .st-key-today_page [data-testid="stRadioOption"] > div > div:first-child {
            display: none;
        }
    }
    .st-key-today_page [role="radiogroup"] label p {
        font-size: .9rem;
        font-weight: 700;
        letter-spacing: .025em;
    }
    .st-key-today_page [role="radiogroup"] label:hover {
        background: var(--surface-raised);
        border-color: var(--border-subtle);
    }
    @supports selector(label:has(input:checked)) {
        .st-key-today_page [role="radiogroup"] label:has(input:checked) {
            color: var(--text-primary);
            border-color: var(--violet-400);
            background: linear-gradient(125deg, var(--violet-600), var(--violet-500));
            box-shadow: inset 0 1px 0 var(--glass-highlight);
        }
        .st-key-today_page [role="radiogroup"] label:has(input:focus-visible) {
            outline: 2px solid var(--violet-300);
            outline-offset: 2px;
        }
    }
    .st-key-today_page [class*="_meal_row"],
    .st-key-today_page [class*="_food_extra"] {
        padding: .58rem 0;
        border-top: 1px solid var(--divider);
        gap: .28rem;
    }
    .st-key-today_page .meal-label {
        margin: 0;
        font-size: .81rem;
        color: var(--violet-300);
        letter-spacing: .1em;
    }
    .st-key-today_page [data-testid="stCaptionContainer"] {
        color: var(--text-secondary);
        font-size: .8rem;
        line-height: 1.5;
    }
    .st-key-today_page textarea {
        min-height: 100px;
        font-size: .94rem;
        line-height: 1.6;
    }
    .st-key-today_page textarea::placeholder { color: var(--text-muted); opacity: 1; }
    .st-key-today_save_bar button {
        min-height: 46px;
        color: var(--text-primary);
        font-size: .92rem;
        font-weight: 750;
        border: 1px solid var(--violet-400);
        border-radius: var(--radius-md);
        background: linear-gradient(115deg, var(--violet-500), var(--violet-600));
        box-shadow: 0 8px 20px rgba(90, 40, 160, .2), inset 0 1px 0 var(--glass-highlight);
    }
    .st-key-today_save_bar button:hover {
        border-color: var(--violet-300);
        background: linear-gradient(115deg, var(--violet-600), var(--violet-500));
        box-shadow: 0 9px 22px rgba(90, 40, 160, .28);
    }
    .st-key-today_save_bar button:active { transform: translateY(1px); }
    @media (max-width: 700px) {
        body:has(.st-key-today_page) [data-testid="stToastContainer"] {
            width: min(336px, calc(100vw - 2rem));
            max-width: calc(100vw - 2rem);
        }
        body:has(.st-key-today_page) [data-testid="stToast"] { width: 100%; }
        .st-key-today_page {
            padding-bottom: calc(5.6rem + env(safe-area-inset-bottom, 0px));
        }
        .st-key-today_page [class*="_section"] { padding: .85rem .9rem; }
        .st-key-today_save_bar {
            position: fixed;
            z-index: 90;
            inset: auto 0 0;
            width: auto;
            padding: .5rem max(.85rem, env(safe-area-inset-right, 0px))
                calc(.5rem + env(safe-area-inset-bottom, 0px)) max(.85rem, env(safe-area-inset-left, 0px));
            border-top: 1px solid var(--border-strong);
            background: var(--canvas-1);
            box-shadow: 0 -12px 32px rgba(0, 0, 0, .28);
        }
        .st-key-today_save_bar button { width: 100%; }
    }
    @media (max-width: 360px) {
        .st-key-today_page [class*="_section"] { padding: .78rem .8rem; }
        .st-key-today_page [role="radiogroup"] { gap: .15rem; }
        .st-key-today_page [role="radiogroup"] label { padding: .28rem .2rem; }
        .st-key-today_page [role="radiogroup"] label p { font-size: .88rem; letter-spacing: 0; }
    }
    @media (max-width: 700px) and (max-height: 550px) {
        /* A short visual viewport (for example with a soft keyboard) should not be covered. */
        .st-key-today_save_bar { position: static; }
        .st-key-today_page { padding-bottom: 1rem; }
    }
    </style>
    """)


def habit_heading(icon: str, title: str, note: str = "") -> None:
    """A small, monochrome icon and escaped heading for Today habit cards."""
    paths = {
        "sleep": '<path d="M20.4 13.1A8.5 8.5 0 0 1 10.9 3.6 8.5 8.5 0 1 0 20.4 13.1Z"/>',
        "exercise": '<path d="m5 8 3-3m8 14 3-3M3 6l3-3m12 18 3-3M5 5l14 14M3 10l7-7m4 18 7-7"/>',
        "food": '<path d="M20 4C8 2 3 9 6 15s14 3 14-11ZM5 21 16 10"/>',
        "water": '<path d="M12 3C9 7 5 11 5 15a7 7 0 0 0 14 0c0-4-4-8-7-12ZM8 15a4 4 0 0 0 4 4"/>',
        "selfcare": '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5ZM20 2v4m-2-2h4"/>',
        "stress": '<path d="M3 8c3-4 6 4 9 0s6 4 9 0M3 13c3-4 6 4 9 0s6 4 9 0M3 18c3-4 6 4 9 0s6 4 9 0"/>',
        "mood": '<circle cx="12" cy="12" r="9"/><path d="M8 14a4 4 0 0 0 8 0M8 9h.01M16 9h.01"/>',
        "note": '<path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15v5ZM12 20h8"/>',
    }
    # st.html sanitizes inline SVG; a self-contained mask keeps the token color.
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{paths[icon]}</svg>'
    encoded_icon = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    icon_style = f"--habit-icon:url(data:image/svg+xml;base64,{encoded_icon})"
    note_html = f'<span class="today-card-note">{html.escape(note)}</span>' if note else ""
    st.html(
        f'<div class="today-card-heading"><span class="today-card-icon" aria-hidden="true">'
        f'<span class="today-card-glyph" style="{icon_style}"></span></span>'
        f'<h2>{html.escape(title)}</h2>{note_html}</div>'
    )


def render_primary_navigation(*, icon_only: bool = False) -> None:
    """Render the visible mobile-first navigation using genuine Streamlit routes."""
    with st.container(key="primary_navigation_home" if icon_only else "primary_navigation"):
        columns = st.columns(4, gap="small")
        links = (
            ("pages/home.py", "Home", ":material/home:"),
            ("pages/today.py", "Today", ":material/event_available:"),
            ("pages/history.py", "History", ":material/history:"),
            ("pages/progress.py", "Progress", ":material/monitoring:"),
        )
        for column, (page, label, icon) in zip(columns, links):
            with column:
                st.page_link(page, label=label, icon=icon, help=label, width="stretch")


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
        with st.expander("Settings", icon=":material/settings:", key="settings_menu"):
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
