"""
Artifact generation skill + lightweight extraction of <artifact> blocks from
model output, plus a defense-in-depth HTML pre-check before it ever reaches
the frontend sandbox (frontend still sanitizes independently - see design.md).
"""
import re

ARTIFACT_SYSTEM_SUFFIX = """
When the user asks you to produce a document, report, or rendered snippet, wrap it in:
<artifact type="markdown" title="...">...</artifact>
or
<artifact type="html" title="...">...</artifact>

HTML artifacts must be a single self-contained fragment (inline <style> allowed, no external \
scripts/resources, no <script> tags that make network requests). Only emit ONE artifact block per \
response, after your normal reply text.
"""

_ARTIFACT_RE = re.compile(
    r'<artifact type="(?P<type>markdown|html)" title="(?P<title>[^"]*)">(?P<body>.*?)</artifact>',
    re.DOTALL,
)

# Extremely conservative denylist as a first-line filter; the real isolation
# boundary is the sandboxed iframe (no allow-same-origin) + DOMPurify on the frontend.
_BLOCKED_PATTERNS = [
    re.compile(r"<script[^>]*\bsrc=", re.IGNORECASE),
    re.compile(r"fetch\s*\(", re.IGNORECASE),
    re.compile(r"XMLHttpRequest", re.IGNORECASE),
    re.compile(r"document\.cookie", re.IGNORECASE),
]


def extract_artifact(full_text: str) -> tuple[str, dict | None]:
    """Split model output into (reply_text, artifact_dict_or_none)."""
    match = _ARTIFACT_RE.search(full_text)
    if not match:
        return full_text.strip(), None

    reply_text = (full_text[: match.start()] + full_text[match.end():]).strip()
    artifact = {
        "artifact_type": match.group("type"),
        "title": match.group("title") or "Untitled artifact",
        "content": match.group("body").strip(),
    }

    if artifact["artifact_type"] == "html":
        for pattern in _BLOCKED_PATTERNS:
            if pattern.search(artifact["content"]):
                artifact["content"] = (
                    "<p><strong>Artifact blocked:</strong> generated HTML contained a "
                    "disallowed pattern (network call, cookie access, or remote script) "
                    "and was withheld for safety.</p>"
                )
                break

    return reply_text, artifact
