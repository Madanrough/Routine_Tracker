-- Erumaa's Daily — Supabase PostgreSQL schema
-- Run this entire file in the Supabase SQL Editor as the project owner.

create extension if not exists pgcrypto;

create table if not exists public.daily_logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    log_date date not null,
    sleep_hours numeric(4,1) not null check (sleep_hours between 0 and 24),
    sleep_score numeric(5,2) not null check (sleep_score between 0 and 100),
    exercise_done boolean not null,
    exercise_minutes integer not null default 0 check (exercise_minutes between 0 and 300),
    exercise_score numeric(5,2) not null check (exercise_score between 0 and 100),
    meal1_protein_fibre boolean not null,
    meal2_protein_fibre boolean not null,
    meal3_protein_fibre boolean not null,
    junk_sugary_food boolean not null,
    meal_quality_score numeric(5,2) not null check (meal_quality_score between 0 and 100),
    junk_control_score numeric(5,2) not null check (junk_control_score between 0 and 100),
    food_score numeric(5,2) not null check (food_score between 0 and 100),
    water_liters numeric(4,1) not null check (water_liters between 0 and 10),
    water_score numeric(5,2) not null check (water_score between 0 and 100),
    stress_level text not null check (stress_level in ('LOW', 'MODERATE', 'HIGH')),
    stress_management boolean not null,
    stress_management_score numeric(5,2) not null check (stress_management_score between 0 and 100),
    mood text not null check (mood in ('Happy', 'Okay', 'Low')),
    daily_completion_score numeric(5,2) not null check (daily_completion_score in (0, 100)),
    daily_score numeric(5,2) not null check (daily_score between 0 and 100),
    daily_note text check (daily_note is null or char_length(daily_note) <= 2000),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint daily_logs_user_date_key unique (user_id, log_date),
    constraint exercise_minutes_consistent check (
        (exercise_done and exercise_minutes >= 0) or
        (not exercise_done and exercise_minutes = 0)
    )
);

create index if not exists daily_logs_user_date_desc_idx
    on public.daily_logs (user_id, log_date desc);

create or replace function public.india_today()
returns date
language sql
stable
set search_path = ''
as $$
    select (now() at time zone 'Asia/Kolkata')::date;
$$;

create or replace function public.protect_daily_log_update()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
    if old.user_id <> new.user_id or old.log_date <> new.log_date then
        raise exception 'Record owner and date cannot be changed';
    end if;
    if old.log_date < public.india_today() - 1 or old.log_date > public.india_today() then
        raise exception 'Only today and yesterday can be edited';
    end if;
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists daily_logs_protect_update on public.daily_logs;
create trigger daily_logs_protect_update
before update on public.daily_logs
for each row execute function public.protect_daily_log_update();

alter table public.daily_logs enable row level security;
alter table public.daily_logs force row level security;

drop policy if exists "Users can read their own daily logs" on public.daily_logs;
create policy "Users can read their own daily logs"
on public.daily_logs for select
to authenticated
using ((select auth.uid()) = user_id);

drop policy if exists "Users can create their own current entries" on public.daily_logs;
create policy "Users can create their own current entries"
on public.daily_logs for insert
to authenticated
with check (
    (select auth.uid()) = user_id
    and log_date between public.india_today() - 1 and public.india_today()
);

drop policy if exists "Users can update only their own recent entries" on public.daily_logs;
create policy "Users can update only their own recent entries"
on public.daily_logs for update
to authenticated
using (
    (select auth.uid()) = user_id
    and log_date between public.india_today() - 1 and public.india_today()
)
with check (
    (select auth.uid()) = user_id
    and log_date between public.india_today() - 1 and public.india_today()
);

-- No DELETE policy is intentional: daily history is preserved.
revoke all on table public.daily_logs from anon;
grant select, insert, update on table public.daily_logs to authenticated;

