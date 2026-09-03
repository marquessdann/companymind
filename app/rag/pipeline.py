import time

from app.services.embeddings import generate_embedding
from app.repositories.documents_repository import match_chunks
from app.security.prompt_injection import sanitize_chunks
from app.llm.client import ask_llm
from app.services.query_logs import log_query
from app.core.config import get_settings
from config.ai_policy import RESPONSE_WHEN_NO_CONTEXT

settings = get_settings()


def run_rag_pipeline(question: str, department: str | None = None) -> dict:
    start = time.perf_counter()

    query_embedding = generate_embedding(question)
    raw_chunks = match_chunks(query_embedding, department=department)
    chunks = sanitize_chunks(raw_chunks)

    has_context = len(chunks) > 0
    answer = ask_llm(question, chunks) if has_context else RESPONSE_WHEN_NO_CONTEXT

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    log_query(
        question=question,
        answer=answer,
        retrieved_count=len(chunks),
        top_similarity=chunks[0]["similarity"] if chunks else None,
        response_time_ms=elapsed_ms,
        had_error=False,
    )

    return {
        "answer": answer,
        "sources": [
            {
                "document_id": c["document_id"],
                "document_title": c["document_title"],
                "content": c["content"],
                "similarity": c["similarity"],
            }
            for c in chunks
        ],
        "has_sufficient_context": has_context,
        "model": settings.chat_model,
        "response_time_ms": elapsed_ms,
    }
