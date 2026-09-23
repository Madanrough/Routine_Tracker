from datetime import date
from types import SimpleNamespace

import pytest

from src import database
from src.database import DailyLogRepository, RepositoryError


def valid_values():
    return {
        "sleep_hours": 8,
        "exercise_done": True,
        "exercise_minutes": 30,
        "meal1_protein_fibre": True,
        "meal2_protein_fibre": True,
        "meal3_protein_fibre": True,
        "junk_sugary_food": False,
        "water_liters": 2.5,
        "stress_level": "LOW",
        "stress_management": True,
        "mood": "Happy",
        "daily_note": "",
    }


class Query:
    def __init__(self, data=None, fail=False):
        self.data = data if data is not None else []
        self.fail = fail
        self.operations = []

    def select(self, value):
        self.operations.append(("select", value))
        return self

    def eq(self, field, value):
        self.operations.append(("eq", field, value))
        return self

    def gte(self, field, value):
        self.operations.append(("gte", field, value))
        return self

    def lte(self, field, value):
        self.operations.append(("lte", field, value))
        return self

    def limit(self, value):
        self.operations.append(("limit", value))
        return self

    def order(self, field, desc=False):
        self.operations.append(("order", field, desc))
        return self

    def upsert(self, payload, on_conflict):
        self.operations.append(("upsert", payload, on_conflict))
        self.data = [payload]
        return self

    def execute(self):
        if self.fail:
            raise ConnectionError("offline")
        return SimpleNamespace(data=self.data)


class Client:
    def __init__(self, query):
        self.query = query
        self.table_calls = []

    def table(self, name):
        self.table_calls.append(name)
        return self.query


def test_duplicate_safe_save_uses_user_date_conflict(monkeypatch):
    query = Query()
    repo = DailyLogRepository(Client(query), "user-1")
    monkeypatch.setattr(database, "india_today", lambda: date(2026, 9, 19))

    result = repo.save_log(date(2026, 9, 19), valid_values())

    operation = next(item for item in query.operations if item[0] == "upsert")
    assert operation[2] == "user_id,log_date"
    assert operation[1]["user_id"] == "user-1"
    assert operation[1]["log_date"] == "2026-09-19"
    assert result["daily_score"] == 100


def test_old_record_is_rejected_before_database_call(monkeypatch):
    client = Client(Query())
    repo = DailyLogRepository(client, "user-1")
    monkeypatch.setattr(database, "india_today", lambda: date(2026, 9, 19))
    with pytest.raises(RepositoryError, match="today's and yesterday's"):
        repo.save_log(date(2026, 9, 17), valid_values())
    assert client.table_calls == []


def test_export_query_is_scoped_to_authenticated_user():
    query = Query([])
    repo = DailyLogRepository(Client(query), "user-1")
    assert repo.export_rows() == []
    assert ("eq", "user_id", "user-1") in query.operations


def test_database_unavailable_is_wrapped_in_friendly_error():
    repo = DailyLogRepository(Client(Query(fail=True)), "user-1")
    with pytest.raises(RepositoryError, match="couldn't load your history"):
        repo.list_logs()

