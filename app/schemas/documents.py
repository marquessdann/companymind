from datetime import datetime
from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    title: str
    category: str
    department: str | None
    created_at: datetime


class DocumentIngestRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: str = Field(..., description="policy | procedure | product | faq | general")
    department: str | None = None
    content: str = Field(..., min_length=20)


class DocumentIngestResponse(BaseModel):
    document_id: str
    chunks_created: int
    status: str
