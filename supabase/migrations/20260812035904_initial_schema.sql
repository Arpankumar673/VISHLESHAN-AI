-- ============================================================
-- VISHLESHAN AI
-- M1 - Initial Database Schema
-- ============================================================

-- ------------------------------------------------------------
-- Extensions
-- ------------------------------------------------------------

create extension if not exists "pgcrypto";
create extension if not exists "vector";


-- ------------------------------------------------------------
-- Utility: updated_at trigger
-- ------------------------------------------------------------

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;


-- ============================================================
-- 1. PROFILES
-- Extends Supabase Auth users
-- ============================================================

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,

    full_name text,
    role text not null default 'user'
        check (role in ('user', 'admin', 'researcher')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ============================================================
-- 2. COMPANIES
-- Canonical company identity
-- ============================================================

create table if not exists public.companies (
    id uuid primary key default gen_random_uuid(),

    name text not null,
    normalized_name text not null,

    official_domain text,
    description text,
    industry text,
    headquarters text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists companies_normalized_name_idx
on public.companies (normalized_name);


-- ============================================================
-- 3. COMPANY IDENTIFIERS
-- Stores identifiers used for identity resolution
-- ============================================================

create table if not exists public.company_identifiers (
    id uuid primary key default gen_random_uuid(),

    company_id uuid not null
        references public.companies(id)
        on delete cascade,

    identifier_type text not null,
    identifier_value text not null,

    source_url text,
    confidence numeric(5,4)
        check (confidence >= 0 and confidence <= 1),

    created_at timestamptz not null default now(),

    unique (company_id, identifier_type, identifier_value)
);


-- ============================================================
-- 4. RESEARCH RUNS
-- Tracks asynchronous company research
-- ============================================================

create table if not exists public.research_runs (
    id uuid primary key default gen_random_uuid(),

    user_id uuid not null
        references auth.users(id)
        on delete cascade,

    company_id uuid not null
        references public.companies(id)
        on delete cascade,

    status text not null default 'queued'
        check (
            status in (
                'queued',
                'running',
                'completed',
                'partial',
                'failed'
            )
        ),

    started_at timestamptz,
    completed_at timestamptz,

    error_message text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (
        completed_at is null
        or started_at is null
        or completed_at >= started_at
    )
);


-- ============================================================
-- 5. EVIDENCE
-- Core evidence/provenance table
-- ============================================================

create table if not exists public.evidence (
    id uuid primary key default gen_random_uuid(),

    company_id uuid not null
        references public.companies(id)
        on delete cascade,

    research_run_id uuid not null
        references public.research_runs(id)
        on delete cascade,

    claim text not null,
    evidence_text text not null,

    source_url text not null,
    source_title text,

    source_type text not null
        check (
            source_type in (
                'government',
                'regulator',
                'certification_body',
                'official_company',
                'official_careers',
                'official_announcement',
                'news',
                'professional_network',
                'employee_review',
                'forum',
                'blog',
                'other'
            )
        ),

    published_at timestamptz,
    observed_at timestamptz not null default now(),

    reliability_score numeric(5,4)
        check (
            reliability_score >= 0
            and reliability_score <= 1
        ),

    confidence_score numeric(5,4)
        check (
            confidence_score >= 0
            and confidence_score <= 1
        ),

    verification_status text not null default 'unverified'
        check (
            verification_status in (
                'verified',
                'unverified',
                'conflicting',
                'unable_to_verify'
            )
        ),

    agent_name text,

    content_hash text,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ============================================================
-- 6. TRUST SCORES
-- Versioned algorithmic trust/risk results
-- ============================================================

create table if not exists public.trust_scores (
    id uuid primary key default gen_random_uuid(),

    company_id uuid not null
        references public.companies(id)
        on delete cascade,

    research_run_id uuid not null
        references public.research_runs(id)
        on delete cascade,

    score numeric(5,2)
        check (score >= 0 and score <= 100),

    confidence numeric(5,4)
        check (confidence >= 0 and confidence <= 1),

    risk_level text
        check (
            risk_level in (
                'low',
                'medium',
                'high',
                'critical',
                'unknown'
            )
        ),

    evidence_coverage numeric(5,4)
        check (
            evidence_coverage >= 0
            and evidence_coverage <= 1
        ),

    algorithm_version text not null,

    explanation text,

    created_at timestamptz not null default now()
);


-- ============================================================
-- 7. REPORTS
-- Final Company Intelligence Reports
-- ============================================================

create table if not exists public.reports (
    id uuid primary key default gen_random_uuid(),

    company_id uuid not null
        references public.companies(id)
        on delete cascade,

    research_run_id uuid not null
        references public.research_runs(id)
        on delete cascade,

    title text not null,

    content jsonb not null default '{}'::jsonb,

    report_version text not null default '1.0',

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);


-- ============================================================
-- INDEXES
-- ============================================================

create index if not exists company_identifiers_company_id_idx
on public.company_identifiers(company_id);

create index if not exists research_runs_user_id_idx
on public.research_runs(user_id);

create index if not exists research_runs_company_id_idx
on public.research_runs(company_id);

create index if not exists research_runs_status_idx
on public.research_runs(status);

create index if not exists research_runs_created_at_idx
on public.research_runs(created_at desc);

create index if not exists evidence_company_id_idx
on public.evidence(company_id);

create index if not exists evidence_research_run_id_idx
on public.evidence(research_run_id);

create index if not exists evidence_source_url_idx
on public.evidence(source_url);

create index if not exists evidence_observed_at_idx
on public.evidence(observed_at desc);

create index if not exists evidence_source_type_idx
on public.evidence(source_type);

create index if not exists evidence_verification_status_idx
on public.evidence(verification_status);

create index if not exists evidence_content_hash_idx
on public.evidence(content_hash);

create index if not exists trust_scores_company_id_idx
on public.trust_scores(company_id);

create index if not exists trust_scores_research_run_id_idx
on public.trust_scores(research_run_id);

create index if not exists trust_scores_created_at_idx
on public.trust_scores(created_at desc);

create index if not exists reports_company_id_idx
on public.reports(company_id);

create index if not exists reports_research_run_id_idx
on public.reports(research_run_id);

create index if not exists reports_created_at_idx
on public.reports(created_at desc);


-- ============================================================
-- UPDATED_AT TRIGGERS
-- ============================================================

drop trigger if exists profiles_updated_at on public.profiles;
create trigger profiles_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

drop trigger if exists companies_updated_at on public.companies;
create trigger companies_updated_at
before update on public.companies
for each row
execute function public.set_updated_at();

drop trigger if exists research_runs_updated_at on public.research_runs;
create trigger research_runs_updated_at
before update on public.research_runs
for each row
execute function public.set_updated_at();

drop trigger if exists evidence_updated_at on public.evidence;
create trigger evidence_updated_at
before update on public.evidence
for each row
execute function public.set_updated_at();

drop trigger if exists reports_updated_at on public.reports;
create trigger reports_updated_at
before update on public.reports
for each row
execute function public.set_updated_at();


-- ============================================================
-- PROFILE CREATION TRIGGER
-- Automatically creates a profile after Supabase Auth signup
-- ============================================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
    insert into public.profiles (id, full_name)
    values (
        new.id,
        coalesce(new.raw_user_meta_data ->> 'full_name', '')
    )
    on conflict (id) do nothing;

    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row
execute function public.handle_new_user();


-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

alter table public.profiles enable row level security;
alter table public.companies enable row level security;
alter table public.company_identifiers enable row level security;
alter table public.research_runs enable row level security;
alter table public.evidence enable row level security;
alter table public.trust_scores enable row level security;
alter table public.reports enable row level security;


-- ============================================================
-- RLS POLICIES
-- ============================================================

drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
on public.profiles
for select
to authenticated
using (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
on public.profiles
for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

drop policy if exists "Authenticated users can view companies" on public.companies;
create policy "Authenticated users can view companies"
on public.companies
for select
to authenticated
using (true);

drop policy if exists "Authenticated users can view company identifiers" on public.company_identifiers;
create policy "Authenticated users can view company identifiers"
on public.company_identifiers
for select
to authenticated
using (true);

drop policy if exists "Users can view own research runs" on public.research_runs;
create policy "Users can view own research runs"
on public.research_runs
for select
to authenticated
using (auth.uid() = user_id);

drop policy if exists "Users can create own research runs" on public.research_runs;
create policy "Users can create own research runs"
on public.research_runs
for insert
to authenticated
with check (auth.uid() = user_id);

drop policy if exists "Authenticated users can view evidence" on public.evidence;
create policy "Authenticated users can view evidence"
on public.evidence
for select
to authenticated
using (true);

drop policy if exists "Authenticated users can view trust scores" on public.trust_scores;
create policy "Authenticated users can view trust scores"
on public.trust_scores
for select
to authenticated
using (true);

drop policy if exists "Authenticated users can view reports" on public.reports;
create policy "Authenticated users can view reports"
on public.reports
for select
to authenticated
using (true);
