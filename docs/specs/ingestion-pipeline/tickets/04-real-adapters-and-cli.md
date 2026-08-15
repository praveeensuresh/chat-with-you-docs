# Ticket 4: Real adapters and Typer CLI

The true end-to-end demo. Source spec:
`docs/specs/ingestion-pipeline/document-ingestion-retrieval-pipeline.md`
(GitHub issue #2). Follows ADR-0004, ADR-0005, ADR-0006 (deploy home), ADR-0003
(CPU-only torch).

## Parent

Spec: Document ingestion and retrieval pipeline (CLI) — GitHub issue #2.

## What to build

The real implementations of the two seams from Ticket 1, wired into the
`ingest` and `search` cores from Tickets 2 and 3, and exposed through a Typer
command line. This is where a real PDF goes into a real store and comes back out
via retrieval.

Behaviour it makes work:

- **Real Embedder adapter**: `e5-base` via sentence-transformers, applying the
  `passage:` / `query:` labels, returning 768 numbers per input. Loaded
  in-process, CPU-only torch (ADR-0003).
- **Real Vector-store adapter**: Qdrant (vector size 768, cosine), supporting
  upsert, delete-by-document, search with score, and clear. Reads
  `qdrant_url`, `qdrant_api_key`, `qdrant_collection` from the existing
  `Settings` (no new config).
- **Typer CLI**, thin wrappers over the two front doors:
  - `ingest <path-to-pdf>` — prints Chunks stored and document name.
  - `search "<question>" [--top-k N]` — prints each hit with document name,
    page, and text.
  - `reset` — wipes all Documents from the store (store clear).

Config: reuse existing `Settings` values only.

## Acceptance criteria

- [ ] `ingest <pdf>` against a real Qdrant loads the PDF and prints the Chunk
      count and document name.
- [ ] `search "<question>"` prints hits with document name, page, and text, and
      `--top-k` controls the count.
- [ ] `reset` wipes all Documents so a following search returns nothing.
- [ ] Real Qdrant collection is created with vector size 768 and cosine
      distance.
- [ ] Real Embedder applies the `passage:` label on ingest and `query:` label
      on search.

## Blocked by

- Ticket 2: Ingest core.
- Ticket 3: Search core.
