# Session log: Getting the project running on Windows (Claude, chat)

This log covers the real environment-setup debugging that happened after the user extracted the
project on their own Windows machine — none of this was anticipated by the original scaffolding
session, since it had no Windows/Docker environment to test against.

## Issue 1 — Corrupted zip (stray directory)

**Symptom:** Windows Explorer's built-in extractor refused to open the delivered zip
("The Compressed (zipped) Folder ... is invalid").

**Root cause:** an earlier `mkdir -p` command using brace expansion (`mkdir -p
project/{docs,agent_transcripts,backend/scripts,...}`) silently failed to expand in the shell
that ran it, creating one literal directory named `{docs,agent_transcripts,backend...}` instead
of the intended subdirectories. That directory's name (containing `{`, `}`, `,`) was legal in the
zip format but broke Windows' extractor.

**Fix:** located and deleted the stray directory (`rm -rf "...{docs,agent_transcripts,backend"`),
rebuilt the zip with `zip -r -q -X`, and verified with `unzip -t` before redelivering.

## Issue 2 — Ollama / Docker not on PATH

**Symptom:** `ollama` and later `docker` commands returned `CommandNotFoundException` in
PowerShell immediately after installing each.

**Root cause:** both installers updated the system PATH, but the already-open PowerShell/VS Code
terminal session had cached the old PATH — a full application restart was required, not just a
new terminal tab.

**Fix:** confirmed each binary actually existed on disk (`Test-Path
"$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"` → `True`), then had the user fully quit and
relaunch VS Code (not just open a new terminal) to pick up the refreshed PATH.

## Issue 3 — Docker Desktop: engine ran, but the CLI never installed

**Symptom:** Docker Desktop's GUI opened and reported "Engine running," but `docker --version`
kept failing even after multiple full restarts.

**Root cause:** `Get-ChildItem -Recurse -Filter "docker.exe"` across the entire `C:` drive
returned nothing — the CLI binaries were never actually placed on disk, indicating a partial/
corrupted install (installer likely needed to run as Administrator).

**Decision:** rather than force a full reinstall (user pushback — too much friction), we pivoted
away from Docker entirely and ran the backend/frontend as native processes, using hosted
Supabase Postgres instead of a local containerized one. This is explicitly allowed by the
assignment brief ("You may use Supabase or Railway").

## Issue 4 — `pip install` build failures (asyncpg, tiktoken)

**Symptom:**
```
error: Microsoft Visual C++ 14.0 or greater is required.
...
error: can't find Rust compiler
```

**Root cause:** the originally pinned `asyncpg==0.29.0` predates prebuilt Windows wheels for
Python 3.13 (the user's installed Python version), so pip fell back to compiling from C source,
which needs Visual C++ Build Tools the user didn't have. Separately, `tiktoken==0.7.0` has no
prebuilt wheel for this combination either and needs a Rust toolchain to build from source.

**Fix:**
- Dropped `tiktoken` from `requirements.txt` entirely — it was only used for precise token
  counting during chunking, and `app/rag/chunking.py` already had a pure-Python fallback for
  when it's unavailable, so removing it changed no behavior.
- Initially bumped `asyncpg` to `>=0.30.0` (which does ship Windows wheels), but ultimately
  replaced it with `psycopg[binary,pool]>=3.2.0` instead — `psycopg` 3's binary wheels are more
  reliably prebuilt across Python versions on Windows, removing this entire class of problem
  rather than just working around one version. This required updating the SQLAlchemy connection
  string scheme from `postgresql+asyncpg://` to `postgresql+psycopg://` in both `config.py` and
  `.env`.

## Issue 5 — Supabase connectivity: IPv6-only direct connection

**Symptom:** `/api/health` reported `"database": false` with no visible error until the backend
terminal's traceback was inspected directly.

**Root cause:** the user's initial `DATABASE_URL` used Supabase's *direct* connection host
(`db.<project>.supabase.co`), which is IPv6-only — unreachable from most consumer/ISP networks
that lack IPv6 routing.

**Fix:** switched to Supabase's *session pooler* connection string instead
(`aws-0-<region>.pooler.supabase.com:5432`, with the pooler-specific username format
`postgres.<project-ref>`), which is IPv4-compatible. `/api/health` then reported
`"database": true`.

## Issue 6 — `psycopg` async mode incompatible with Windows' default event loop

**Symptom:** the FastAPI app (`uvicorn`) worked fine and correctly reported a healthy database
connection, but the standalone `scripts/ingest.py` failed with:
```
psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode.
```

**Root cause:** `psycopg`'s async mode requires asyncio's `SelectorEventLoop`; Windows defaults
to `ProactorEventLoop`. `uvicorn` sets the compatible event loop policy automatically as part of
its own startup, which is why the web app worked — but a standalone script invoked via
`asyncio.run()` does not get that for free.

**Fix:** added an explicit Windows-only event loop policy override at the top of
`scripts/ingest.py`:
```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```
Ingestion then completed successfully (2 sample transcripts, 2 chunks, embedded and stored in
Supabase's `transcript_chunks` table).

## Issue 7 — Retrieval false negative on a clearly-covered question

**Symptom:** asking "How did they improve onboarding activation?" — a question the sample
transcript directly answers — returned the "insufficient information" fallback message instead
of a grounded answer.

**Root cause:** `RETRIEVAL_SIMILARITY_THRESHOLD=0.55` was too strict for this small, short-sample
corpus (two single-chunk transcripts), causing the genuinely relevant chunk to fall just under
the cosine-similarity cutoff.

**Fix:** lowered the threshold to `0.3` in `.env` and restarted `uvicorn` (a plain `--reload`
does not pick up `.env` changes, since it only watches Python source files — a full restart was
required). Retried the same question and got the correct grounded, cited answer:
> "...redesigned onboarding... interactive checklist... activation went up roughly 3x...
> [Episode: building products people love, Guest: Jane Doe]"

## Issue 8 — Next.js dependency flagged with a critical CVE

**Symptom:** `npm install` completed but warned about 3 vulnerabilities (1 critical) in the pinned
`next@14.2.5`.

**Root cause:** Next.js disclosed several App Router / React Server Components vulnerabilities in
December 2025 (CVE-2025-66478 — CVSS 10.0 RCE — plus CVE-2025-55183/55184/67779), all fixed in
`14.2.35` for the 14.x line.

**Fix:** bumped `next` to `14.2.35` in `package.json` and re-ran `npm install next@14.2.35`
before ever starting the dev server, so the vulnerable version was never actually run.

## Final verification

With all of the above fixed, the full user-facing flow was verified working directly by the user:
- Grounded QA with correct citations (Ollama, local)
- Provider toggle correctly erroring out on missing `ANTHROPIC_API_KEY` (Claude, cloud) instead
  of crashing
- Ship 30 for 30 essay skill (shorter than the ~1,250-word target on the local 8B model — a real,
  documented local-model trade-off, not a bug)
- Artifact generation + sandboxed HTML/Markdown viewer

All fixes described above are reflected in the committed code (`backend/requirements.txt`,
`backend/app/config.py`, `backend/scripts/ingest.py`, `frontend/package.json`, `.env.example`).
