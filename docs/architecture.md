# Architecture — The Lenny Growth Assistant

## 1. System overview

```
┌─────────────┐      REST/JSON        ┌───────────────┐        SQL/pgvector      ┌──────────────┐
│  Frontend   │ ───────────────────▶ │   FastAPI      │ ───────────────────────▶ │  PostgreSQL  │
│  (Next.js)  │ ◀─────────────────── │   Backend      │ ◀─────────────────────── │  + pgvector  │
└─────────────┘   streamed tokens     └───────┬────────┘                          └──────────────┘
                                               │
                                   ┌───────────┴───────────┐
                                   ▼                        ▼
                           ┌───────────────┐        ┌───────────────┐
                           │ OllamaProvider │        │AnthropicProvider│
                           │ (local, req'd) │        │ (cloud, optional)│
                           └───────────────┘        └───────────────┘
```

## 2. Database schema

- **sessions**(`id` UUID PK, `title`, `provider`, `user_metadata` JSONB, `created_at`, `updated_at`)
- **messages**(`id` UUID PK, `session_id` FK→sessions, `role`, `content`, `sources` JSONB,
  `provider_used`, `created_at`)
- **artifacts**(`id` UUID PK, `message_id` FK→messages, `artifact_type` [markdown|html], `title`,
  `content`, `created_at`)
- **transcript_chunks**(`id` UUID PK, `episode_title`, `guest_name`, `episode_url`, `timestamp_ref`,
  `chunk_index`, `chunk_text`, `embedding` VECTOR(384), `created_at`) — HNSW-indexable via pgvector
  (`CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)` recommended once corpus grows beyond a
  few thousand chunks; cosine `<=>` operator used at query time either way).

`sources` on `messages` is a denormalized JSON snapshot of the citations shown for that answer, so
history replay doesn't require re-running retrieval.

## 3. API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/sessions` | Create a session (optional title/provider) |
| GET | `/api/sessions` | List sessions, newest first |
| GET | `/api/sessions/{id}` | Fetch a session + full message history |
| POST | `/api/chat` | Send a message; retrieves context, routes to a skill, streams from the selected provider, persists message + artifact |
| GET | `/api/artifacts/{id}` | Fetch a generated artifact for the viewer |
| GET | `/api/health` | Reports DB connectivity, Ollama reachability, vector index presence, active default provider |

Errors follow a consistent `{ "error": str, "detail": str }` JSON shape via a global FastAPI
exception handler; validation errors use FastAPI/Pydantic's built-in 422 contract.

## 4. Ingestion / retrieval flow

1. `scripts/download_transcripts.py` copies source transcript files into `backend/data/raw/`
   (swap in real scraping/API calls here without touching downstream code).
2. `scripts/ingest.py`:
   - Parses episode title/guest from filename convention `title__guest.md`.
   - Chunks text paragraph-aware, targeting ~650 tokens with ~100-token overlap
     (`app/rag/chunking.py`).
   - Embeds chunks locally via `sentence-transformers/all-MiniLM-L6-v2` (`app/rag/embeddings.py`) —
     no network dependency, works fully offline.
   - Upserts into `transcript_chunks`, deleting any prior rows for that episode title first (safe to
     re-run for content refreshes).
3. At query time, `TranscriptRetriever` embeds the user's message, runs a cosine-similarity query
   with a similarity floor (`RETRIEVAL_SIMILARITY_THRESHOLD`), and returns the top-K chunks with
   episode/guest/timestamp metadata for citation.

## 5. Agent routing / skill boundaries

Two independent "skills" share the same retrieval + provider plumbing but use different system
prompts, kept in separate modules so they can evolve independently:

- `app/skills/grounded_qa.py` — default conversational QA. Forces inline citation syntax and an
  explicit refusal phrase when context is insufficient.
- `app/skills/ship30_writer.py` — content-generation skill. Encodes the Ship 30 for 30 structural
  rules (hook, ~1,250 words, skimmable formatting, grounded claims, concrete takeaway) as an
  explicit prompt contract rather than an unstructured one-off instruction.
- `app/skills/artifact_generator.py` — cross-cutting: appended to either skill's prompt when the
  user wants a renderable document; parses the model's `<artifact>` block out of the reply and
  applies a first-line safety filter before persistence.

`ChatRequest.mode` (`default` | `ship30`) is the routing signal from the frontend; `app/api/chat.py`
selects the system prompt accordingly, keeping routing logic in one place.

## 6. Model toggle

`app/providers/factory.py` resolves the active provider per request, in priority order:
`ChatRequest.provider` (explicit UI choice) → `X-LLM-Provider` header → session's stored default →
`DEFAULT_LLM_PROVIDER` env var. Both `OllamaProvider` and `AnthropicProvider` implement the same
`BaseLLMProvider.generate()` async-generator interface, so the rest of the app never branches on
provider identity. Provider failures (connection refused, missing API key, timeout) yield a
user-facing explanatory string instead of raising — the chat still completes with the sources it
retrieved and a clear "here's what went wrong" message.

## 7. Security

**Artifact rendering is the primary untrusted-content boundary.** Defense in depth:
1. Backend: `extract_artifact()` regex-denylists obvious exfiltration patterns (remote `<script src>`,
   `fetch(`, `XMLHttpRequest`, `document.cookie`) in HTML artifacts before they're ever persisted.
2. Frontend: `DOMPurify.sanitize()` strips dangerous tags/attributes a second time.
3. Rendering: the sanitized HTML is mounted via `<iframe sandbox="allow-scripts" srcDoc={...}>` with
   **`allow-same-origin` deliberately omitted** — the iframe gets an opaque, unique origin per render,
   so even a script that survives both filters cannot read the parent page's cookies, `localStorage`,
   or DOM, and cannot make same-origin-credentialed requests back to the API.
4. What's explicitly **not** attempted: full CSP-based iframe policy, server-side headless-browser
   re-rendering, or WASM sandboxing — judged out of scope for this exercise, documented as a next
   step for a production deployment.

Markdown artifacts are rendered via `react-markdown` (no `dangerouslySetInnerHTML`), which is
XSS-safe by construction for standard Markdown syntax.

## 8. Deployment topology

`docker-compose.yml` runs three services: `db` (Postgres 16 + pgvector image), `backend` (FastAPI,
depends on `db` health check), `frontend` (Next.js, depends on `backend`). Ollama itself runs on the
host (not containerized) and is reached via `host.docker.internal`, since the assignment requires it
to be "run on your machine" for the demo — containerizing it is a one-line addition
(`ollama/ollama` image) documented in README.md as an optional profile.
