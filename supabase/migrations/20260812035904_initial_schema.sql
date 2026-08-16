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

create table public.profiles (
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

create table public.companies (
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

create unique index companies_normalized_name_idx
on public.companies (normalized_name);


-- ============================================================
-- 3. COMPANY IDENTIFIERS
-- Stores identifiers used for identity resolution
-- ============================================================

create table public.company_identifiers (
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

create table public.research_runs (
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

create table public.evidence (
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

create table public.trust_scores (
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

create table public.reports (
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

create index company_identifiers_company_id_idx
on public.company_identifiers(company_id);

create index research_runs_user_id_idx
on public.research_runs(user_id);

create index research_runs_company_id_idx
on public.research_runs(company_id);

create index research_runs_status_idx
on public.research_runs(status);

create index research_runs_created_at_idx
on public.research_runs(created_at desc);

create index evidence_company_id_idx
on public.evidence(company_id);

create index evidence_research_run_id_idx
on public.evidence(research_run_id);

create index evidence_source_url_idx
on public.evidence(source_url);

create index evidence_observed_at_idx
on public.evidence(observed_at desc);

create index evidence_source_type_idx
on public.evidence(source_type);

create index evidence_verification_status_idx
on public.evidence(verification_status);

create index evidence_content_hash_idx
on public.evidence(content_hash);

create index trust_scores_company_id_idx
on public.trust_scores(company_id);

create index trust_scores_research_run_id_idx
on public.trust_scores(research_run_id);

create index trust_scores_created_at_idx
on public.trust_scores(created_at desc);

create index reports_company_id_idx
on public.reports(company_id);

create index reports_research_run_id_idx
on public.reports(research_run_id);

create index reports_created_at_idx
on public.reports(created_at desc);


-- ============================================================
-- UPDATED_AT TRIGGERS
-- ============================================================

create trigger profiles_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

create trigger companies_updated_at
before update on public.companies
for each row
execute function public.set_updated_at();

create trigger research_runs_updated_at
before update on public.research_runs
for each row
execute function public.set_updated_at();

create trigger evidence_updated_at
before update on public.evidence
for each row
execute function public.set_updated_at();

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
    );

    return new;
end;
$$;

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
-- PROFILES POLICIES
-- ============================================================

create policy "Users can view own profile"
on public.profiles
for select
to authenticated
using (auth.uid() = id);

create policy "Users can update own profile"
on public.profiles
for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);


-- ============================================================
-- COMPANIES POLICIES
-- Companies are readable by authenticated users.
-- Creation/modification will later be controlled by backend.
-- ============================================================

create policy "Authenticated users can view companies"
on public.companies
for select
to authenticated
using (true);


-- ============================================================
-- COMPANY IDENTIFIERS POLICIES
-- ============================================================

create policy "Authenticated users can view company identifiers"
on public.company_identifiers
for select
to authenticated
using (true);


-- ============================================================
-- RESEARCH RUN POLICIES
-- Users can access only their own research runs.
-- ============================================================

create policy "Users can view own research runs"
on public.research_runs
for select
to authenticated
using (auth.uid() = user_id);

create policy "Users can create own research runs"
on public.research_runs
for insert
to authenticated
with check (auth.uid() = user_id);


-- ============================================================
-- EVIDENCE POLICIES
-- Evidence is accessible only when the related research run
-- belongs to the authenticated user.
-- ============================================================

create policy "Users can view own research evidence"
on public.evidence
for select
to authenticated
using (
    exists (
        select 1
        from public.research_runs rr
        where rr.id = evidence.research_run_id
          and rr.user_id = auth.uid()
    )
);


-- ============================================================
-- TRUST SCORE POLICIES
-- ============================================================

create policy "Users can view own trust scores"
on public.trust_scores
for select
to authenticated
using (
    exists (
        select 1
        from public.research_runs rr
        where rr.id = trust_scores.research_run_id
          and rr.user_id = auth.uid()
    )
);


-- ============================================================
-- REPORT POLICIES
-- ============================================================

create policy "Users can view own reports"
on public.reports
for select
to authenticated
using (
    exists (
        select 1
        from public.research_runs rr
        where rr.id = reports.research_run_id
          and rr.user_id = auth.uid()
    )
);


-- ============================================================
-- END OF INITIAL SCHEMA
-- ============================================================