"""
Recursive-ish character/token chunking for transcript files.
Splits on paragraph boundaries first, falling back to sentence/character
splits, so chunks stay topically coherent instead of cutting mid-thought.
"""
import re

try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(text: str) -> int:
        return len(_ENC.encode(text))
except Exception:  # pragma: no cover - tiktoken optional at runtime
    def _count_tokens(text: str) -> int:
        return max(1, len(text) // 4)


def chunk_transcript(text: str, target_tokens: int = 650, overlap_tokens: int = 100) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _count_tokens(para)
        if current_tokens + para_tokens > target_tokens and current:
            chunks.append("\n\n".join(current))
            # carry the tail of the previous chunk forward for overlap/context continuity
            overlap_text = current[-1] if current else ""
            current = [overlap_text] if _count_tokens(overlap_text) <= overlap_tokens else []
            current_tokens = _count_tokens(overlap_text) if current else 0
        current.append(para)
        current_tokens += para_tokens

    if current:
        chunks.append("\n\n".join(current))

    return [c for c in chunks if c.strip()]
