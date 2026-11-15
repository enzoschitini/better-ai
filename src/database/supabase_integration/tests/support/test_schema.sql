-- Schema MINIMO para os testes de integracao (rode UMA vez no projeto Supabase DE TESTE).
-- A integracao NAO faz DDL (constituicao P10): isto e preparacao manual.
create table if not exists public.sbx_test_items (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  qty integer default 0,
  bucket text,
  path text,
  created_at timestamptz not null default now()
);
-- Acesso so via chave secret (service_role) do backend; sem politicas para anon/authenticated.
alter table public.sbx_test_items enable row level security;
-- Crie tambem o bucket PRIVADO indicado em SBX_TEST_BUCKET (ex.: it-bucket) no painel Storage.
