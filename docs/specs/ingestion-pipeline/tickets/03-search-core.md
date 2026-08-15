# Ticket 3: Search core

The `search(question, top_k=5)` front door. Source spec:
`docs/specs/ingestion-pipeline/document-ingestion-retrieval-pipeline.md`
(GitHub issue #2). Follows ADR-0004 (pipeline) and ADR-0005 (deep modules).

## Parent

Spec: Document ingestion and retrieval pipeline (CLI) — GitHub issue #2.

## What to build

A single front door `search(question, top_k=5)` that finds the closest Chunks
to a question, using the seams from Ticket 1. Each hit carries the facts a
Citation needs.

Behaviour it makes work:

- Embed the question as a query (the `query:` label).
- Ask the store for the closest Chunks by the query vector.
- Return a list of hits, each with `text`, `document_name`, `page`, `score`.
- `top_k` controls how many hits come back (default 5).
- A `top_k` larger than the number of stored Chunks returns all of them, no
  error.
- A question that matches nothing returns an empty list (the clear "not found"
  signal the later Grounded-answer step relies on).

Tested through the `search` front door with the fake embedder and fake store,
seeding Chunks via the store fake — tests must not reach into the store directly
past the seam.

## Acceptance criteria

- [ ] The embedder is asked to embed the question as a query.
- [ ] Search over seeded Chunks returns hits that include document name, page,
      text, and score, honouring `top_k`.
- [ ] A `top_k` larger than the number of stored Chunks returns all available
      Chunks with no error.
- [ ] A search that matches nothing returns an empty list.

## Blocked by

- Ticket 1: Pipeline seams and fake adapters.
