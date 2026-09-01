# Notas para entrevista técnica — CompanyMind AI

Respostas curtas e diretas, em linguagem própria, para as perguntas mais prováveis sobre este projeto.

**Como funciona RAG?**
A pergunta do usuário é transformada em vetor (embedding). Esse vetor é comparado por similaridade contra os vetores dos trechos de documentos já armazenados no banco. Os trechos mais próximos semanticamente são recuperados e inseridos no prompt enviado ao LLM, junto com a pergunta original. O modelo responde com base nesse contexto, em vez de depender só do que aprendeu no treinamento.

**O que são embeddings?**
Representações numéricas (vetores) de um texto, geradas por um modelo especializado, de forma que textos com significado parecido fiquem próximos nesse espaço vetorial. Duas frases diferentes na escrita mas com o mesmo sentido têm embeddings próximos.

**Como funciona busca vetorial?**
Em vez de buscar por palavras-chave exatas, calcula-se a distância (aqui, similaridade de cosseno) entre o vetor da pergunta e os vetores armazenados, retornando os N mais próximos. Isso é o que permite encontrar "política de férias" mesmo que a pergunta seja "quantos dias de descanso eu tenho por ano".

**Por que pgvector?**
Porque o Supabase já é PostgreSQL, e o pgvector adiciona o tipo `vector` e índices (`ivfflat`) diretamente no mesmo banco relacional. Isso evita manter um banco vetorial separado (Pinecone, Weaviate, etc.) só para esse projeto — dado, metadado e vetor moram na mesma tabela, com as mesmas garantias transacionais.

**Por que Supabase?**
PostgreSQL gerenciado, com pgvector disponível, Row Level Security nativo e uma API REST/SDK prontos, o que reduz bastante a infraestrutura que eu mesmo precisaria manter para um projeto de portfólio, sem abrir mão de um banco relacional "de verdade".

**RAG vs. fine-tuning?**
RAG muda o que o modelo *sabe* sem retreinar nada — o conhecimento vive no banco. Fine-tuning muda *como* o modelo se comporta (estilo, formato, tom), ajustando os pesos. Para dados corporativos que mudam com frequência e precisam de rastreabilidade de fonte, RAG é a escolha certa. Fine-tuning faria sentido para um comportamento muito específico e estável ao longo do tempo.

**API vs. MCP?**
Uma API REST é um contrato específico que cada cliente precisa aprender a consumir. MCP é um protocolo padronizado para expor "ferramentas" (funções) de forma que qualquer agente compatível consiga descobrir o que existe e como chamar, sem acoplamento a uma implementação REST específica. Neste projeto, as mesmas funções de busca (`app/mcp/tools.py`) são reaproveitadas pela API e pelo MCP Server — a lógica de negócio não se repete.

**RAG vs. tool calling?**
RAG injeta contexto automaticamente antes da resposta. Tool calling é o modelo decidindo, durante o raciocínio, chamar uma função específica para obter um dado que precisa naquele momento (ex.: listar departamentos). Podem coexistir: o pipeline principal usa RAG, mas o modelo também tem acesso a tools pontuais.

**Como os dados foram protegidos?**
Row Level Security habilitada em todas as tabelas, com policies explícitas de somente leitura para `documents`/`document_chunks` e bloqueio total de leitura pública em `query_logs`. A `service_role key`, que ignora RLS, só existe no backend — nunca é exposta ao frontend. Endpoints administrativos exigem uma chave separada dos endpoints públicos.

**Como evitei alucinações?**
Três camadas: (1) o pipeline só chama o LLM se a busca vetorial encontrar chunks acima de um limiar de similaridade — sem contexto suficiente, a resposta padrão é retornada sem gastar chamada de API; (2) o system prompt instrui explicitamente o modelo a responder só com base no contexto fornecido; (3) a resposta sempre retorna as fontes e a similaridade usadas, então é possível auditar se a resposta realmente veio da base.

**Como fiz controle de acesso?**
RLS no banco (camada de dados) + chave administrativa separada para endpoints de escrita (camada de aplicação). A aplicação de IA em si só tem permissão de leitura sobre os dados corporativos usados no RAG.

**Como organizei o backend?**
Separação por responsabilidade: `api` só lida com HTTP, `schemas` valida entrada/saída, `services` tem lógica reaproveitável (embeddings, chunking), `repositories` isola acesso a dados, `rag`/`llm`/`mcp` são as camadas específicas de IA, e `security` concentra as regras de proteção. A configuração de comportamento da IA (`config/ai_policy.py`) fica fora do código de negócio de propósito, para poder mudar sem tocar no pipeline.

**Como colocaria isso em produção?**
API em um serviço gerenciado (Railway, Fly.io ou similar) atrás de HTTPS, com variáveis de ambiente via secrets do próprio provedor. Supabase já é gerenciado. Adicionaria autenticação real de usuário final (Supabase Auth), rate limiting por usuário, um índice vetorial ajustado ao volume real de documentos, e observabilidade além do banco (ex.: exportar métricas para um serviço de monitoramento).
