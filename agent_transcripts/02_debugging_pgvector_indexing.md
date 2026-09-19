# Session: Fixing the pgvector similarity query

**Initial (failed) approach:** Passed the Python `list[float]` embedding directly as a query
parameter without casting it, e.g.:

```sql
SELECT ..., 1 - (embedding <=> :vector) AS similarity_score
FROM transcript_chunks
WHERE 1 - (embedding <=> :vector) >= :threshold
```

**Problem:** asyncpg has no native adapter for Python lists → pgvector's `vector` type; the driver
raises a type-mismatch error because it doesn't know how to coerce a bound parameter to `vector`
without an explicit cast, and pgvector's operator resolution needs both operands typed as `vector`.

**Fix:** Serialize the embedding as its pgvector text representation (`str(query_vector)`, i.e.
`"[0.01, -0.02, ...]"`) and add an explicit `CAST(:vector AS vector)` in the SQL, matching pgvector's
documented parameter-binding pattern for drivers without a native adapter:

```sql
1 - (embedding <=> CAST(:vector AS vector)) AS similarity_score
...
WHERE 1 - (embedding <=> CAST(:vector AS vector)) >= :threshold
```

**Outcome:** Query executes correctly against a pgvector-enabled Postgres instance; documented the
same pattern in `app/rag/retriever.py` so future contributors don't hit the same error.
