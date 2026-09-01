from openai import OpenAI

from app.core.config import get_settings

_settings = get_settings()
_client = OpenAI(api_key=_settings.openai_api_key)


def generate_embedding(text: str) -> list[float]:
    response = _client.embeddings.create(
        model=_settings.embedding_model,
        input=text.replace("\n", " "),
    )
    return response.data[0].embedding


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    cleaned = [t.replace("\n", " ") for t in texts]
    response = _client.embeddings.create(
        model=_settings.embedding_model,
        input=cleaned,
    )
    return [item.embedding for item in response.data]
