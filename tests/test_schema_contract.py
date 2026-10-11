from pathlib import Path


SCHEMA = (Path(__file__).parents[1] / "supabase" / "schema.sql").read_text(encoding="utf-8").lower()
MIGRATION = (
    Path(__file__).parents[1]
    / "supabase"
    / "migrations"
    / "20261011_add_fruit_and_freshened_up.sql"
).read_text(encoding="utf-8").lower()


def test_schema_enforces_unique_user_date_and_rls():
    assert "unique (user_id, log_date)" in SCHEMA
    assert "enable row level security" in SCHEMA
    assert "force row level security" in SCHEMA


def test_schema_scopes_all_write_and_read_policies_to_auth_uid():
    assert SCHEMA.count("(select auth.uid()) = user_id") >= 4
    assert "for select" in SCHEMA
    assert "for insert" in SCHEMA
    assert "for update" in SCHEMA
    assert "for delete" not in SCHEMA


def test_schema_enforces_india_edit_window_and_preserves_owner_date():
    assert "asia/kolkata" in SCHEMA
    assert "log_date between public.india_today() - 1 and public.india_today()" in SCHEMA
    assert "old.user_id <> new.user_id or old.log_date <> new.log_date" in SCHEMA


def test_canonical_schema_contains_nullable_v21_fields():
    assert "ate_fruit boolean" in SCHEMA
    assert "freshened_up boolean" in SCHEMA
    assert "ate_fruit boolean not null" not in SCHEMA
    assert "freshened_up boolean not null" not in SCHEMA


def test_v21_migration_is_additive_and_preserves_legacy_nulls():
    assert "alter table public.daily_logs" in MIGRATION
    assert "add column if not exists ate_fruit boolean" in MIGRATION
    assert "add column if not exists freshened_up boolean" in MIGRATION
    assert "not null" not in MIGRATION
    assert " default " not in MIGRATION
    assert "update " not in MIGRATION
    assert "delete " not in MIGRATION

