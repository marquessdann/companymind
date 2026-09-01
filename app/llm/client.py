from openai import OpenAI

from app.core.config import get_settings
from config.ai_policy import SYSTEM_PROMPT, RESPONSE_WHEN_NO_CONTEXT

settings = get_settings()
_client = OpenAI(api_key=settings.openai_api_key)


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

    response = _client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=600,
    )

    return response.choices[0].message.content
