import pytest


@pytest.fixture
def sample_chunks():
    return [
        {
            "episode": "Building Products People Love",
            "guest": "Jane Doe",
            "timestamp": "chunk 1/3",
            "text": "The best growth loops start with a single retained habit, not a viral mechanic.",
            "score": 0.82,
        },
        {
            "episode": "Building Products People Love",
            "guest": "Jane Doe",
            "timestamp": "chunk 2/3",
            "text": "We saw 3x activation after moving onboarding from a form to an interactive checklist.",
            "score": 0.77,
        },
    ]
