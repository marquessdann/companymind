-- CompanyMind AI — schema do banco (Supabase / PostgreSQL + pgvector)
--
-- Execute este arquivo no SQL Editor do Supabase (ou via migração) antes
-- de rodar a aplicação. Requer a extensão "vector" habilitada no projeto
-- (Database → Extensions → vector, no painel do Supabase).

create extension if not exists vector;
create extension if not exists pgcrypto; -- gen_random_uuid()

-- ============================================================
-- Tabelas
-- ============================================================

create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    category text not null,          -- policy | procedure | product | faq | general
    department text,
    created_at timestamptz not null default now()
);

create table if not exists document_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid not null references documents(id) on delete cascade,
    content text not null,
    embedding vector(1536) not null,  -- text-embedding-3-small tem 1536 dimensões
    created_at timestamptz not null default now()
);

create table if not exists query_logs (
    id uuid primary key default gen_random_uuid(),
    question text not null,
    answer text not null,
    retrieved_chunks_count int not null,
    top_similarity float,
    response_time_ms int not null,
    had_error boolean not null default false,
    created_at timestamptz not null default now()
);

-- ============================================================
-- Índice vetorial
-- ============================================================
-- ivfflat precisa de massa de dados para o índice ser bem calibrado;
-- "lists" pode ser ajustado conforme o volume real de documentos
-- (regra prática: aproximadamente sqrt(número de linhas)).

create index if not exists document_chunks_embedding_idx
    on document_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

create index if not exists document_chunks_document_id_idx
    on document_chunks (document_id);

-- ============================================================
-- Função de busca por similaridade
-- ============================================================
-- Chamada pela aplicação via supabase.rpc("match_document_chunks", {...})
-- em app/repositories/documents_repository.py.

create or replace function match_document_chunks(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    filter_department text default null
)
returns table (
    document_id uuid,
    document_title text,
    content text,
    similarity float
)
language sql stable
as $$
    select
        dc.document_id,
        d.title as document_title,
        dc.content,
        1 - (dc.embedding <=> query_embedding) as similarity
    from document_chunks dc
    join documents d on d.id = dc.document_id
    where
        1 - (dc.embedding <=> query_embedding) > match_threshold
        and (filter_department is null or d.department = filter_department)
    order by dc.embedding <=> query_embedding
    limit match_count;
$$;

-- ============================================================
-- Row Level Security
-- ============================================================

alter table documents enable row level security;
alter table document_chunks enable row level security;
alter table query_logs enable row level security;

-- Leitura pública de documentos e chunks. A aplicação usa a service_role
-- key (que ignora RLS) para todas as operações no backend; estas policies
-- existem para o caso de a anon key ser usada em algum fluxo de leitura
-- direto do cliente no futuro.
create policy "documents are publicly readable"
    on documents for select
    using (true);

create policy "document_chunks are publicly readable"
    on document_chunks for select
    using (true);

-- query_logs é bloqueada por padrão: nenhuma policy de select é criada
-- para roles públicas (anon/authenticated). Só a service_role key
-- consegue ler/escrever nessa tabela, e ela só existe no backend
-- (nunca é exposta ao frontend).
