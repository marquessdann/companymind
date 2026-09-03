# CompanyMind AI

RAG corporativo: uma API que responde perguntas em linguagem natural sobre a base de conhecimento interna de uma empresa (políticas, procedimentos, produtos, FAQs), restringindo as respostas ao que está de fato documentado. Sem contexto recuperado com similaridade suficiente, o modelo não é chamado — a API retorna direto que não há informação suficiente, em vez de deixar o LLM tentar preencher a lacuna.

## Stack

FastAPI + Pydantic v2 na API. Supabase (PostgreSQL) como banco, com pgvector para o armazenamento e busca dos embeddings. OpenAI para geração de embeddings e chat completion. MCP para expor as mesmas ferramentas de busca fora do processo da API. Docker para empacotamento local.

## Arquitetura

```
POST /api/v1/chat
    → embedding da pergunta
    → match_document_chunks (pgvector, similaridade de cosseno)
    → sanitização dos chunks recuperados (prompt injection)
    → chat completion com o contexto recuperado
    → log da consulta (query_logs)
    → resposta + fontes + similaridade
```

A busca vetorial roda como função SQL no próprio Postgres (`match_document_chunks`, em `sql/schema.sql`), não em memória na aplicação — o índice `ivfflat` sobre a coluna `vector(1536)` é quem faz o trabalho pesado.

```
app/
  api/v1/        endpoints REST
  core/          configuração via variáveis de ambiente
  schemas/       contratos Pydantic de entrada/saída
  services/      embeddings, chunking, logging de consultas
  repositories/  acesso a dados (Supabase)
  rag/           orquestração do pipeline
  llm/           cliente de chat completion
  mcp/           tools compartilhadas + MCP Server
  security/      auth admin, defesa contra prompt injection
  database/      cliente Supabase
config/
  ai_policy.py   system prompt e regras do assistente, isolado do código de negócio
sql/
  schema.sql     tabelas, índice vetorial, função de match, RLS
scripts/
  seed_data.py, ingest_file.py
tests/
```

## RAG, tool calling e MCP

Três coisas diferentes que costumam ser confundidas. RAG resolve "responder com base em texto recuperado" — acontece dentro do próprio pipeline de `/chat`, de forma automática, antes de qualquer resposta. Tool calling é o modelo decidindo, em tempo de execução, chamar uma função específica (implementado em `app/llm/client.py`, usando o parâmetro `tools` da API da OpenAI) para obter um dado pontual, em vez de depender só do contexto já injetado — hoje isso cobre `list_company_departments`. MCP é a camada que expõe essas mesmas funções para fora do processo — qualquer cliente compatível com o protocolo descobre e chama `search_company_knowledge`, `get_company_policy`, etc., sem acoplamento à implementação REST. As três camadas reaproveitam a mesma lógica de negócio em `app/mcp/tools.py`; não há três implementações separadas da mesma busca.

Fine-tuning não entrou no escopo porque não resolve o problema real do projeto: os documentos mudam com frequência e a resposta precisa ser rastreável até a fonte. RAG resolve isso puxando o conhecimento do banco em tempo de consulta; fine-tuning faria sentido para ajustar estilo e comportamento do assistente, não para ensinar fatos que mudam.

## Segurança

RLS habilitada em todas as tabelas, com policies de leitura pública apenas para `documents`/`document_chunks` — `query_logs` é bloqueada por padrão. A aplicação usa a `service_role key` do Supabase apenas no backend; o frontend nunca tem acesso a ela. Endpoints administrativos (`/api/v1/admin/*`, além de `/api/v1/documents` e `/api/v1/metrics`) exigem um header separado dos endpoints públicos. CORS restrito às origens configuradas em `Settings.allowed_origins` (não aberto para qualquer site). Todo chunk recuperado passa por `app/security/prompt_injection.py`, que sinaliza — sem descartar — trechos que se parecem com instruções embutidas no documento, e o system prompt trata explicitamente conteúdo recuperado como dado, nunca como comando.

## Observabilidade

Cada chamada a `/chat` grava pergunta, quantidade de chunks recuperados, maior similaridade encontrada, tempo de resposta e se houve erro. `/api/v1/metrics` agrega isso em total de consultas, tempo médio de resposta, taxa de perguntas sem contexto suficiente e taxa de erro. Erros da API da OpenAI e exceções não tratadas são capturados por exception handlers globais em `app/main.py`, logados via `logging`, e nunca retornam stack trace para o cliente.

## Testes

Cobertura de schemas, chunking, defesa contra prompt injection e o pipeline de RAG completo, com Supabase e OpenAI mockados — a suíte roda sem depender de rede ou gastar chamada de API.

## CI

GitHub Actions (`.github/workflows/tests.yml`) roda a suíte de testes a cada push e pull request para `main`.

## Roadmap

Autenticação de usuário final via Supabase Auth. Frontend estático de demo (HTML/JS) consumindo a API via fetch. Streaming de resposta via SSE. Reranking dos chunks antes de montar o contexto. Deploy da API em Railway ou Fly.io. Painel de métricas próprio além do endpoint `/metrics`.
