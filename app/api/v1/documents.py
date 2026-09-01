from fastapi import APIRouter

from app.schemas.documents import DocumentOut
from app.repositories.documents_repository import list_documents

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.get("/documents", response_model=list[DocumentOut])
def get_documents() -> list[DocumentOut]:
    return list_documents()
