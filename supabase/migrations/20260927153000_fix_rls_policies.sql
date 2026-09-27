-- ============================================================
-- VISHLESHAN AI — RLS POLICIES & PERMISSIONS FIX
-- Run this script in the Supabase SQL Editor if using publishable/anon keys
-- or if backend inserts fail with 42501 RLS policy violation.
-- ============================================================

-- 1. COMPANIES
drop policy if exists "Enable insert for authenticated and anon" on public.companies;
create policy "Enable insert for authenticated and anon"
on public.companies for insert
to authenticated, anon
with check (true);

drop policy if exists "Enable update for authenticated and anon" on public.companies;
create policy "Enable update for authenticated and anon"
on public.companies for update
to authenticated, anon
using (true);

drop policy if exists "Enable select for authenticated and anon" on public.companies;
create policy "Enable select for authenticated and anon"
on public.companies for select
to authenticated, anon
using (true);


-- 2. COMPANY IDENTIFIERS
drop policy if exists "Enable insert for authenticated and anon" on public.company_identifiers;
create policy "Enable insert for authenticated and anon"
on public.company_identifiers for insert
to authenticated, anon
with check (true);

drop policy if exists "Enable update for authenticated and anon" on public.company_identifiers;
create policy "Enable update for authenticated and anon"
on public.company_identifiers for update
to authenticated, anon
using (true);

drop policy if exists "Enable select for authenticated and anon" on public.company_identifiers;
create policy "Enable select for authenticated and anon"
on public.company_identifiers for select
to authenticated, anon
using (true);


-- 3. RESEARCH RUNS
drop policy if exists "Enable insert for authenticated and anon" on public.research_runs;
create policy "Enable insert for authenticated and anon"
on public.research_runs for insert
to authenticated, anon
with check (true);

drop policy if exists "Enable update for authenticated and anon" on public.research_runs;
create policy "Enable update for authenticated and anon"
on public.research_runs for update
to authenticated, anon
using (true);

drop policy if exists "Enable select for authenticated and anon" on public.research_runs;
create policy "Enable select for authenticated and anon"
on public.research_runs for select
to authenticated, anon
using (true);


-- 4. EVIDENCE
drop policy if exists "Enable insert for authenticated and anon" on public.evidence;
create policy "Enable insert for authenticated and anon"
on public.evidence for insert
to authenticated, anon
with check (true);

drop policy if exists "Enable update for authenticated and anon" on public.evidence;
create policy "Enable update for authenticated and anon"
on public.evidence for update
to authenticated, anon
using (true);

drop policy if exists "Enable select for authenticated and anon" on public.evidence;
create policy "Enable select for authenticated and anon"
on public.evidence for select
to authenticated, anon
using (true);


-- 5. TRUST SCORES
drop policy if exists "Enable insert for authenticated and anon" on public.trust_scores;
create policy "Enable insert for authenticated and anon"
on public.trust_scores for insert
to authenticated, anon
with check (true);

drop policy if exists "Enable update for authenticated and anon" on public.trust_scores;
create policy "Enable update for authenticated and anon"
on public.trust_scores for update
to authenticated, anon
using (true);

drop policy if exists "Enable select for authenticated and anon" on public.trust_scores;
create policy "Enable select for authenticated and anon"
on public.trust_scores for select
to authenticated, anon
using (true);


-- 6. REPORTS
drop policy if exists "Enable insert for authenticated and anon" on public.reports;
create policy "Enable insert for authenticated and anon"
on public.reports for insert
to authenticated, anon
with check (true);

drop policy if exists "Enable update for authenticated and anon" on public.reports;
create policy "Enable update for authenticated and anon"
on public.reports for update
to authenticated, anon
using (true);

drop policy if exists "Enable select for authenticated and anon" on public.reports;
create policy "Enable select for authenticated and anon"
on public.reports for select
to authenticated, anon
using (true);
