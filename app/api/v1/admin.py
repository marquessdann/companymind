from fastapi import APIRouter, Depends

from app.schemas.documents import DocumentIngestRequest, DocumentIngestResponse
from app.security.auth import require_admin_key
from app.services.chunking import chunk_text
from app.services.embeddings import generate_embeddings_batch
from app.repositories.documents_repository import insert_document, insert_chunks

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("/documents", response_model=DocumentIngestResponse)
def ingest_document(request: DocumentIngestRequest) -> DocumentIngestResponse:
    document_id = insert_document(request.title, request.category, request.department)

    chunks = chunk_text(request.content)
    embeddings = generate_embeddings_batch(chunks)
    created = insert_chunks(document_id, chunks, embeddings)

    return DocumentIngestResponse(
        document_id=document_id,
        chunks_created=created,
        status="completed",
    )
