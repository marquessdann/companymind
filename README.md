# CompanyMind AI — Corporate Knowledge & AI Integration Platform

Plataforma de RAG (Retrieval-Augmented Generation) que permite consultar em linguagem natural a base de conhecimento interna de uma empresa simulada — políticas, procedimentos, produtos e FAQs — sem que o modelo invente respostas fora do que está documentado.

O projeto foi construído como estudo aprofundado de arquitetura de aplicações de IA em produção: RAG, embeddings, busca vetorial com pgvector, tool calling, MCP (Model Context Protocol) e as camadas de segurança e observabilidade que normalmente ficam de fora de tutoriais introdutórios.

## Por que este projeto existe

Chatbots que apenas encapsulam uma chamada ao ChatGPT não demonstram muita coisa em uma entrevista técnica. Este projeto foi desenhado para responder, com código real, perguntas como: como impedir que o modelo alucine informação corporativa? Como controlar o acesso aos dados que alimentam a IA? Como preparar um sistema para ser consumido por outros agentes no futuro, e não só por um chat?

## Stack

| Camada | Tecnologia |
|---|---|
| API | FastAPI + Pydantic v2 |
| Banco de dados | Supabase (PostgreSQL) |
| Busca vetorial | pgvector (similaridade de cosseno) |
| LLM / Embeddings | OpenAI API (`gpt-4o-mini`, `text-embedding-3-small`) |
| Protocolo de integração | MCP (Model Context Protocol) |
| Infra local | Docker / docker-compose |
| Testes | pytest |

## Arquitetura

```
usuário → POST /api/v1/chat
              ↓
        gera embedding da pergunta (OpenAI)
              ↓
        busca vetorial no Supabase/pgvector (match_document_chunks)
              ↓
        sanitiza os chunks recuperados (defesa contra prompt injection)
              ↓
        monta o contexto e chama o LLM com system prompt fixo (config/ai_policy.py)
              ↓
        loga a consulta (query_logs) e retorna resposta + fontes + similaridade
```

Se a busca vetorial não retornar nenhum chunk acima do `SIMILARITY_THRESHOLD`, o pipeline **nem chama o LLM** — ele já responde com a mensagem padrão de "não encontrei informação suficiente". Isso é intencional: reduz custo de API e elimina a possibilidade de o modelo tentar "ajudar" inventando algo.

### Estrutura de pastas

```
app/
  api/v1/        endpoints (chat, search, documents, admin, health, metrics)
  core/          configuração (variáveis de ambiente)
  schemas/       contratos de entrada/saída (Pydantic)
  services/      embeddings, chunking, logs
  repositories/  acesso a dados (Supabase)
  rag/           orquestração do pipeline de RAG
  llm/           cliente de chat completion
  mcp/           tools compartilhadas + MCP Server
  security/      autenticação admin + defesa contra prompt injection
  database/      cliente Supabase
config/
  ai_policy.py   identidade, regras e limites do assistente (separado do código de negócio)
sql/
  schema.sql     tabelas, índice vetorial, função de match e RLS
scripts/
  seed_data.py   popula o banco com documentos fictícios
  ingest_file.py ingestão de arquivos TXT/MD/PDF via CLI
tests/           pytest
frontend/        demo estática em HTML/JS puro
```

## Como rodar localmente

### 1. Pré-requisitos

- Python 3.12+
- Conta no [Supabase](https://supabase.com) (plano free é suficiente)
- Chave de API da OpenAI

### 2. Configurar o Supabase

1. Crie um projeto novo no Supabase.
2. Abra o **SQL Editor** e execute o conteúdo de `sql/schema.sql`. Isso habilita a extensão `pgvector`, cria as tabelas (`documents`, `document_chunks`, `query_logs`), o índice vetorial `ivfflat`, a função `match_document_chunks` e as políticas de Row Level Security.
3. Copie a `URL`, a `anon key` e a `service_role key` do projeto (em *Project Settings → API*).

**Importante sobre a service role key**: ela tem acesso total ao banco e ignora RLS. Ela é usada **apenas no backend**, nunca no frontend. O frontend, se algum dia precisar acessar o Supabase diretamente, deve usar a `anon key`, que respeita as políticas de RLS definidas em `sql/schema.sql` — e essas políticas liberam apenas leitura de `documents`/`document_chunks`, bloqueando `query_logs` e qualquer escrita.

### 3. Configurar o projeto

```bash
git clone <seu-fork>
cd companymind-ai
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Preencha o `.env` com as credenciais do Supabase e da OpenAI.

### 4. Popular a base com dados de exemplo

```bash
python scripts/seed_data.py
```

Isso insere seis documentos fictícios (política de férias, home office, reembolso, ficha de produto, FAQ de senha, onboarding), gera os embeddings de cada chunk e grava no Supabase.

### 5. Subir a API

```bash
uvicorn app.main:app --reload
```

Acesse `http://localhost:8000/docs` para o Swagger gerado automaticamente pelo FastAPI.

### 6. Testar uma pergunta

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual é a política de férias?"}'
```

Resposta esperada (resumida):

```json
{
  "answer": "Você tem direito a 30 dias corridos de férias por ano trabalhado...",
  "sources": [
    { "document_title": "Política de Férias", "similarity": 0.89, "content": "..." }
  ],
  "has_sufficient_context": true,
  "model_used": "gpt-4o-mini",
  "response_time_ms": 743
}
```

Pergunta fora da base:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual é a política de férias em Marte?"}'
```

```json
{
  "answer": "Não encontrei informação suficiente na base de conhecimento da empresa para responder esta pergunta.",
  "sources": [],
  "has_sufficient_context": false
}
```

### 7. Rodar com Docker (opcional)

```bash
docker compose up --build
```

### 8. Frontend de demonstração

Abra `frontend/index.html` direto no navegador com a API rodando em `localhost:8000`.

## RAG, tool calling e MCP — quando usar cada um

Os três resolvem "dar contexto externo ao modelo", mas em momentos e granularidades diferentes:

- **RAG** é usado dentro do próprio pipeline de `/chat`: a pergunta vira embedding, busca chunks relevantes e injeta esse texto no prompt antes de chamar o LLM. É a técnica principal para responder perguntas sobre a base de conhecimento.
- **Tool calling** é quando o próprio LLM decide, durante a conversa, chamar uma função específica (`app/mcp/tools.py`) em vez de depender só do contexto que já foi injetado — por exemplo, para listar departamentos ou buscar um produto específico por nome.
- **MCP** é a camada de distribuição dessas mesmas tools (`app/mcp/server.py`) para **fora** do processo da API: qualquer cliente compatível com o protocolo (Claude Desktop, outro agente, outro backend) pode descobrir e chamar `search_company_knowledge`, `get_company_policy`, etc., sem precisar conhecer a implementação REST.

Na prática: RAG resolve "responder com base em texto recuperado", tool calling resolve "o modelo decide executar uma ação/consulta", MCP resolve "expor essas ações para fora da aplicação de forma padronizada".

## RAG vs. fine-tuning

Fine-tuning não foi usado neste projeto porque não resolveria o problema real: a empresa precisa que a IA responda com informação **atualizada e rastreável**, e documentos corporativos mudam com frequência. Treinar um modelo do zero a cada atualização de política é caro e lento, e ainda assim não garante rastreabilidade da fonte.

RAG resolve isso porque o conhecimento vive no banco de dados, não nos pesos do modelo — atualizar um documento é um `INSERT`/`UPDATE`, não um retreinamento.

Fine-tuning faria sentido em uma segunda versão do projeto para ajustar **estilo e comportamento** do assistente (ex.: um tom de escrita muito específico da marca, ou um formato de resposta estruturado altamente repetitivo), não para ensinar fatos novos.

## Segurança

- Segredos apenas em `.env` (nunca commitado — ver `.gitignore`).
- `service_role key` do Supabase usada só no backend; o frontend nunca a recebe.
- Row Level Security habilitada em todas as tabelas (`sql/schema.sql`), com policies explícitas de somente-leitura.
- Endpoints administrativos (`/api/v1/admin/*`) protegidos por header `X-Admin-Key`, separados dos endpoints públicos.
- Validação de entrada em todos os endpoints via Pydantic.
- Defesa contra prompt injection: qualquer chunk recuperado que contenha marcadores típicos de instrução embutida (`"ignore as instruções anteriores"`, etc.) é sinalizado antes de entrar no prompt — ver `app/security/prompt_injection.py` e o teste correspondente em `tests/test_prompt_injection.py`.
- O system prompt (`config/ai_policy.py`) instrui explicitamente o modelo a tratar documentos recuperados como dado, nunca como comando.
- Se a busca vetorial não retorna contexto suficiente, o LLM nem é chamado — elimina a superfície de alucinação nesse caminho.

## Observabilidade

Toda chamada a `/api/v1/chat` grava um registro em `query_logs` com pergunta, quantidade de chunks recuperados, maior similaridade encontrada e tempo de resposta. O endpoint `GET /api/v1/metrics` agrega isso em total de consultas, tempo médio de resposta, quantidade de perguntas sem contexto suficiente e taxa de erro.

## Testes

```bash
pytest
```

Cobertura inclui: schemas Pydantic, chunking de texto, defesa contra prompt injection e o pipeline de RAG (com Supabase/OpenAI mockados, sem custo de API nos testes).

## Roadmap

- [ ] Autenticação de usuários finais (não só admin) via Supabase Auth
- [ ] Streaming de resposta (SSE) no endpoint de chat
- [ ] Reranking dos chunks recuperados antes de montar o contexto
- [ ] Versão 2 com fine-tuning de estilo sobre um modelo pequeno
- [ ] Deploy em produção (Railway/Fly.io para a API, Supabase já é gerenciado)
- [ ] Painel de métricas em `frontend/` além do endpoint `/metrics`

## Preparando para entrevista

O arquivo [`docs/interview-notes.md`](docs/interview-notes.md) reúne, em linguagem direta, as respostas para as perguntas mais prováveis sobre este projeto: o que é RAG, embeddings, busca vetorial, por que pgvector, por que Supabase, RAG vs. fine-tuning, API vs. MCP, RAG vs. tool calling, como os dados foram protegidos, como as alucinações foram reduzidas, controle de acesso, organização do backend e como isso iria para produção.
