from unittest.mock import patch

from app.rag.pipeline import run_rag_pipeline
from config.ai_policy import RESPONSE_WHEN_NO_CONTEXT


@patch("app.rag.pipeline.log_query")
@patch("app.rag.pipeline.match_chunks")
@patch("app.rag.pipeline.generate_embedding")
def test_pipeline_returns_no_context_message_when_nothing_found(
    mock_embedding, mock_match, mock_log
):
    mock_embedding.return_value = [0.0] * 1536
    mock_match.return_value = []

    result = run_rag_pipeline("Qual a política de home office em Marte?")

    assert result["has_sufficient_context"] is False
    assert result["answer"] == RESPONSE_WHEN_NO_CONTEXT
    assert result["sources"] == []


@patch("app.rag.pipeline.log_query")
@patch("app.rag.pipeline.ask_llm")
@patch("app.rag.pipeline.match_chunks")
@patch("app.rag.pipeline.generate_embedding")
def test_pipeline_uses_retrieved_chunks(mock_embedding, mock_match, mock_ask_llm, mock_log):
    mock_embedding.return_value = [0.0] * 1536
    mock_match.return_value = [
        {
            "document_id": "abc-123",
            "document_title": "Política de Férias",
            "content": "30 dias corridos por ano.",
            "similarity": 0.91,
        }
    ]
    mock_ask_llm.return_value = "Você tem direito a 30 dias corridos de férias por ano."

    result = run_rag_pipeline("Qual é a política de férias?")

    assert result["has_sufficient_context"] is True
    assert len(result["sources"]) == 1
    assert result["sources"][0]["document_title"] == "Política de Férias"
    mock_ask_llm.assert_called_once()
