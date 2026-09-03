from fastapi import APIRouter, Depends

from app.schemas.documents import DocumentOut
from app.repositories.documents_repository import list_documents
from app.security.auth import require_admin_key

router = APIRouter(prefix="/api/v1", tags=["documents"])


@router.get(
    "/documents",
    response_model=list[DocumentOut],
    dependencies=[Depends(require_admin_key)],
)
def get_documents() -> list[DocumentOut]:
    return list_documents()
