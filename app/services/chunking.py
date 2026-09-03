from app.core.config import get_settings

settings = get_settings()


def clean_text(text: str) -> str:
    return " ".join(text.split())


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    if overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap deve ser menor que chunk_size, ou o corte nunca avança "
            f"(recebido chunk_size={chunk_size}, overlap={overlap})."
        )

    text = clean_text(text)

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
