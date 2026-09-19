# Session log: Initial project scaffolding (Claude, chat)

**Goal:** Stand up the full project per the assignment brief — FastAPI backend, Next.js
frontend, RAG pipeline, dual LLM provider, Ship 30 skill, sandboxed artifact viewer, docs,
tests — from the assignment PDF and a reference implementation guide.

**Approach:**
1. Scaffolded the directory structure (`backend/`, `frontend/`, `docs/`, `agent_transcripts/`).
2. Wrote `Settings` (pydantic-settings) as the single source of runtime configuration, so the
   local/cloud model toggle and DB connection are both environment-driven with no code changes.
3. Modeled `sessions` / `messages` / `artifacts` / `transcript_chunks` with SQLAlchemy 2.0 async
   ORM + pgvector's `Vector` column type.
4. Wrote `BaseLLMProvider` as an abstract async-generator interface before writing either
   concrete provider, so `OllamaProvider` and `AnthropicProvider` were forced to share one call
   signature — this made the provider-toggle requirement trivial to satisfy later.
5. Wrote the grounded-QA and Ship 30 for 30 skills as separate system-prompt modules sharing the
   same retrieval plumbing, and an artifact extractor with a first-line HTML safety denylist
   ahead of the frontend's sandboxed iframe.
6. Wrote the Next.js frontend: two-pane layout (chat + artifact viewer), `DOMPurify` +
   `sandbox="allow-scripts"` (no `allow-same-origin`) for untrusted HTML artifacts.

**Verification at the time:** every backend Python file was syntax-checked (`py_compile`) and the
dependency-free logic (chunking, prompt construction, artifact extraction) was smoke-tested
directly in the sandbox — all passed. Nothing had been run against a real Postgres or Ollama
instance yet, since that sandbox had neither available.

**Outcome:** a complete, internally consistent scaffold, packaged as a zip for the user to run
locally on their own Windows machine. Everything downstream in this log (02, 03, 04) is what
broke, and how it got fixed, once the project actually had to run outside that sandbox.
