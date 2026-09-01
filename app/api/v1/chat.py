from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.rag.pipeline import run_rag_pipeline

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = run_rag_pipeline(request.question, department=request.department)
    return ChatResponse(**result)
