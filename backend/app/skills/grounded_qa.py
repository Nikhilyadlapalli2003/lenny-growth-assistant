"""
Grounded conversational QA skill: retrieves relevant transcript chunks and
builds a system prompt that forces citation and an honest "I don't know".
"""
GROUNDED_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an internal tool that answers \
product management and growth questions using ONLY the provided Lenny's Podcast transcript excerpts.

Rules:
1. Ground every claim in the provided context. Cite the source inline as \
[Episode: <episode title>, Guest: <guest name>] immediately after the claim.
2. If the context does not contain enough information to answer, say plainly: \
"I don't have sufficient information in Lenny's podcast archive to answer this." \
Do not guess or use outside knowledge.
3. Preserve conversation context across follow-up questions.
4. Be concise and actionable - this is for working PMs and growth leads, not a lecture.

Context excerpts:
{context}
"""


def build_grounded_prompt(chunks: list[dict]) -> str:
    if not chunks:
        formatted = "(No relevant transcript excerpts were found for this query.)"
    else:
        formatted = "\n\n".join(
            f"--- {c['episode']} (Guest: {c.get('guest') or 'Unknown'}, "
            f"{c.get('timestamp') or 'n/a'}) ---\n{c['text']}"
            for c in chunks
        )
    return GROUNDED_SYSTEM_PROMPT.format(context=formatted)
