from app.database.supabase_client import get_supabase
from app.core.config import get_settings

settings = get_settings()


def insert_document(title: str, category: str, department: str | None) -> str:
    supabase = get_supabase()
    result = (
        supabase.table("documents")
        .insert({"title": title, "category": category, "department": department})
        .execute()
    )
    return result.data[0]["id"]


def insert_chunks(document_id: str, chunks: list[str], embeddings: list[list[float]]) -> int:
    supabase = get_supabase()
    rows = [
        {"document_id": document_id, "content": chunk, "embedding": embedding}
        for chunk, embedding in zip(chunks, embeddings)
    ]
    supabase.table("document_chunks").insert(rows).execute()
    return len(rows)


def match_chunks(
    query_embedding: list[float],
    top_k: int | None = None,
    department: str | None = None,
) -> list[dict]:
    """Chama a função SQL match_document_chunks (definida em sql/schema.sql),
    que executa a busca por similaridade de cosseno usando pgvector."""
    supabase = get_supabase()
    top_k = top_k or settings.retrieval_top_k

    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_threshold": settings.similarity_threshold,
            "match_count": top_k,
            "filter_department": department,
        },
    ).execute()

    return response.data or []


def list_documents() -> list[dict]:
    supabase = get_supabase()
    result = supabase.table("documents").select("*").order("created_at", desc=True).execute()
    return result.data or []
