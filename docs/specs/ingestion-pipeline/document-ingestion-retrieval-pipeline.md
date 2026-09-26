<!-- Published as GitHub issue #2: https://github.com/praveeensuresh/chat-with-you-docs/issues/2 -->

# Spec: Document ingestion and retrieval pipeline (CLI)

Phase 2, Week 1. Backend only, proven from the command line. This is the base that the LLM answer step (Week 2) and the upload page (later) sit on top of.

Uses the glossary in `CONTEXT.md` (Document, Chunk, Citation, Grounded answer) and follows ADR-0004 (pipeline), ADR-0005 (deep modules + test seams), ADR-0006 (deploy home).

## Problem Statement

A person has their own documents (PDFs) and wants to ask questions about them and get answers that come only from those documents, with proof of where each answer came from. Before any of that can work, the system must be able to take a PDF, break it into searchable pieces, and find the right pieces for a question. Right now the backend has only a health check — there is no way to load a Document or retrieve from it.

## Solution

Build the backend ingestion and retrieval pipeline, usable from the command line, so retrieval is proven before any UI or LLM work.

- `ingest` a PDF: read it page by page, cut it into Chunks, turn each Chunk into numbers (an embedding), and store it in Qdrant with the facts needed for a Citation.
- `search` a question: turn the question into numbers, find the closest Chunks, and print each one with its document name, page, and text (the Citation).
- `reset`: wipe the store to start clean while testing.

The real work lives in two functions, `ingest` and `search`. The command line is a thin wrapper over them, so the later upload page and LLM step reuse the same functions with no rewrite.

## User Stories

1. As a developer, I want to ingest a PDF from the command line, so that its contents become searchable.
2. As a developer, I want ingest to tell me how many Chunks were stored and for which document, so that I can confirm it worked.
3. As a developer, I want each Chunk cut to about 800 characters with about 150 characters of overlap, so that pieces are specific but do not lose meaning at their edges.
4. As a developer, I want no Chunk to cross a page break, so that every Chunk has exactly one page number.
5. As a developer, I want each stored Chunk to carry its text, document name, page number, document id, and chunk index, so that a Citation can be built later.
6. As a developer, I want stored text to use the `passage:` label and questions to use the `query:` label, so that the e5-base model works correctly.
7. As a developer, I want the document id and display name to be the file's base name, so that documents are grouped and shown by a human-readable name.
8. As a developer, I want re-ingesting the same file to not create duplicate Chunks, so that search results stay clean.
9. As a developer, I want re-ingesting an edited (shorter) file to remove the old version's leftover Chunks, so that stale content cannot pollute answers.
10. As a developer, I want to search a question and get back the closest Chunks, so that I can prove retrieval works.
11. As a developer, I want each search result to show document name, page, and text, so that I can see the Citation.
12. As a developer, I want to control how many results come back (top_k, default 5), so that I can tune the amount of context.
13. As a developer, I want a search against an empty store to return an empty result, so that the later Grounded-answer behavior has a clear signal to say "not found." There is no minimum score, so once Documents are stored the closest Chunks always come back (ADR-0008).
14. As a developer, I want a reset command that wipes all stored Documents, so that I can start clean between tests.
15. As a developer, I want a clear error when I point ingest at a missing file or a non-PDF file, so that mistakes fail loudly instead of silently.
16. As a developer, I want pages that contain no extractable text to produce no Chunks, so that empty pieces do not enter the store.
17. As a developer, I want a top_k larger than the number of stored Chunks to simply return all of them, so that small stores do not error.
18. As a developer, I want the pipeline logic to sit behind two small functions, so that a person or an AI can understand the system by reading two entry points.
19. As a developer, I want to swap in a fake embedder and a fake store during tests, so that tests run fast with no model download or live server.
20. As a maintainer, I want a passing test suite over this pipeline, so that later refactors are safe (the Safety Floor).

## Implementation Decisions

Modules (deep modules, ADR-0005):

- **Ingestion core** — front door `ingest(pdf_path)`. Hides: read pages with pypdf, cut each page with `langchain-text-splitters` (about 800 chars, 150 overlap), embed as passages, build ids, delete-then-insert. Returns the number of Chunks stored and the document name.
- **Retrieval core** — front door `search(question, top_k=5)`. Hides: embed the question as a query, ask the store for the closest Chunks, map results to hits. Returns a list of hits, each with `text`, `document_name`, `page`, `score`.

Seams (ADR-0005), with a real adapter and a fake adapter each:

- **Embedder seam** — two operations: embed stored text (applies the `passage:` label) and embed a question (applies the `query:` label). Returns a fixed-length list of numbers per input. Real adapter: `e5-base` via sentence-transformers. Fake adapter: deterministic in-memory numbers that also records which operation was called and the raw text. Splitting the two operations makes the label choice explicit and testable at the seam.
- **Vector-store seam** — operations: upsert Chunks (id, vector, payload); delete all Chunks for a document id; search by a query vector returning top_k with payload and score; clear all. Real adapter: Qdrant (vector size 768, cosine). Fake adapter: in-memory nearest-match that records calls.

Do NOT build "any model" or "any vector DB" provider abstractions — only one real thing exists for each, so the only second adapter is the test fake (ADR-0005 rule).

Schema (one Qdrant point per Chunk):

- **id**: a deterministic UUID derived from the document id plus the chunk index (UUID5). Reason: Qdrant point ids must be an unsigned integer or a UUID, so a raw string like "report.pdf:3" cannot be the id directly; deriving a UUID keeps ids stable across re-ingests and valid for Qdrant.
- **vector**: 768 numbers.
- **payload**: `text`, `document_name`, `page`, `document_id`, `chunk_index`.

Rules that close gaps:

- **document id = document name = the file's base name** (for example `report.pdf`), not the full path.
- **Pages are numbered from 1** (matches how people read a PDF).
- **chunk_index is document-wide and 0-based**, so sorting by it rebuilds reading order.
- **Every ingest does delete-then-insert** for the document id first, then writes the fresh Chunks.
- **Empty or no-text pages produce no Chunks**; a PDF that yields no text stores 0 Chunks and ingest reports 0.
- **Bad input** (missing file, or a file that is not a PDF) raises a clear error before any work.
- **top_k greater than the number of stored Chunks** returns all available Chunks, no error.
- **reset** clears all Documents from the store.

Command line (Typer), thin wrappers over the two functions:

- `ingest <path-to-pdf>` — prints Chunks stored and document name.
- `search "<question>" [--top-k N]` — prints each hit with document name, page, and text.
- `reset` — wipes the store.

Config: reuse the existing `Settings` values (`embedding_model`, `qdrant_url`, `qdrant_collection`, `qdrant_api_key`). No new config needed for this phase.

## Testing Decisions

A good test checks external behavior at the two front doors (`ingest`, `search`), not the internals. Tests must not reach into pypdf, the splitter, or Qdrant directly. There is exactly one test surface (the pipeline interface), with the fake embedder and fake store injected behind it.

Modules tested: the Ingestion core and Retrieval core, through their front doors, using the fakes.

Prior art: none yet — these are the first tests in the repo, so they also set the Safety Floor for future refactors. Test runner is pytest, run with `uv run pytest` in `backend/` (matches the uv + Python 3.12 setup).

Test cases (all through `ingest` / `search`):

- Ingest a small known PDF: assert the number of Chunks, and that each Chunk has one page number and correct document name and chunk index.
- Chunk sizing: assert Chunks respect the size and page-boundary rules (no Chunk spans two pages).
- Labels: assert the embedder was asked to embed stored text as passages, and questions as queries.
- Re-ingest the same file: assert Chunk count does not double.
- Re-ingest a shorter edited file: assert the old leftover Chunks are gone.
- Search over seeded Chunks: assert the returned hits include document name and page, and honor top_k.
- Search against an empty store: assert an empty result.
- top_k larger than stored Chunks: assert all available Chunks return, no error.
- Bad path / non-PDF: assert a clear error is raised.

## Out of Scope

- LLM answer generation and Grounded-answer wording (Week 2, separate spec).
- The web upload page (later, separate spec).
- The eval script — 10-20 test questions scored automatically (spec must-have #8, later). This is where real answer quality is measured.
- An optional slow end-to-end smoke test using the real `e5-base` and real Qdrant (can be added with the eval-script work).
- Non-PDF formats: txt, markdown, docx.
- Auth, multi-user, and cost tracking.

## Further Notes

- The fast tests prove the plumbing is correct (chunking, labels, payload, ids, dedup, top_k, empty). They do NOT prove answer quality, because the fake embedder returns fake numbers. Answer quality is the eval script's job, later.
- The two front doors are deliberately reused later by the LLM answer step and the upload page, so no rewrite is needed.
- Deploy target for the backend is Hugging Face Spaces free tier with CPU-only torch (ADR-0006, ADR-0003).
- Repo comment rule (CLAUDE.md): no comments except short section comments stating purpose.
