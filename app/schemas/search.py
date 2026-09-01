from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    document_id: str
    document_title: str
    chunk_content: str
    similarity: float


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total_found: int
