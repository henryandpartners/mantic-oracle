-- Mantic Oracle — consultation memory table.
-- Run once against the Supabase project (SQL editor or psql).

create table if not exists oracle_consultations (
    id          uuid primary key default gen_random_uuid(),
    agent_id    text        not null,
    decision    text,
    judge       text,
    hexagram    text,
    odu         text,
    voice       jsonb,
    cast_at     timestamptz not null default now()
);

create index if not exists oracle_consultations_agent_idx
    on oracle_consultations (agent_id, cast_at desc);

-- Row Level Security: off for now; access is service-key only
-- (RLS with service-role bypass is the default posture for tables
-- written exclusively server-side).
alter table oracle_consultations enable row level security;

-- Retention: consultations are memories, not records. Keep 90 days.
-- (Wire as a pg_cron job if desired:
--  select cron.schedule('oracle-memory-trim', '17 4 * * *', $$
--    delete from oracle_consultations where cast_at < now() - interval '90 days'
--  $$);)
