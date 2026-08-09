# Tickets: Document ingestion and retrieval pipeline (CLI)

Tracer-bullet tickets for the backend ingestion + retrieval pipeline.
Source spec: `docs/specs/document-ingestion-retrieval-pipeline.md` (GitHub issue #2).
Published as GitHub issues #3 and #4.

Work the **frontier**: any ticket whose blockers are all done. For this linear chain, that means top to bottom.

## Ingest a PDF into Qdrant (with reset)

GitHub issue: #3

**What to build:** From the command line, ingest a PDF into Qdrant and be able to wipe the store. `ingest <pdf>` reads the PDF page by page, cuts it into Chunks (~800 characters, ~150 overlap, one page per Chunk), turns each Chunk into numbers with `e5-base` (stored text uses the `passage:` label), and stores it in Qdrant with the payload a Citation needs. Re-ingesting the same or an edited file replaces cleanly. `reset` wipes all Documents. This ticket also builds the embedder seam and the vector-store seam, each with a real adapter and an in-memory test fake, which the Search ticket reuses. Follows ADR-0004, ADR-0005.

**Blocked by:** None — can start immediately.

- [ ] `ingest <path-to-pdf>` prints the number of Chunks stored and the document name.
- [ ] Chunks are about 800 characters with about 150 overlap, and no Chunk crosses a page.
- [ ] Each stored Chunk payload has text, document_name, page, document_id, chunk_index.
- [ ] Pages are numbered from 1; chunk_index is document-wide and 0-based.
- [ ] document_id and document_name are the file's base name.
- [ ] Stored text is embedded through the passage operation (the `passage:` label).
- [ ] Each Chunk id is a deterministic UUID derived from document_id + chunk_index.
- [ ] Re-ingesting the same file does not create duplicate Chunks.
- [ ] Re-ingesting a shorter edited file removes the old version's leftover Chunks (delete-then-insert).
- [ ] A page with no extractable text produces no Chunks; a PDF with no text stores 0 and reports it.
- [ ] A missing file or a non-PDF file raises a clear error before any work.
- [ ] `reset` removes all Documents from the store.
- [ ] The embedder seam and vector-store seam each have a real adapter and an in-memory test fake.
- [ ] Tests run via `uv run pytest` in `backend/`, using the fakes (no model download, no live Qdrant), covering the behaviors above through the `ingest` front door.

## Search returns cited Chunks

GitHub issue: #4

**What to build:** `search "<question>" [--top-k N]` turns the question into numbers with `e5-base` (the `query:` label), finds the closest Chunks in Qdrant, and prints each one with its document name, page, and text (the Citation). Reuses the embedder seam and vector-store seam built in "Ingest a PDF into Qdrant (with reset)". Follows ADR-0004, ADR-0005.

**Blocked by:** Ingest a PDF into Qdrant (with reset) (#3).

- [ ] `search "<question>"` prints each hit with document_name, page, and text.
- [ ] The question is embedded through the query operation (the `query:` label).
- [ ] `--top-k N` controls how many hits return; default is 5.
- [ ] A question that matches nothing returns an empty result.
- [ ] A top_k larger than the number of stored Chunks returns all of them with no error.
- [ ] Tests run via `uv run pytest` in `backend/`, using the fakes, covering the behaviors above through the `search` front door.
