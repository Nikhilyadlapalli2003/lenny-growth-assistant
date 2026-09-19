# Session: Initial project scaffolding

**Goal:** Stand up the FastAPI backend skeleton (config, DB models, provider interface) and the
Next.js frontend skeleton (layout, API client) matching the architecture in `docs/architecture.md`.

**Approach:**
1. Defined `Settings` (pydantic-settings) as the single source of runtime configuration, so the
   local/cloud model toggle and DB connection are both environment-driven with no code changes.
2. Modeled `sessions` / `messages` / `artifacts` / `transcript_chunks` with SQLAlchemy 2.0 async
   ORM + pgvector's `Vector` column type.
3. Wrote `BaseLLMProvider` as an abstract async-generator interface before writing either concrete
   provider, so `OllamaProvider` and `AnthropicProvider` were forced to share one call signature.

**Outcome:** Backend imports and syntax-checked cleanly (`python -m py_compile`) on first pass for
config/database/schemas; provider implementations required one correction (see next log).
