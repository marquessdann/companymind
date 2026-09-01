from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    department: str | None = Field(default=None, description="Filtro opcional por departamento")


class RetrievedChunk(BaseModel):
    document_id: str
    document_title: str
    content: str
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[RetrievedChunk]
    has_sufficient_context: bool
    model_used: str
    response_time_ms: int
