# The Lenny Growth Assistant

A grounded conversational assistant over Lenny's Podcast transcripts: ask product/growth
questions, get cited answers, turn them into Ship 30 for 30–style essays, and generate
Markdown/HTML artifacts rendered in-app.

See also: [`docs/PRD.md`](docs/PRD.md), [`docs/architecture.md`](docs/architecture.md),
[`docs/design.md`](docs/design.md), [`agent_transcripts/`](agent_transcripts/).

## Architecture overview

```
frontend (Next.js, :3000)  ─▶  backend (FastAPI, :8000)  ─▶  Postgres + pgvector (:5432)
                                        │
                                        ├── OllamaProvider  → local Ollama daemon (:11434, on host)
                                        └── AnthropicProvider → Anthropic API (cloud, optional)
```

Full detail in `docs/architecture.md`.

## Prerequisites

- Docker & Docker Compose v24+
- [Ollama](https://ollama.com) installed **on your host machine** (not containerized — see note below)
- Node.js 20 LTS and Python 3.11 only if you want to run services outside Docker

## Quickstart (one command)

```bash
# 1. Pull the local model the demo will use
ollama pull llama3.1:8b
ollama serve   # if not already running as a background service

# 2. Configure environment
cp .env.example .env
# (defaults work out of the box for local Docker Compose)

# 3. Start everything
docker compose up --build

# 4. Ingest transcripts (one-time, or whenever the corpus changes)
docker compose exec backend python scripts/download_transcripts.py --source-dir /app/data/sample_transcripts --copy-only
docker compose exec backend python scripts/ingest.py
```

Then open **http://localhost:3000**.

> **Why Ollama isn't in docker-compose.yml:** the assignment requires the demo to exercise a real
> local model on your machine. The backend reaches it via `host.docker.internal:11434`. To
> containerize Ollama instead, add:
> ```yaml
>   ollama:
>     image: ollama/ollama
>     ports: ["11434:11434"]
>     volumes: ["ollama_data:/root/.ollama"]
> ```
> and point `OLLAMA_BASE_URL=http://ollama:11434`.

## Environment variables

See `.env.example` for the full list with defaults. Required for the local demo: nothing beyond the
defaults. Optional: `ANTHROPIC_API_KEY` to enable the cloud provider toggle — leave blank to run
100% local.

## Running without Docker (local dev)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Ingesting your own transcripts

Drop `.txt` or `.md` files into `backend/data/raw/`, named `episode-title__guest-name.md`, then:

```bash
python backend/scripts/ingest.py
```

Re-running ingestion for an already-ingested episode title replaces its chunks (safe refresh).

## Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

Covers: chunking edge cases, skill prompt construction, artifact extraction + HTML safety
filtering, provider factory routing, and API contract validation (422s, route wiring).

### Manual test plan (UI)
1. Start a new session → confirm a session ID is created and persists across a page reload.
2. Ask a question clearly covered by an ingested transcript → confirm citations appear and match a
   real episode.
3. Ask an out-of-domain question (e.g., "what's the capital of France?") → confirm the assistant
   states it doesn't have that information rather than answering from general knowledge.
4. Click "Ship 30 essay" on a covered topic → confirm ~1,000–1,500 words, headers, bullets.
5. Ask the assistant to "turn that into a one-page HTML summary" → confirm the artifact viewer opens
   on the right and renders inside the sandboxed iframe.
6. In browser devtools, confirm the artifact iframe has no `allow-same-origin` in its `sandbox`
   attribute and that `iframe.contentWindow.document.cookie` throws/is inaccessible from the parent.
7. Switch the model dropdown to "Claude (cloud)" without an API key set → confirm a clear
   configuration error message, not a crash.
8. Stop Ollama (`docker compose stop` is N/A since it's host-run — just `ollama` process kill) and
   send a message → confirm `/api/health` reports `ollama: false` and chat returns a helpful error.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Ollama error` in chat replies | `ollama serve` not running, or model not pulled | `ollama serve` + `ollama pull llama3.1:8b` |
| Backend can't reach Postgres on startup | `db` healthcheck not yet passed | Wait for `db` container to report healthy, or check `DATABASE_URL` |
| `/api/health` shows `vector_index: false` | `ingest.py` hasn't been run yet | Run the ingestion steps above |
| Frontend shows CORS errors | `CORS_ALLOW_ORIGINS` doesn't match frontend origin | Update `.env` and restart `backend` |
| Anthropic provider returns a config error | `ANTHROPIC_API_KEY` unset | Set it in `.env`, or stay on `ollama` |

## Next steps (documented, not built)
- True token-by-token SSE streaming to the frontend (backend already streams internally).
- HNSW index creation + periodic `VACUUM ANALYZE` guidance for `transcript_chunks` at scale.
- A real transcript-scraping job behind `download_transcripts.py`.
- Reranking pass on top of vector similarity for higher precision at larger corpus sizes.
