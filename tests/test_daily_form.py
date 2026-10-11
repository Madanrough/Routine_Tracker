"""Integration checks for the shared daily form and Today presentation."""

import pytest
from streamlit.testing.v1 import AppTest

from src.timezone_utils import india_today


def _form_app(existing, styled):
    from contextlib import nullcontext
    from types import SimpleNamespace

    import streamlit as st

    from src.daily_form import render_daily_form
    from src.database import DailyLogRepository
    from src.timezone_utils import india_today
    from src.ui import apply_global_styles, apply_today_styles

    class LocalQuery:
        def upsert(self, payload, on_conflict):
            assert on_conflict == "user_id,log_date"
            st.session_state.saved_payload = payload
            return self

        def execute(self):
            return SimpleNamespace(data=[st.session_state.saved_payload])

    class LocalClient:
        def table(self, name):
            assert name == "daily_logs"
            return LocalQuery()

    apply_global_styles()
    if styled:
        apply_today_styles()
    with st.container(key="today_page") if styled else nullcontext():
        render_daily_form(
            india_today(), DailyLogRepository(LocalClient(), "test-user"),
            existing, today_style=styled,
        )


@pytest.mark.parametrize("styled", [True, False])
def test_all_fields_save_with_original_keys_and_yes_no_semantics(styled):
    app = AppTest.from_function(_form_app, args=(None, styled), default_timeout=10).run()
    prefix = f"daily_{india_today().isoformat()}"
    assert not app.exception
    assert app.number_input(key=f"{prefix}_minutes").disabled

    app.radio(key=f"{prefix}_exercise").set_value("YES").run()
    assert not app.number_input(key=f"{prefix}_minutes").disabled
    app.number_input(key=f"{prefix}_sleep").set_value(7.5)
    app.number_input(key=f"{prefix}_minutes").set_value(35)
    app.number_input(key=f"{prefix}_water").set_value(2.2)
    for name, value in {
        "meal1": "YES", "meal2": "NO", "meal3": "YES", "junk": "YES",
        "fruit": "NO", "freshened": "NO", "stress": "HIGH", "relax": "YES", "mood": "Low",
    }.items():
        app.radio(key=f"{prefix}_{name}").set_value(value)
    app.text_area(key=f"{prefix}_note").set_value("A quiet evening")
    app.button(key=f"{prefix}_save").click().run()

    assert not app.exception
    assert len(app.success) == 1
    payload = app.session_state.saved_payload
    expected = {
        "sleep_hours": 7.5, "exercise_done": True, "exercise_minutes": 35,
        "meal1_protein_fibre": True, "meal2_protein_fibre": False,
        "meal3_protein_fibre": True, "junk_sugary_food": True,
        "ate_fruit": False, "freshened_up": False, "water_liters": 2.2,
        "stress_level": "HIGH", "stress_management": True, "mood": "Low",
        "daily_note": "A quiet evening", "user_id": "test-user",
        "log_date": india_today().isoformat(),
    }
    assert {name: payload[name] for name in expected} == expected
    assert payload["food_score"] == 40
    assert payload["daily_completion_score"] == 100

    # Switching to No keeps the control disabled and persists zero minutes.
    app.radio(key=f"{prefix}_exercise").set_value("NO").run()
    assert app.number_input(key=f"{prefix}_minutes").disabled
    app.button(key=f"{prefix}_save").click().run()
    assert app.session_state.saved_payload["exercise_minutes"] == 0
    assert app.session_state.saved_payload["exercise_done"] is False


def test_unanswered_new_fields_are_not_saved_as_no():
    app = AppTest.from_function(_form_app, args=(None, True), default_timeout=10).run()
    prefix = f"daily_{india_today().isoformat()}"
    assert app.radio(key=f"{prefix}_fruit").value is None
    assert app.radio(key=f"{prefix}_freshened").value is None
    app.button(key=f"{prefix}_save").click().run()
    assert not app.exception
    assert "Fruit" in app.error[0].value
    assert "Freshened up" in app.error[0].value
    assert "saved_payload" not in app.session_state


def test_legacy_nulls_stay_unselected_while_explicit_no_is_retained():
    existing = {"ate_fruit": None, "freshened_up": None, "junk_sugary_food": False}
    app = AppTest.from_function(_form_app, args=(existing, True), default_timeout=10).run()
    prefix = f"daily_{india_today().isoformat()}"
    assert not app.exception
    assert app.radio(key=f"{prefix}_fruit").value is None
    assert app.radio(key=f"{prefix}_freshened").value is None
    assert app.radio(key=f"{prefix}_junk").value == "NO"
