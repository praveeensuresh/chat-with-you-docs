# ADR-0004: Document ingestion and retrieval pipeline

**Date**: 2026-08-09
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

Phase 2 turns a PDF into data we can search. The steps are: read the PDF, cut
it into small pieces, turn each piece into numbers, store them, and later find
the closest pieces to a question. We also must show citations (which document
and which page an answer came from). These choices get baked into every stored
vector, so changing them later means re-doing every document.

## Decision

- Read the PDF with `pypdf`, one page at a time, and keep the page number.
- Cut each page's text with `langchain-text-splitters` into chunks of about 800
  characters with about 150 characters of overlap. A chunk never crosses a page.
- Make embeddings with `e5-base`. Stored text gets the `passage: ` label;
  questions get the `query: ` label.
- Store each chunk in Qdrant (vector size 768, cosine distance) with a payload
  of: text, document name, page number, document id, chunk index.
- The document id is the file name. The chunk id is a fixed UUID5 derived from
  the document id plus the chunk index. Qdrant only accepts an unsigned integer
  or a UUID as a point id, so a plain text id such as `report.pdf:3` cannot be
  used; deriving a UUID keeps the id stable across re-uploads and valid for
  Qdrant. The page is not part of the id, because the chunk index already counts
  across the whole document and cannot repeat. Every upload does delete-then-insert
  for that document id.

## Alternatives Considered

### Alternative 1: A stronger PDF reader (pdfplumber or PyMuPDF)
- **Pros**: cleaner text, better with tables and columns.
- **Cons**: heavier; PyMuPDF is AGPL-licensed.
- **Why not**: `pypdf` is light and enough for normal text PDFs. We can swap it
  later if extraction quality is poor.

### Alternative 2: Content-hash document id
- **Pros**: two different files that share a name stay separate.
- **Cons**: an edited file becomes a new document, so the old version lingers
  and delete-then-insert cannot clear it.
- **Why not**: for one-person testing, file-name id plus delete-then-insert
  replaces edited files cleanly.

### Alternative 3: Random chunk ids
- **Pros**: simplest.
- **Cons**: re-uploading the same file duplicates its chunks.
- **Why not**: fixed ids plus delete-then-insert avoid duplicates and leftovers.

### Alternative 4: A plain text chunk id such as `report.pdf:3`
- **Pros**: readable, and needs no derivation step.
- **Cons**: Qdrant rejects it — point ids must be an unsigned integer or a UUID.
- **Why not**: not possible in the chosen store. UUID5 keeps the same stability
  with a valid id type.

## Consequences

### Positive
- Citations can name the exact document and page.
- Re-uploads stay clean (no duplicates, no stale chunks).
- Light memory and disk footprint.

### Negative
- Scanned or fancy-layout PDFs may extract badly (a `pypdf` limit).
- Two different files with the same name would clash.

### Risks
- Forgetting the `passage:`/`query:` labels silently lowers answer quality.
  Mitigated by baking the labels into the core functions.
- Changing chunk size or the model later needs a full re-embed. Mitigated by
  keeping ingestion behind one function (ADR-0005).
