"""Supabase data access with ownership and edit-window safeguards."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from supabase import Client

from src.scoring import score_daily_record
from src.timezone_utils import india_today, is_editable_log_date
from src.validators import validate_daily_record

LOGGER = logging.getLogger(__name__)


class RepositoryError(RuntimeError):
    """A user-safe wrapper around data access failures."""


class DailyLogRepository:
    def __init__(self, client: Client, user_id: str):
        self.client = client
        self.user_id = user_id

    def get_log(self, log_date: date) -> dict[str, Any] | None:
        try:
            response = (
                self.client.table("daily_logs")
                .select("*")
                .eq("user_id", self.user_id)
                .eq("log_date", log_date.isoformat())
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as exc:
            LOGGER.exception("Failed to load daily log")
            raise RepositoryError("We couldn't load this entry. Please try again.") from exc

    def list_logs(self, start: date | None = None, end: date | None = None) -> list[dict[str, Any]]:
        try:
            query = (
                self.client.table("daily_logs")
                .select("*")
                .eq("user_id", self.user_id)
            )
            if start:
                query = query.gte("log_date", start.isoformat())
            if end:
                query = query.lte("log_date", end.isoformat())
            response = query.order("log_date", desc=True).execute()
            return list(response.data or [])
        except Exception as exc:
            LOGGER.exception("Failed to list daily logs")
            raise RepositoryError("We couldn't load your history. Please try again.") from exc

    def save_log(self, log_date: date, values: dict[str, Any]) -> dict[str, Any]:
        """Insert or update one record, rejecting dates outside the edit window."""
        if not is_editable_log_date(log_date, india_today()):
            raise RepositoryError("Only today's and yesterday's entries can be edited.")
        validate_daily_record(values)
        payload = {
            **values,
            **score_daily_record(values),
            "user_id": self.user_id,
            "log_date": log_date.isoformat(),
            "exercise_minutes": int(values.get("exercise_minutes") or 0),
            "sleep_hours": float(values["sleep_hours"]),
            "water_liters": float(values["water_liters"]),
            "ate_fruit": values["ate_fruit"],
            "freshened_up": values["freshened_up"],
            "daily_note": (values.get("daily_note") or "").strip() or None,
        }
        try:
            response = (
                self.client.table("daily_logs")
                .upsert(payload, on_conflict="user_id,log_date")
                .execute()
            )
            if not response.data:
                raise RuntimeError("Database returned no saved record")
            return response.data[0]
        except Exception as exc:
            LOGGER.exception("Failed to save daily log")
            raise RepositoryError(
                "Something went wrong while saving this entry. Please try again."
            ) from exc

    def export_rows(self) -> list[dict[str, Any]]:
        """Export complete selected rows, including newly added database columns."""
        return self.list_logs()
