# Ticket 1: Pipeline seams and fake adapters

Prefactor foundation for the document ingestion and retrieval pipeline.
Source spec: `docs/specs/ingestion-pipeline/document-ingestion-retrieval-pipeline.md`
(GitHub issue #2). Follows ADR-0005 (deep modules + test seams).

## Parent

Spec: Document ingestion and retrieval pipeline (CLI) — GitHub issue #2.

## What to build

The two swap points the pipeline is built on, plus the in-memory fakes that let
the later cores be tested with no model download and no live server.

- An **Embedder seam** with two named operations: embed stored text (the
  `passage:` label) and embed a question (the `query:` label). Each returns a
  fixed-length (768) list of numbers per input.
- A **Vector-store seam** with four operations: upsert Chunks (id, vector,
  payload); delete all Chunks for a document id; search by a query vector
  returning top_k with payload and score; clear all.
- A **fake Embedder**: deterministic in-memory numbers that also records which
  operation was called and the raw text passed in.
- A **fake Vector-store**: in-memory nearest-match that records its calls and
  supports upsert, delete-by-document, search, and clear.

Do NOT build "any model" or "any vector DB" provider abstractions — only the
test fake is the second adapter (ADR-0005 rule).

## Acceptance criteria

- [x] Embedder seam exposes separate embed-passages and embed-query operations.
- [x] Vector-store seam exposes upsert, delete-by-document, search, clear.
- [x] Fake Embedder returns fixed-length deterministic vectors and records the
      operation name and raw text for each call.
- [x] Fake Vector-store performs in-memory nearest-match search and records calls.
- [x] A test proves the fakes record their calls and the fake store returns
      closest-first results.

## Blocked by

- None — can start immediately.
