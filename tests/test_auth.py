from types import SimpleNamespace

import pytest

from src import auth


class FakeAuth:
    def __init__(self):
        self.signed_out = False

    def sign_out(self):
        self.signed_out = True


def test_logout_clears_all_user_derived_session_state(monkeypatch):
    fake_auth = FakeAuth()
    state = {
        "supabase_client": SimpleNamespace(auth=fake_auth),
        "auth_user_id": "user-a",
        "auth_email": "private@example.com",
        "export_csv": b"private data",
        "daily_2026-09-19_note": "private note",
        "celebration_2026-09-14": True,
    }
    monkeypatch.setattr(auth.st, "session_state", state)

    auth.logout()

    assert fake_auth.signed_out
    assert state == {}


def test_login_failure_is_user_safe(monkeypatch):
    class FailingAuth:
        def sign_in_with_password(self, credentials):
            raise ConnectionError("database unavailable")

    state = {}
    monkeypatch.setattr(auth.st, "session_state", state)
    client = SimpleNamespace(auth=FailingAuth())
    assert auth.login(client, "person@example.com", "not-logged") is False
    assert "auth_user_id" not in state


def test_missing_secrets_raise_friendly_configuration_error(monkeypatch):
    state = {}
    monkeypatch.setattr(auth.st, "session_state", state)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    class MissingSecrets:
        def get(self, *args, **kwargs):
            raise FileNotFoundError

    monkeypatch.setattr(auth.st, "secrets", MissingSecrets())
    with pytest.raises(auth.ConfigurationError, match="Supabase is not configured"):
        auth.get_supabase_client()

