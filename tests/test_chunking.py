from app.services.chunking import chunk_text, clean_text


def test_clean_text_collapses_whitespace():
    assert clean_text("  ola   mundo \n\n") == "ola mundo"


def test_chunk_text_returns_single_chunk_when_short():
    text = "texto curto"
    chunks = chunk_text(text, chunk_size=100, overlap=10)
    assert chunks == [text]


def test_chunk_text_splits_long_text_with_overlap():
    text = "a" * 1000
    chunks = chunk_text(text, chunk_size=300, overlap=50)

    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)
