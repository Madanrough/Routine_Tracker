"""Supabase email/password authentication for the private application."""

from __future__ import annotations

import logging
import os

import streamlit as st
from supabase import Client, ClientOptions, create_client

LOGGER = logging.getLogger(__name__)


class ConfigurationError(RuntimeError):
    """Raised when required deployment configuration is unavailable."""


def _secret(name: str) -> str | None:
    environment_value = os.getenv(name)
    if environment_value:
        return environment_value
    try:
        direct = st.secrets.get(name)
        if direct:
            return str(direct)
        section = st.secrets.get("supabase", {})
        return str(section.get(name.lower())) if section.get(name.lower()) else None
    except Exception:  # No secrets file is normal before initial setup.
        return None


def get_supabase_client() -> Client:
    """Create one authenticated Supabase client per Streamlit session."""
    if "supabase_client" in st.session_state:
        return st.session_state.supabase_client
    url = _secret("SUPABASE_URL")
    anon_key = _secret("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        raise ConfigurationError(
            "Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY "
            "to Streamlit secrets."
        )
    client = create_client(
        url,
        anon_key,
        options=ClientOptions(auto_refresh_token=True, persist_session=False),
    )
    st.session_state.supabase_client = client
    return client


def current_user_id() -> str | None:
    return st.session_state.get("auth_user_id")


def login(client: Client, email: str, password: str) -> bool:
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if not response.user:
            return False
        st.session_state.auth_user_id = str(response.user.id)
        st.session_state.auth_email = str(response.user.email or email)
        return True
    except Exception:
        LOGGER.exception("Supabase sign-in failed")
        return False


def logout() -> None:
    """Sign out remotely and remove all user-derived session data locally."""
    client = st.session_state.get("supabase_client")
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            LOGGER.exception("Supabase sign-out failed")
    # Form values, generated exports, and revealed achievements are user data.
    # Clearing the whole session prevents them leaking into a later login by a
    # different account in the same browser tab.
    st.session_state.clear()


def render_login(client: Client) -> None:
    """Render the private sign-in screen."""
    st.markdown(
        """
        <div class="login-hero">
          <div class="brand-kicker">PRIVATE WELLNESS SPACE</div>
          <h1>Erumaa's Daily</h1>
          <p>A gentle place for everyday routines.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", width="stretch")
    if submitted:
        if not email.strip() or not password:
            st.error("Enter your email and password.")
        elif login(client, email.strip(), password):
            st.rerun()
        else:
            st.error("We couldn't sign you in. Check your details and try again.")
