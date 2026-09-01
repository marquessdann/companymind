import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest
from app.schemas.search import SearchRequest


def test_chat_request_rejects_short_question():
    with pytest.raises(ValidationError):
        ChatRequest(question="oi")


def test_chat_request_accepts_valid_question():
    req = ChatRequest(question="Qual é a política de férias?")
    assert req.department is None


def test_search_request_top_k_bounds():
    with pytest.raises(ValidationError):
        SearchRequest(query="ferias", top_k=100)
