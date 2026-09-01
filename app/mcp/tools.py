"""
Definição das ferramentas de leitura da base de conhecimento.

Este módulo é a fonte única de verdade das "tools" do CompanyMind: as mesmas
funções são reaproveitadas tanto pelo tool calling do LLM (app/rag) quanto
pelo MCP Server (app/mcp/server.py), evitando duas implementações divergentes
da mesma regra de negócio.
"""

from app.services.embeddings import generate_embedding
from app.repositories.documents_repository import match_chunks
from app.database.supabase_client import get_supabase


def search_company_knowledge(query: str, top_k: int = 5) -> list[dict]:
    embedding = generate_embedding(query)
    return match_chunks(embedding, top_k=top_k)


def get_company_policy(topic: str) -> list[dict]:
    embedding = generate_embedding(topic)
    results = match_chunks(embedding, top_k=3)

    return [
        result
        for result in results
        if "policy" in result.get("document_title", "").lower()
    ]


def get_product_information(product_query: str) -> list[dict]:
    embedding = generate_embedding(product_query)
    return match_chunks(embedding, top_k=3)


def list_company_departments() -> list[str]:
    supabase = get_supabase()
    result = supabase.table("documents").select("department").execute()
    departments = {row["department"] for row in (result.data or []) if row["department"]}
    return sorted(departments)


def search_faq(question: str) -> list[dict]:
    embedding = generate_embedding(question)
    return match_chunks(embedding, top_k=3)
