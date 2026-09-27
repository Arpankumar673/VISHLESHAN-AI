-- ============================================================
-- VISHLESHAN AI v2 — M2 Migration
-- RAG Evidence Vector Embeddings & Similarity Search (pgvector)
-- ============================================================

-- Ensure pgvector extension is enabled
create extension if not exists "vector";

-- ------------------------------------------------------------
-- EVIDENCE EMBEDDINGS TABLE
-- Stores 1536-dimensional text-embedding-3-small vector chunks
-- ------------------------------------------------------------

create table if not exists public.evidence_embeddings (
    id uuid primary key default gen_random_uuid(),

    evidence_id uuid not null
        references public.evidence(id)
        on delete cascade,

    company_id uuid not null
        references public.companies(id)
        on delete cascade,

    research_run_id uuid not null
        references public.research_runs(id)
        on delete cascade,

    chunk_index integer not null default 0,
    chunk_text text not null,

    embedding vector(1536) not null,

    metadata jsonb not null default '{}'::jsonb,

    embedding_model text not null default 'text-embedding-3-small',

    created_at timestamptz not null default now(),

    unique (evidence_id, chunk_index, embedding_model)
);

-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------

create index if not exists evidence_embeddings_company_id_idx
on public.evidence_embeddings(company_id);

create index if not exists evidence_embeddings_research_run_id_idx
on public.evidence_embeddings(research_run_id);

create index if not exists evidence_embeddings_evidence_id_idx
on public.evidence_embeddings(evidence_id);

-- HNSW Vector Index for Cosine Distance Similarity Search
create index if not exists evidence_embeddings_vector_cosine_idx
on public.evidence_embeddings
using hnsw (embedding vector_cosine_ops);

-- ------------------------------------------------------------
-- ROW LEVEL SECURITY
-- ------------------------------------------------------------

alter table public.evidence_embeddings enable row level security;

drop policy if exists "Authenticated users can view evidence embeddings" on public.evidence_embeddings;
create policy "Authenticated users can view evidence embeddings"
on public.evidence_embeddings
for select
to authenticated
using (true);

-- ------------------------------------------------------------
-- RPC FUNCTION: MATCH EVIDENCE CHUNKS
-- Company-isolated vector similarity search using Cosine Distance
-- ------------------------------------------------------------

create or replace function public.match_evidence_chunks(
    query_embedding vector(1536),
    match_company_id uuid,
    match_threshold float default 0.0,
    match_count int default 5
)
returns table (
    id uuid,
    evidence_id uuid,
    company_id uuid,
    research_run_id uuid,
    chunk_index int,
    chunk_text text,
    similarity float,
    metadata jsonb
)
language plpgsql
security definer
set search_path = public
as $$
begin
    return query
    select
        ee.id,
        ee.evidence_id,
        ee.company_id,
        ee.research_run_id,
        ee.chunk_index,
        ee.chunk_text,
        cast(1 - (ee.embedding <=> query_embedding) as float) as similarity,
        ee.metadata
    from public.evidence_embeddings ee
    where ee.company_id = match_company_id
      and (1 - (ee.embedding <=> query_embedding)) >= match_threshold
    order by ee.embedding <=> query_embedding asc
    limit match_count;
end;
$$;
