"""Home dashboard."""

from __future__ import annotations

import base64
import html
from pathlib import Path

import streamlit as st

from src.auth import current_user_id, get_supabase_client
from src.database import DailyLogRepository, RepositoryError
from src.messages import greeting, message_for_day
from src.scoring import calculate_current_streak, calculate_weekly_average
from src.timezone_utils import india_now, india_today, week_bounds
from src.ui import (
    message_card,
    metric_list,
    progress_ring,
    render_primary_navigation,
    render_settings,
    section_label,
    stat_grid,
)


_HOME_IMAGE_PATH = Path(__file__).resolve().parents[1] / "assets" / "home-fairy-twilight.png"
_HOME_IMAGE_DATA = base64.b64encode(_HOME_IMAGE_PATH.read_bytes()).decode("ascii")


def _render_home_hero(title: str, subtitle: str) -> None:
    """Render the Home greeting over the bundled twilight illustration."""
    safe_title = "&nbsp;".join(html.escape(part) for part in title.rsplit(" ", 1))
    safe_subtitle = html.escape(subtitle)
    st.html(
        f"""
        <style>
        .block-container {{
            max-width: 1180px;
        }}

        .st-key-primary_navigation_home {{
            position: sticky;
            top: 3.35rem;
            z-index: 80;
            margin: 2.2rem 0 1.35rem;
            padding: .45rem;
            border: 1px solid var(--border-strong);
            border-radius: var(--radius-xl);
            background: var(--surface-solid);
            box-shadow: var(--shadow-raised), 0 0 32px rgba(139, 92, 246, .17);
        }}

        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {{
            .st-key-primary_navigation_home {{
                background: var(--glass-strong);
                -webkit-backdrop-filter: blur(var(--blur)) saturate(130%);
                backdrop-filter: blur(var(--blur)) saturate(130%);
            }}
        }}

        .st-key-primary_navigation_home [data-testid="stHorizontalBlock"] {{ gap: .5rem; }}
        .st-key-primary_navigation_home [data-testid="stColumn"] {{
            min-width: 0 !important;
            width: 25% !important;
            flex: 1 1 0 !important;
        }}
        .st-key-primary_navigation_home [data-testid="stPageLink"] a {{
            display: flex;
            min-height: 54px;
            align-items: center;
            justify-content: center;
            padding: .55rem;
            border: 1px solid transparent;
            border-radius: var(--radius-md);
            color: var(--violet-300);
            text-decoration: none;
            transition: color var(--motion-fast) ease, background var(--motion-fast) ease, border-color var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
        }}
        .st-key-primary_navigation_home [data-testid="stPageLink"] p {{
            position: absolute !important;
            width: 1px !important;
            height: 1px !important;
            padding: 0 !important;
            margin: -1px !important;
            overflow: hidden !important;
            clip-path: inset(50%) !important;
            white-space: nowrap !important;
            border: 0 !important;
        }}
        .st-key-primary_navigation_home [data-testid="stIconMaterial"] {{
            display: inline-flex !important;
            font-size: 1.48rem !important;
        }}
        .st-key-primary_navigation_home [data-testid="stPageLink"] a:hover {{
            color: var(--text-primary);
            background: rgba(139, 92, 246, .13);
            border-color: var(--border-subtle);
        }}
        .st-key-primary_navigation_home [data-testid="stPageLink"] a[aria-current="page"],
        .st-key-primary_navigation_home [data-testid="stPageLink"] a[href=""] {{
            color: #fff;
            background: linear-gradient(135deg, rgba(165, 112, 255, .78), rgba(108, 54, 202, .76));
            border-color: var(--violet-300);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, .17), 0 0 25px rgba(163, 93, 255, .32);
        }}

        .home-hero {{
            position: relative;
            isolation: isolate;
            min-height: clamp(23rem, 36vw, 27.5rem);
            margin: 0.25rem 0 2rem;
            overflow: hidden;
            border: 1px solid var(--border-strong);
            border-radius: 28px;
            background: var(--surface-solid);
            box-shadow:
                0 28px 80px rgba(0, 0, 0, 0.46),
                0 0 54px rgba(139, 92, 246, 0.14),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
        }}

        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {{
            .home-hero {{
                background:
                    linear-gradient(118deg, rgba(11, 5, 24, 0.96), rgba(32, 15, 68, 0.74)),
                    var(--glass);
                -webkit-backdrop-filter: blur(var(--blur)) saturate(132%);
                backdrop-filter: blur(var(--blur)) saturate(132%);
            }}
        }}

        .home-hero::before {{
            content: "";
            position: absolute;
            z-index: 2;
            inset: 0;
            pointer-events: none;
            background:
                linear-gradient(90deg, rgba(5, 2, 12, 0.94) 0%, rgba(8, 3, 18, 0.7) 32%, rgba(8, 3, 18, 0.08) 67%, transparent 100%),
                linear-gradient(0deg, rgba(5, 2, 10, 0.42), transparent 42%);
        }}

        .home-hero::after {{
            content: "";
            position: absolute;
            z-index: 2;
            inset: 0;
            pointer-events: none;
            background:
                radial-gradient(circle 3px at 61% 25%, rgba(244, 224, 255, 0.95), transparent 5px),
                radial-gradient(circle 2px at 78% 54%, rgba(233, 195, 255, 0.9), transparent 4px),
                radial-gradient(circle 2px at 54% 63%, rgba(200, 151, 255, 0.86), transparent 4px);
            animation: home-sparkle 4.8s ease-in-out infinite alternate;
        }}

        @keyframes home-sparkle {{
            from {{ opacity: 0.22; }}
            to {{ opacity: 0.85; }}
        }}

        .home-hero-copy {{
            position: relative;
            z-index: 3;
            display: flex;
            min-height: clamp(23rem, 36vw, 27.5rem);
            width: min(58%, 38rem);
            flex-direction: column;
            justify-content: center;
            padding: clamp(2.2rem, 4.5vw, 3.6rem);
        }}

        .home-hero-title {{
            max-width: 13ch;
            margin: 0.8rem 0 0.9rem !important;
            color: var(--text-primary);
            font-family: var(--font-system);
            font-size: clamp(2.55rem, 4.9vw, 3.7rem) !important;
            font-weight: 760;
            letter-spacing: -0.052em;
            line-height: 0.98 !important;
            text-wrap: balance;
        }}

        .home-hero-subtitle {{
            margin: 0;
            color: var(--text-secondary);
            font-size: clamp(1rem, 1.7vw, 1.16rem);
            line-height: 1.5;
        }}

        .home-hero-art {{
            position: absolute;
            z-index: 1;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: right center;
            transform: scale(1.025);
            animation: home-art-float 8s ease-in-out infinite alternate;
        }}

        @keyframes home-art-float {{
            from {{ transform: scale(1.025) translateY(0); }}
            to {{ transform: scale(1.025) translateY(-5px); }}
        }}

        .st-key-home_overview {{
            position: relative;
            margin-bottom: 1.6rem;
            padding: clamp(1.35rem, 3.2vw, 2rem);
            overflow: hidden;
            border: 1px solid var(--border-strong);
            border-radius: 24px;
            background: var(--surface-solid);
            box-shadow: var(--shadow-raised), var(--glow-soft), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }}

        .st-key-home_overview::before {{
            content: "";
            position: absolute;
            inset: -45% auto auto -10%;
            width: 20rem;
            height: 20rem;
            border-radius: 999px;
            background: rgba(147, 84, 255, 0.17);
            filter: blur(64px);
            pointer-events: none;
        }}

        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {{
            .st-key-home_overview {{
                background: linear-gradient(135deg, rgba(30, 17, 49, 0.86), rgba(15, 8, 27, 0.82));
                -webkit-backdrop-filter: blur(var(--blur)) saturate(125%);
                backdrop-filter: blur(var(--blur)) saturate(125%);
            }}
        }}

        .st-key-home_overview .progress-wrap {{
            margin: 1.1rem 0 0.45rem;
        }}

        .st-key-home_overview .progress-ring {{
            width: clamp(210px, 22vw, 252px);
            height: clamp(210px, 22vw, 252px);
            box-shadow: 0 0 58px rgba(139, 92, 246, 0.34), inset 0 0 24px rgba(255, 255, 255, 0.06);
            animation: home-score-glow 5s ease-in-out infinite alternate;
        }}

        @keyframes home-score-glow {{
            from {{ box-shadow: 0 0 40px rgba(139, 92, 246, 0.25), inset 0 0 20px rgba(255, 255, 255, 0.05); }}
            to {{ box-shadow: 0 0 68px rgba(169, 104, 255, 0.42), inset 0 0 24px rgba(255, 255, 255, 0.08); }}
        }}

        .st-key-home_overview .progress-inner {{
            width: calc(clamp(210px, 22vw, 252px) - 34px);
            height: calc(clamp(210px, 22vw, 252px) - 34px);
        }}

        .st-key-home_overview .progress-number {{
            font-size: clamp(3rem, 5vw, 4rem);
        }}

        .st-key-home_overview .progress-caption {{
            font-size: 0.72rem;
        }}

        .st-key-home_overview .metric-list {{
            margin-bottom: 0;
        }}

        .st-key-home_habits {{
            margin: 0 0 1.65rem;
        }}

        .home-habit-grid {{
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.8rem;
            margin-top: 0.75rem;
        }}

        .home-habit-card {{
            display: flex;
            min-width: 0;
            min-height: 8.2rem;
            flex-direction: column;
            align-items: flex-start;
            padding: 1.1rem 1.2rem;
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-lg);
            background: var(--surface-solid);
            box-shadow: var(--shadow-soft), 0 0 24px rgba(139, 92, 246, 0.07);
        }}

        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {{
            .home-habit-card {{
                background: linear-gradient(145deg, rgba(255, 255, 255, 0.04), transparent 44%), var(--glass);
                -webkit-backdrop-filter: blur(var(--blur));
                backdrop-filter: blur(var(--blur));
            }}
        }}

        .home-habit-index {{
            color: var(--violet-400);
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.12em;
        }}

        .home-habit-label {{
            margin-top: 0.8rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 680;
        }}

        .home-habit-value {{
            margin-top: 0.2rem;
            color: var(--text-primary);
            font-size: clamp(1rem, 1.7vw, 1.3rem);
            font-weight: 780;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }}

        .st-key-home_weekly {{
            margin: 0.35rem 0 1.5rem;
        }}

        .st-key-home_weekly .stat-grid {{
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 0.75rem;
        }}

        .st-key-home_weekly .stat-card {{
            min-height: 8.25rem;
            padding: 1.25rem 1.35rem;
            border-color: var(--border-strong);
            background: linear-gradient(145deg, rgba(35, 20, 57, 0.9), rgba(16, 9, 29, 0.84));
            box-shadow: 0 15px 42px rgba(0, 0, 0, 0.26), 0 0 28px rgba(139, 92, 246, 0.09);
        }}

        .st-key-home_weekly .kpi-value {{
            margin: 0.55rem 0 0.35rem;
            color: var(--violet-300);
            font-size: clamp(1.65rem, 3vw, 2.25rem);
        }}

        .st-key-home_footer {{
            margin-top: 0.8rem;
            padding: 0.35rem 0 1.5rem;
        }}

        .st-key-home_footer .message-card {{
            position: relative;
            isolation: isolate;
            min-height: 6rem;
            overflow: hidden;
            padding: 1.45rem 2rem 1.45rem 5.2rem;
            border: 1px solid rgba(196, 181, 253, .47);
            border-radius: var(--radius-xl);
            background:
                radial-gradient(circle at 0% 50%, rgba(139, 92, 246, .24), transparent 19rem),
                linear-gradient(120deg, #211033, #11091e 65%, #1b1030);
            box-shadow: var(--shadow-raised), 0 0 34px rgba(139, 92, 246, .14), inset 0 1px 0 rgba(255, 255, 255, .06);
            color: var(--text-primary);
            font-size: clamp(.98rem, 1.6vw, 1.1rem);
            font-weight: 570;
            line-height: 1.6;
            text-align: left;
            overflow-wrap: anywhere;
        }}

        .st-key-home_footer .message-card::before {{
            content: "♡";
            position: absolute;
            left: 1.45rem;
            top: 50%;
            display: grid;
            place-items: center;
            width: 2.65rem;
            height: 2.65rem;
            transform: translateY(-50%);
            border: 1px solid rgba(196, 181, 253, .48);
            border-radius: 50%;
            background: rgba(139, 92, 246, .15);
            box-shadow: 0 0 24px rgba(167, 139, 250, .16);
            color: var(--violet-300);
            font-size: 1.7rem;
            font-weight: 400;
            line-height: 1;
        }}

        .st-key-home_footer .stButton {{
            margin-top: 0.8rem;
        }}

        @supports ((-webkit-backdrop-filter: blur(1px)) or (backdrop-filter: blur(1px))) {{
            .st-key-home_footer .message-card {{
                background:
                    radial-gradient(circle at 0% 50%, rgba(139, 92, 246, .2), transparent 19rem),
                    linear-gradient(120deg, rgba(33, 16, 51, .9), rgba(17, 9, 30, .86) 65%, rgba(27, 16, 48, .88));
                -webkit-backdrop-filter: blur(var(--blur));
                backdrop-filter: blur(var(--blur));
            }}
        }}

        @media (max-width: 900px) {{
            .home-habit-grid {{
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 700px) {{
            .home-hero {{
                display: flex;
                min-height: 0;
                flex-direction: column;
                margin-bottom: 1.35rem;
                border-radius: 22px;
            }}

            .home-hero::before {{
                display: none;
            }}

            .home-hero-copy {{
                order: 2;
                min-height: 0;
                width: 100%;
                padding: 1.5rem 1.6rem 1.7rem;
                background: linear-gradient(145deg, rgba(30, 15, 56, 0.95), rgba(10, 5, 20, 0.97));
            }}

            .home-hero-title {{
                margin-top: 0.55rem;
                font-size: clamp(2.15rem, 10vw, 3.15rem) !important;
            }}

            .home-hero-art {{
                position: relative;
                order: 1;
                height: clamp(215px, 45vw, 300px);
                object-position: right center;
                transform: none;
                animation: none;
            }}

            .st-key-home_overview {{
                padding: 1.15rem;
            }}

            .st-key-home_overview [data-testid="stHorizontalBlock"] {{
                flex-direction: column;
            }}

            .st-key-home_overview [data-testid="stColumn"] {{
                width: 100% !important;
                flex: 1 1 100% !important;
            }}

            .home-habit-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .home-habit-card {{
                min-height: 7.4rem;
                padding: 0.9rem 1rem;
            }}

            .st-key-home_weekly .stat-card {{
                min-height: 7.2rem;
                padding: 1rem;
            }}
        }}

        @media (max-width: 480px) {{
            .st-key-primary_navigation_home {{
                margin-top: 2.1rem;
                margin-bottom: 1rem;
                padding: .3rem;
                border-radius: var(--radius-lg);
            }}
            .st-key-primary_navigation_home [data-testid="stHorizontalBlock"] {{ gap: .18rem; }}
            .st-key-primary_navigation_home [data-testid="stPageLink"] a {{ min-height: 48px; padding: .3rem; }}
            .st-key-primary_navigation_home [data-testid="stIconMaterial"] {{ font-size: 1.3rem !important; }}
            .st-key-home_footer .message-card {{
                min-height: 5.5rem;
                padding: 1.15rem 1.2rem 1.15rem 4.25rem;
                font-size: .95rem;
            }}
            .st-key-home_footer .message-card::before {{
                left: 1rem;
                width: 2.35rem;
                height: 2.35rem;
                font-size: 1.5rem;
            }}
        }}

        @media (max-width: 380px) {{
            .home-hero-copy {{
                width: 100%;
                padding: 1.3rem;
            }}

            .st-key-home_weekly .stat-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (prefers-reduced-motion: reduce) {{
            .home-hero-art,
            .home-hero::after,
            .st-key-home_overview .progress-ring {{
                animation: none !important;
            }}
        }}
        </style>
        <section class="home-hero" aria-labelledby="home-hero-title">
            <div class="home-hero-copy">
                <span class="brand-kicker">ERUMAA'S DAILY</span>
                <h1 class="home-hero-title" id="home-hero-title">{safe_title}</h1>
                <p class="home-hero-subtitle">{safe_subtitle}</p>
            </div>
            <img class="home-hero-art" src="data:image/png;base64,{_HOME_IMAGE_DATA}"
                 alt="" aria-hidden="true">
        </section>
        """
    )


def _answer_status(record: dict | None, field: str) -> str:
    """Keep legacy NULL answers distinct from an explicit No."""
    if record is None:
        return "Not entered"
    answer = record.get(field)
    if answer is None:
        return "Not tracked"
    return "Yes" if answer is True else "No"


def _render_habit_cards(record: dict | None) -> None:
    if record is None:
        values = ["Not entered"] * 5
    else:
        sleep = record.get("sleep_hours")
        water = record.get("water_liters")
        exercised = record.get("exercise_done")
        values = [
            f"{float(sleep):g} hours" if sleep is not None else "Not tracked",
            (
                f"{float(record.get('exercise_minutes') or 0):g} minutes"
                if exercised is True
                else "Rest day" if exercised is False else "Not tracked"
            ),
            f"{float(water):g} L" if water is not None else "Not tracked",
            _answer_status(record, "ate_fruit"),
            _answer_status(record, "freshened_up"),
        ]

    labels = ("Sleep", "Exercise", "Water", "Fruit", "Freshened up")
    cards = "".join(
        f'<div class="home-habit-card"><span class="home-habit-index">{index:02d}</span>'
        f'<span class="home-habit-label">{html.escape(label)}</span>'
        f'<strong class="home-habit-value">{html.escape(value)}</strong></div>'
        for index, (label, value) in enumerate(zip(labels, values), start=1)
    )
    st.html(f'<div class="home-habit-grid">{cards}</div>')

today = india_today()
now = india_now()
repo = DailyLogRepository(get_supabase_client(), current_user_id() or "")
render_settings(repo)
render_primary_navigation(icon_only=True)
_render_home_hero(greeting(now), "Your day at a glance")

try:
    logs = repo.list_logs()
except RepositoryError as exc:
    st.error(str(exc))
    st.stop()

today_record = next((row for row in logs if str(row.get("log_date")) == today.isoformat()), None)
monday, sunday = week_bounds(today)
week_records = [row for row in logs if monday.isoformat() <= str(row.get("log_date")) <= sunday.isoformat()]
score = float(today_record.get("daily_score") or 0) if today_record else 0.0

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

with st.container(key="home_overview"):
    score_column, rhythm_column = st.columns([0.88, 1.12], gap="large", vertical_alignment="center")
    with score_column:
        section_label("✦", "Today's progress", today.strftime("%a, %d %b"))
        progress_ring(score)
    with rhythm_column:
        section_label("◇", "Daily rhythm")
        metric_list(cards)

with st.container(key="home_habits"):
    section_label("◇", "Today at a glance")
    _render_habit_cards(today_record)

streak = calculate_current_streak(logs, today)
weekly_score = calculate_weekly_average(week_records)
streak_unit = "DAY" if streak == 1 else "DAYS"
with st.container(key="home_weekly"):
    section_label("∿", "This week")
    stat_grid(
        [
            ("CURRENT STREAK", f"{streak} {streak_unit}", "Consecutive complete days"),
            ("WEEKLY SCORE", f"{weekly_score:.0f}%", f"{len(week_records)} of 7 days"),
        ]
    )

with st.container(key="home_footer"):
    complete = bool(today_record and float(today_record.get("daily_completion_score") or 0) == 100)
    if complete:
        message_card("✨ TODAY COMPLETE ✨\n\nYou showed up today. ❤️", complete=True)
    else:
        message_card(message_for_day(today))
        if st.button("Complete Today", type="primary", width="stretch"):
            st.switch_page("pages/today.py")
