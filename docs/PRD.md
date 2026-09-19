# PRD — The Lenny Growth Assistant

## 1. Forward Deployment Brief

### User and problem
**Primary user:** A product manager or growth lead inside a company that has licensed/curated a set
of Lenny's Podcast transcripts as an internal knowledge base. They want tactical, source-grounded
answers to questions like "how do other PMs structure activation experiments?" without listening to
hours of audio or trusting an ungrounded chatbot that hallucinates frameworks.

**Job to be done:** "Turn 100+ hours of podcast knowledge into a 30-second, trustworthy answer I can
act on or share with my team — with a citation I can go verify."

**Pain removed:** Manual transcript search, uncredited paraphrasing, and the risk of repeating
made-up advice to stakeholders.

### Success metrics
1. **Retrieval groundedness:** ≥ 90% of assistant answers that make a substantive claim include at
   least one valid `[Episode: ..., Guest: ...]` citation traceable to a real ingested chunk.
2. **Local inference latency:** < 4s to first streamed token on the required local Ollama demo
   (8B-class model, consumer hardware).
3. **Artifact render safety:** 0 successful script-based escapes from the sandboxed artifact iframe
   across the manual security test plan (see README.md).
4. **Operational metric:** A new team member can run the full stack end-to-end (`docker compose up`)
   in under 15 minutes using only the README.

### Assumptions
- The transcript corpus is provided as plain-text/Markdown files (one per episode); no scraping of
  Lenny's Newsletter site is performed as part of this submission — ingestion assumes files are
  already exported, consistent with typical publicly available transcript archives.
- "Users" in this exercise means a single internal team, not a multi-tenant SaaS — no per-org
  isolation was built.
- Local embedding (`sentence-transformers/all-MiniLM-L6-v2`) is acceptable for retrieval quality at
  this scale; a hosted embedding API was not required to satisfy "runs locally."
- The Ship 30 for 30 "skill" is implemented as a dedicated, reusable system prompt + word-count/
  formatting contract rather than a fine-tuned model, per the assignment's allowance for
  "skill or tool."
- Claude Agent SDK / Pi Coding Agent orchestration is represented here as a clean provider +
  skill-routing abstraction (`app/providers`, `app/skills`) rather than a hard dependency on one
  specific SDK, so the same code path works whether the team standardizes on Claude Agent SDK,
  LangChain, or a bare API client later.

### Scope choices
**Included:** session-scoped chat with persistence, dual-provider (Ollama/Anthropic) toggle,
pgvector-backed grounded retrieval, Ship 30 for 30 essay skill, artifact generation + sandboxed
in-app viewer, health/observability endpoint, Docker Compose one-command startup, automated tests.

**Excluded (and why):**
- Authentication/multi-user accounts — out of scope for a single-team internal tool evaluation;
  `user_metadata` JSON field on sessions is a placeholder for future SSO integration.
- Transcript scraping/crawling automation — ingestion assumes files are supplied; a
  `download_transcripts.py` script exists as the seam where that would plug in.
- Fine-tuned or hosted reranking model — cosine similarity via pgvector HNSW is judged sufficient
  at this corpus size; reranking is a documented future improvement.
- Real-time collaborative sessions (multiple users in one chat) — not requested by the brief.

### Risks and trade-offs
| Risk | Mitigation |
|---|---|
| Hallucination when retrieval is weak | Similarity threshold gate + explicit "I don't have sufficient information" instruction in the system prompt |
| Local model (7-8B) reasoning/formatting quality vs. cloud | Provider toggle lets evaluator compare; Ship 30 skill prompt is deliberately structured/constrained to reduce reliance on model reasoning depth |
| Latency of local inference | Streaming response (token-by-token) instead of blocking; configurable timeout with a clear error message |
| Unsafe artifact rendering (XSS) | Sandboxed iframe with `allow-scripts` but **no** `allow-same-origin` (opaque origin — cannot read parent cookies/storage) + DOMPurify sanitization + backend-side denylist for obvious exfiltration patterns (see architecture.md §Security) |
| Data leakage across sessions | Each session is a separate DB row scoped by `session_id`; chat history for the LLM call is filtered to that session only |
| Ollama unavailable at demo time | `/api/health` reports Ollama status distinctly; provider errors return a user-facing message instead of a raw stack trace |

## 2. Flows
1. User opens app → frontend creates a session (`POST /api/sessions`) → session ID stored client-side.
2. User sends a question → backend embeds the query → retrieves top-K chunks from `transcript_chunks`
   → builds grounded system prompt → streams from selected provider → persists message + citations.
3. User clicks "Ship 30 essay" → same flow, but routed through the Ship 30 skill prompt instead of
   the default QA prompt.
4. If the model emits an `<artifact>` block, the backend extracts and stores it separately; the
   frontend shows a "View generated artifact" link that opens the right-pane viewer.

## 3. Acceptance criteria
- [ ] A new session persists across a page reload (session ID in local state; history fetchable via
      `GET /api/sessions/{id}`).
- [ ] Switching the provider dropdown changes `provider_used` in the next response.
- [ ] A question with no matching transcript content returns the "insufficient information" message,
      not a fabricated answer.
- [ ] Ship 30 output is Markdown, includes headers/bullets, and is within roughly 1,000–1,500 words.
- [ ] Generated HTML artifacts render inside the sandboxed iframe and cannot access
      `document.cookie` or `localStorage` of the parent page.
- [ ] `docker compose up` brings up db + backend + frontend with no manual steps beyond providing
      `.env` and pulling an Ollama model.

## 4. Implementation plan
1. Data layer (Postgres + pgvector models) → 2. Ingestion pipeline → 3. Provider abstraction →
4. Retrieval + grounded QA skill → 5. Ship 30 skill → 6. Artifact extraction/safety layer →
7. FastAPI routes + persistence → 8. Frontend chat + artifact viewer → 9. Docker Compose +
docs → 10. Tests + manual security pass.
