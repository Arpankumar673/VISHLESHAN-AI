-- ============================================================
-- VISHLESHAN AI v2 — Phase 2 Migration
-- Add job retry and worker metadata columns to research_runs
-- ============================================================

alter table public.research_runs
add column if not exists attempt_count integer not null default 0,
add column if not exists last_error text,
add column if not exists worker_id text;
