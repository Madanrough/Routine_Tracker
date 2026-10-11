"""Reusable Today/yesterday entry form."""

from __future__ import annotations

from contextlib import nullcontext
from datetime import date
from typing import Any

import streamlit as st

from src.database import DailyLogRepository, RepositoryError
from src.timezone_utils import india_today
from src.ui import habit_heading, section_label
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


def _freshened_choice(prefix: str) -> str | None:
    return st.radio(
        "Did you freshen up after Office?",
        ["YES", "NO"],
        horizontal=True,
        index=None,
        key=f"{prefix}_freshened",
    )


def _meal_choice(prefix: str, number: int, today_style: bool) -> str | None:
    with st.container(key=f"{prefix}_{number}_meal_row") if today_style else nullcontext():
        label = {1: "1ST MEAL", 2: "2ND MEAL", 3: "3RD MEAL"}[number]
        st.markdown(f'<div class="meal-label">{label}</div>', unsafe_allow_html=True)
        return st.radio(
            "Protein + fibre included?", ["YES", "NO"], horizontal=True,
            index=None, key=f"{prefix}_meal{number}",
        )


def render_daily_form(
    target_date: date,
    repo: DailyLogRepository,
    existing: dict[str, Any] | None = None,
    *,
    heading: bool = True,
    today_style: bool = False,
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
        habit_heading("sleep", "Sleep") if today_style else section_label("😴", "Sleep")
        sleep = st.number_input(
            "Hours slept",
            min_value=0.0,
            max_value=24.0,
            step=0.5,
            key=f"{prefix}_sleep",
        )
        if not today_style:
            freshened = _freshened_choice(prefix)

    with st.container(border=True, key=f"{prefix}_exercise_section"):
        habit_heading("exercise", "Exercise") if today_style else section_label("🏃", "Exercise")
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
        habit_heading("food", "Food & Nourishment") if today_style else section_label("🥗", "Food")
        meal1 = _meal_choice(prefix, 1, today_style)
        meal2 = _meal_choice(prefix, 2, today_style)
        meal3 = _meal_choice(prefix, 3, today_style)
        with st.container(key=f"{prefix}_junk_food_extra") if today_style else nullcontext():
            junk = st.radio(
                "Junk or sugary food?",
                ["YES", "NO"],
                horizontal=True,
                index=None,
                help="YES means it was consumed. NO means it was not consumed.",
                key=f"{prefix}_junk",
            )
        with st.container(key=f"{prefix}_fruit_food_extra") if today_style else nullcontext():
            fruit = st.radio(
                "Did you eat any fruit today?",
                ["YES", "NO"],
                horizontal=True,
                index=None,
                key=f"{prefix}_fruit",
            )

    with st.container(border=True, key=f"{prefix}_water_section"):
        habit_heading("water", "Water") if today_style else section_label("💧", "Water")
        water = st.number_input(
            "Litres today",
            min_value=0.0,
            max_value=10.0,
            step=0.1,
            key=f"{prefix}_water",
        )

    if today_style:
        with st.container(border=True, key=f"{prefix}_selfcare_section"):
            habit_heading("selfcare", "Freshened up")
            freshened = _freshened_choice(prefix)

    with st.container(border=True, key=f"{prefix}_stress_section"):
        habit_heading("stress", "Stress management") if today_style else section_label("🧘", "Stress management")
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
        habit_heading("mood", "Mood") if today_style else section_label("🙂", "Mood")
        mood = st.radio(
            "How did you feel?",
            ["Happy", "Okay", "Low"],
            horizontal=True,
            index=None,
            format_func=lambda value: value if today_style else {"Happy": "😊 Happy", "Okay": "😐 Okay", "Low": "😔 Low"}[value],
            key=f"{prefix}_mood",
        )
        st.caption("Mood is for reflection only and does not affect your score.")

    with st.container(border=True, key=f"{prefix}_note_section"):
        habit_heading("note", "Daily note", "Optional") if today_style else section_label("✍️", "Daily note", "Optional")
        note = st.text_area(
            "Anything you want to remember?",
            max_chars=2000,
            placeholder="A small moment worth remembering…" if today_style else "Optional",
            key=f"{prefix}_note",
        )
    save_label = "SAVE TODAY" if target_date == india_today() else "SAVE ENTRY"
    if today_style:
        save_label = "Save Today's Entry" if target_date == india_today() else "Save Entry"
    with st.container(key="today_save_bar") if today_style else nullcontext():
        submitted = st.button(save_label, type="primary", width="stretch", key=f"{prefix}_save")
    if submitted:
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
            if today_style:
                st.toast(f"Saved · Daily score is {float(saved['daily_score']):.0f}%", icon=":material/check_circle:")
        except (ValidationError, RepositoryError) as exc:
            st.error(str(exc))
            if today_style:
                st.toast(str(exc), icon=":material/error:", duration="long")
