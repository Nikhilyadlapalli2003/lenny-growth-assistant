from app.rag.chunking import chunk_transcript


def test_chunk_transcript_produces_nonempty_chunks():
    text = "\n\n".join([f"Paragraph {i}. " * 40 for i in range(10)])
    chunks = chunk_transcript(text, target_tokens=200, overlap_tokens=50)
    assert len(chunks) > 1
    assert all(c.strip() for c in chunks)


def test_chunk_transcript_handles_empty_input():
    assert chunk_transcript("", target_tokens=200, overlap_tokens=50) == []


def test_chunk_transcript_handles_short_input():
    chunks = chunk_transcript("A single short paragraph.", target_tokens=200, overlap_tokens=50)
    assert len(chunks) == 1
