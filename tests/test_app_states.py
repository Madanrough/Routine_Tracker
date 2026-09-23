from pathlib import Path

from streamlit.testing.v1 import AppTest

from src import auth


ROOT = Path(__file__).parents[1]


def test_missing_secrets_render_friendly_setup_message(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.setattr(auth, "_secret", lambda _name: None)

    app = AppTest.from_file(ROOT / "app.py", default_timeout=10).run()

    assert not app.exception
    assert any("Supabase is not configured" in error.value for error in app.error)
    assert any("README.md" in info.value for info in app.info)
