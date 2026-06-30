create extension if not exists "pgcrypto";

create table if not exists public.buddy_access_checks (
    id uuid primary key,
    place jsonb not null,
    needs jsonb not null,
    stage text not null,
    timeline jsonb not null default '[]'::jsonb,
    evidence jsonb not null default '[]'::jsonb,
    analysis jsonb,
    call_session jsonb,
    final_report jsonb,
    community_report jsonb,
    created_at timestamptz not null,
    updated_at timestamptz not null
);

create table if not exists public.buddy_community_reports (
    id uuid primary key,
    check_id uuid not null references public.buddy_access_checks(id) on delete cascade,
    place jsonb not null,
    status text not null,
    public_summary text not null,
    evidence_summary text not null,
    voice_conversation_summary text,
    expires_at timestamptz not null,
    created_at timestamptz not null
);

create index if not exists buddy_access_checks_updated_at_idx
    on public.buddy_access_checks (updated_at desc);

create index if not exists buddy_community_reports_status_idx
    on public.buddy_community_reports (status);

create index if not exists buddy_community_reports_expires_at_idx
    on public.buddy_community_reports (expires_at);

alter table public.buddy_access_checks enable row level security;
alter table public.buddy_community_reports enable row level security;

drop policy if exists "Service role manages buddy access checks"
    on public.buddy_access_checks;
create policy "Service role manages buddy access checks"
    on public.buddy_access_checks
    for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

drop policy if exists "Service role manages buddy community reports"
    on public.buddy_community_reports;
create policy "Service role manages buddy community reports"
    on public.buddy_community_reports
    for all
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

drop policy if exists "Anon reads unexpired buddy community reports"
    on public.buddy_community_reports;
create policy "Anon reads unexpired buddy community reports"
    on public.buddy_community_reports
    for select
    using (expires_at > now());
