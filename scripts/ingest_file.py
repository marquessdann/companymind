"""
Ingestão de um arquivo local (TXT, MD ou PDF) para a base de conhecimento.

Uso:
    python scripts/ingest_file.py caminho/arquivo.pdf "Título" policy RH
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pypdf import PdfReader

from app.services.chunking import chunk_text
from app.services.embeddings import generate_embeddings_batch
from app.repositories.documents_repository import insert_document, insert_chunks


def extract_text(path: str) -> str:
    if path.endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> None:
    if len(sys.argv) < 4:
        print("Uso: python scripts/ingest_file.py <arquivo> <titulo> <categoria> [departamento]")
        sys.exit(1)

    path, title, category = sys.argv[1], sys.argv[2], sys.argv[3]
    department = sys.argv[4] if len(sys.argv) > 4 else None

    raw_text = extract_text(path)
    document_id = insert_document(title, category, department)

    chunks = chunk_text(raw_text)
    embeddings = generate_embeddings_batch(chunks)
    created = insert_chunks(document_id, chunks, embeddings)

    print(f"Documento '{title}' ingerido com {created} chunk(s). ID: {document_id}")


if __name__ == "__main__":
    main()
