-- V2.1: add optional storage for newly required application check-ins.
-- Columns remain nullable so historical rows retain NULL (not tracked).

alter table public.daily_logs
    add column if not exists ate_fruit boolean,
    add column if not exists freshened_up boolean;
