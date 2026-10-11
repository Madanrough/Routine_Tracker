"""Reusable Today/yesterday entry form."""

from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

from src.database import DailyLogRepository, RepositoryError
from src.timezone_utils import india_today
from src.ui import section_label
from src.validators import ValidationError


def _choice(value: Any, true_label: str = "YES", false_label: str = "NO") -> str | None:
    if value is True:
        return true_label
    if value is False:
        return false_label
    return None


def _seed(key: str, value: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def render_daily_form(
    target_date: date,
    repo: DailyLogRepository,
    existing: dict[str, Any] | None = None,
    *,
    heading: bool = True,
) -> None:
    prefix = f"daily_{target_date.isoformat()}"
    row = existing or {}
    defaults = {
        f"{prefix}_sleep": float(row.get("sleep_hours") or 0),
        f"{prefix}_freshened": _choice(row.get("freshened_up")),
        f"{prefix}_exercise": _choice(row.get("exercise_done")),
        f"{prefix}_minutes": float(row.get("exercise_minutes") or 0),
        f"{prefix}_meal1": _choice(row.get("meal1_protein_fibre")),
        f"{prefix}_meal2": _choice(row.get("meal2_protein_fibre")),
        f"{prefix}_meal3": _choice(row.get("meal3_protein_fibre")),
        f"{prefix}_junk": _choice(row.get("junk_sugary_food")),
        f"{prefix}_fruit": _choice(row.get("ate_fruit")),
        f"{prefix}_water": float(row.get("water_liters") or 0),
        f"{prefix}_stress": row.get("stress_level"),
        f"{prefix}_relax": _choice(row.get("stress_management")),
        f"{prefix}_mood": row.get("mood"),
        f"{prefix}_note": row.get("daily_note") or "",
    }
    for key, value in defaults.items():
        _seed(key, value)

    if heading:
        st.caption(target_date.strftime("%A, %d %B %Y"))
    with st.container(border=True, key=f"{prefix}_sleep_section"):
        section_label("😴", "Sleep")
        sleep = st.number_input(
            "Hours slept",
            min_value=0.0,
            max_value=24.0,
            step=0.5,
            key=f"{prefix}_sleep",
        )
        freshened = st.radio(
            "Did you freshen up after waking up?",
            ["YES", "NO"],
            horizontal=True,
            index=None,
            key=f"{prefix}_freshened",
        )

    with st.container(border=True, key=f"{prefix}_exercise_section"):
        section_label("🏃", "Exercise")
        exercise_choice = st.radio(
            "Did you exercise?",
            ["YES", "NO"],
            horizontal=True,
            index=None,
            key=f"{prefix}_exercise",
        )
        minutes = st.number_input(
            "Minutes",
            min_value=0,
            max_value=300,
            step=5,
            disabled=exercise_choice != "YES",
            key=f"{prefix}_minutes",
        )

    with st.container(border=True, key=f"{prefix}_food_section"):
        section_label("🥗", "Food")
        st.markdown('<div class="meal-label">1ST MEAL</div>', unsafe_allow_html=True)
        meal1 = st.radio("Protein + fibre included?", ["YES", "NO"], horizontal=True, index=None, key=f"{prefix}_meal1")
        st.markdown('<div class="meal-label">2ND MEAL</div>', unsafe_allow_html=True)
        meal2 = st.radio("Protein + fibre included?", ["YES", "NO"], horizontal=True, index=None, key=f"{prefix}_meal2")
        st.markdown('<div class="meal-label">3RD MEAL</div>', unsafe_allow_html=True)
        meal3 = st.radio("Protein + fibre included?", ["YES", "NO"], horizontal=True, index=None, key=f"{prefix}_meal3")
        junk = st.radio(
            "Junk or sugary food?",
            ["YES", "NO"],
            horizontal=True,
            index=None,
            help="YES means it was consumed. NO means it was not consumed.",
            key=f"{prefix}_junk",
        )
        fruit = st.radio(
            "Did you eat any fruit today?",
            ["YES", "NO"],
            horizontal=True,
            index=None,
            key=f"{prefix}_fruit",
        )

    with st.container(border=True, key=f"{prefix}_water_section"):
        section_label("💧", "Water")
        water = st.number_input(
            "Litres today",
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            key=f"{prefix}_water",
        )

    with st.container(border=True, key=f"{prefix}_stress_section"):
        section_label("🧘", "Stress management")
        stress = st.radio("Stress level", ["LOW", "MODERATE", "HIGH"], horizontal=True, index=None, key=f"{prefix}_stress")
        relax = st.radio(
            "Did you do something to relax?",
            ["YES", "NO"],
            horizontal=True,
            index=None,
            key=f"{prefix}_relax",
        )
        st.caption("Stress level is recorded for reflection and does not reduce your score.")

    with st.container(border=True, key=f"{prefix}_mood_section"):
        section_label("🙂", "Mood")
        mood = st.radio(
            "How did you feel?",
            ["Happy", "Okay", "Low"],
            horizontal=True,
            index=None,
            format_func=lambda value: {"Happy": "😊 Happy", "Okay": "😐 Okay", "Low": "😔 Low"}[value],
            key=f"{prefix}_mood",
        )
        st.caption("Mood is for reflection only and does not affect your score.")

    with st.container(border=True, key=f"{prefix}_note_section"):
        section_label("✍️", "Daily note", "Optional")
        note = st.text_area(
            "Anything you want to remember?",
            max_chars=2000,
            placeholder="Optional",
            key=f"{prefix}_note",
        )
    if st.button("SAVE TODAY" if target_date == india_today() else "SAVE ENTRY", type="primary", width="stretch", key=f"{prefix}_save"):
        values = {
            "sleep_hours": sleep,
            "freshened_up": None if freshened is None else freshened == "YES",
            "exercise_done": None if exercise_choice is None else exercise_choice == "YES",
            "exercise_minutes": int(minutes) if exercise_choice == "YES" else 0,
            "meal1_protein_fibre": None if meal1 is None else meal1 == "YES",
            "meal2_protein_fibre": None if meal2 is None else meal2 == "YES",
            "meal3_protein_fibre": None if meal3 is None else meal3 == "YES",
            "junk_sugary_food": None if junk is None else junk == "YES",
            "ate_fruit": None if fruit is None else fruit == "YES",
            "water_liters": water,
            "stress_level": stress,
            "stress_management": None if relax is None else relax == "YES",
            "mood": mood,
            "daily_note": note,
        }
        try:
            saved = repo.save_log(target_date, values)
            st.session_state[f"saved_{target_date.isoformat()}"] = True
            st.success(f"Saved · Daily score is {float(saved['daily_score']):.0f}%")
        except (ValidationError, RepositoryError) as exc:
            st.error(str(exc))
