import json

from openai import OpenAI

from app.core.config import get_settings
from config.ai_policy import SYSTEM_PROMPT, RESPONSE_WHEN_NO_CONTEXT
from app.mcp.tools import list_company_departments

settings = get_settings()
_client = OpenAI(api_key=settings.openai_api_key)

# Tool calling de verdade: o modelo pode decidir, durante a geração da
# resposta, chamar list_company_departments() quando a pergunta for sobre
# "quais áreas/departamentos existem" em vez de sobre o conteúdo de um
# documento específico (que já vem via RAG no contexto). É a mesma função
# reaproveitada pelo MCP Server (app/mcp/server.py) — nenhuma lógica
# duplicada entre as duas camadas.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_company_departments",
            "description": (
                "Lista os departamentos da empresa que possuem documentos "
                "cadastrados na base de conhecimento. Use quando a pergunta "
                "for sobre quais áreas/departamentos existem — não para "
                "perguntas sobre o conteúdo de uma política ou procedimento "
                "específico, que já vêm no contexto recuperado."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
]

AVAILABLE_TOOLS = {"list_company_departments": list_company_departments}


def build_context_block(chunks: list[dict]) -> str:
    if not chunks:
        return ""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(f"[Fonte {i} - {chunk['document_title']}]\n{chunk['content']}")
    return "\n\n".join(parts)


def ask_llm(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return RESPONSE_WHEN_NO_CONTEXT

    context = build_context_block(chunks)

    user_message = (
        f"CONTEXTO RECUPERADO DA BASE DE CONHECIMENTO:\n{context}\n\n"
        f"PERGUNTA DO FUNCIONÁRIO:\n{question}\n\n"
        "Responda usando apenas o contexto acima. Cite a fonte quando possível."
    )

    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = _client.chat.completions.create(
        model=settings.chat_model,
        messages=messages,
        tools=TOOLS,
        temperature=0.2,
        max_tokens=600,
    )

    message = response.choices[0].message

    if message.tool_calls:
        # O modelo pediu para chamar uma ou mais tools antes de responder.
        # Executamos localmente e devolvemos o resultado como mensagens de
        # role "tool", depois pedimos a resposta final com esse resultado
        # já disponível.
        messages.append(message)

        for tool_call in message.tool_calls:
            fn = AVAILABLE_TOOLS.get(tool_call.function.name)
            result = fn() if fn else []
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

        follow_up = _client.chat.completions.create(
            model=settings.chat_model,
            messages=messages,
            temperature=0.2,
            max_tokens=600,
        )
        return follow_up.choices[0].message.content

    return message.content
