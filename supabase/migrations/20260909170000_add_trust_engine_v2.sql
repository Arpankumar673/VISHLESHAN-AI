-- ============================================================
-- VISHLESHAN AI v2
-- Phase 4: Trust Engine v2 Schema Extension
-- ============================================================

alter table public.trust_scores
add column if not exists verification_status text default 'unable_to_verify'
    check (
        verification_status in (
            'verified',
            'partially_verified',
            'unable_to_verify',
            'conflicting'
        )
    ),
add column if not exists dimension_scores jsonb default '{}'::jsonb,
add column if not exists risk_adjustment jsonb default '{}'::jsonb,
add column if not exists conflict_summary jsonb default '{}'::jsonb,
add column if not exists evidence_references jsonb default '[]'::jsonb;

-- Index for verification_status on trust_scores
create index if not exists trust_scores_verification_status_idx
on public.trust_scores(verification_status);
