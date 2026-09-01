from app.database.supabase_client import get_supabase


def log_query(
    question: str,
    answer: str,
    retrieved_count: int,
    top_similarity: float | None,
    response_time_ms: int,
    had_error: bool,
) -> None:
    supabase = get_supabase()
    supabase.table("query_logs").insert(
        {
            "question": question,
            "answer": answer,
            "retrieved_chunks_count": retrieved_count,
            "top_similarity": top_similarity,
            "response_time_ms": response_time_ms,
            "had_error": had_error,
        }
    ).execute()


def get_metrics_summary() -> dict:
    supabase = get_supabase()
    result = supabase.table("query_logs").select("*").execute()
    logs = result.data or []

    if not logs:
        return {
            "total_queries": 0,
            "avg_response_time_ms": 0,
            "queries_with_no_context": 0,
            "error_rate": 0.0,
        }

    total = len(logs)
    avg_time = sum(l["response_time_ms"] for l in logs) / total
    no_context = sum(1 for l in logs if l["retrieved_chunks_count"] == 0)
    errors = sum(1 for l in logs if l["had_error"])

    return {
        "total_queries": total,
        "avg_response_time_ms": round(avg_time, 2),
        "queries_with_no_context": no_context,
        "error_rate": round(errors / total, 4),
    }
