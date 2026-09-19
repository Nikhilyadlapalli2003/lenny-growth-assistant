from app.skills.artifact_generator import extract_artifact
from app.skills.grounded_qa import build_grounded_prompt
from app.skills.ship30_writer import build_ship30_prompt


def test_grounded_prompt_includes_context(sample_chunks):
    prompt = build_grounded_prompt(sample_chunks)
    assert "Building Products People Love" in prompt
    assert "I don't have sufficient information" in prompt


def test_grounded_prompt_handles_empty_context():
    prompt = build_grounded_prompt([])
    assert "No relevant transcript excerpts" in prompt


def test_ship30_prompt_targets_word_count(sample_chunks):
    prompt = build_ship30_prompt(sample_chunks)
    assert "1,250 words" in prompt


def test_extract_artifact_splits_markdown_block():
    text = 'Here you go.\n<artifact type="markdown" title="Notes">\n# Hello\n</artifact>'
    reply, artifact = extract_artifact(text)
    assert reply == "Here you go."
    assert artifact["artifact_type"] == "markdown"
    assert artifact["title"] == "Notes"
    assert "# Hello" in artifact["content"]


def test_extract_artifact_returns_none_when_absent():
    reply, artifact = extract_artifact("Just a normal reply, no artifact here.")
    assert artifact is None
    assert reply == "Just a normal reply, no artifact here."


def test_extract_artifact_blocks_unsafe_html():
    unsafe = (
        'Here.\n<artifact type="html" title="Bad">'
        '<script src="https://evil.example/x.js"></script></artifact>'
    )
    _, artifact = extract_artifact(unsafe)
    assert "blocked" in artifact["content"].lower()
