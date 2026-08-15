# Ticket 2: Ingest core

The `ingest(pdf_path)` front door. Source spec:
`docs/specs/ingestion-pipeline/document-ingestion-retrieval-pipeline.md`
(GitHub issue #2). Follows ADR-0004 (pipeline) and ADR-0005 (deep modules).

## Parent

Spec: Document ingestion and retrieval pipeline (CLI) — GitHub issue #2.

## What to build

A single front door `ingest(pdf_path)` that turns a PDF into searchable Chunks
in the vector store, using the seams from Ticket 1. It reports how many Chunks
were stored and for which Document.

Behaviour it makes work:

- Read the PDF page by page (pypdf), keeping the page number (pages start at 1).
- Cut each page into Chunks of about 800 characters with about 150 overlap;
  no Chunk crosses a page break, so each Chunk has exactly one page number.
- `chunk_index` is document-wide and 0-based, so sorting by it rebuilds reading
  order.
- Embed each Chunk as a passage (the `passage:` label).
- document id = document name = the file's base name (e.g. `report.pdf`).
- Each stored point carries payload `text`, `document_name`, `page`,
  `document_id`, `chunk_index`; the point id is a deterministic UUID5 from the
  document id plus the chunk index.
- Every ingest does delete-then-insert for the document id first, then writes
  the fresh Chunks (re-ingest never duplicates; re-ingesting a shorter edited
  file removes stale leftover Chunks).
- Pages with no extractable text produce no Chunks; a PDF that yields no text
  stores 0 Chunks and ingest reports 0.
- A missing file or a non-PDF file raises a clear error before any work.
- Returns the number of Chunks stored and the document name.

Tested through the `ingest` front door with the fake embedder and fake store —
tests must not reach into pypdf, the splitter, or the store directly.

## Acceptance criteria

- [ ] Ingesting a small known PDF stores the expected number of Chunks; each
      Chunk has one page number and the correct document name and chunk index.
- [ ] Chunks respect the ~800/150 size rule and no Chunk spans two pages.
- [ ] The embedder is asked to embed stored text as passages.
- [ ] Re-ingesting the same file does not double the Chunk count.
- [ ] Re-ingesting a shorter edited file removes the old leftover Chunks.
- [ ] A page with no extractable text produces no Chunks; a no-text PDF reports 0.
- [ ] A missing file or non-PDF file raises a clear error before any work.
- [ ] `ingest` returns the Chunk count and document name.

## Blocked by

- Ticket 1: Pipeline seams and fake adapters.
