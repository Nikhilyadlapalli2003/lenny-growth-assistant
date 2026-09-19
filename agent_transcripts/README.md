# Agent Transcripts

Real session logs from building and getting this project running, per the assignment's
requirement to include coding-agent transcripts (successes and corrected mistakes), secrets
removed.

- `01_initial_scaffolding.md` — the initial build session: project structure, config layer, DB
  models, provider abstraction, skills, frontend, docs.
- `02_windows_environment_setup.md` — the real debugging session that followed once the project
  had to actually run on a Windows machine with no Docker: a corrupted zip, PATH issues with
  Ollama/Docker, a partial Docker Desktop install, pip build failures on Windows (asyncpg/tiktoken
  → psycopg), Supabase IPv6-vs-pooler connectivity, a Windows-specific asyncio event loop bug in
  psycopg, a retrieval threshold tuning fix, and a Next.js critical-CVE dependency bump.

All API keys, database passwords, and other secrets that appeared during the real session were
excluded from these logs.
