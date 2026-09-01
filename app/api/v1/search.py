from fastapi import APIRouter

from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.embeddings import generate_embedding
from app.repositories.documents_repository import match_chunks

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    embedding = generate_embedding(request.query)
    chunks = match_chunks(embedding, top_k=request.top_k)

    results = [
        SearchResult(
            document_id=c["document_id"],
            document_title=c["document_title"],
            chunk_content=c["content"],
            similarity=c["similarity"],
        )
        for c in chunks
    ]

    return SearchResponse(results=results, total_found=len(results))
