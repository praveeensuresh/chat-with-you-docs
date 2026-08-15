# ADR-0005: Deep-module pipeline with test seams

**Date**: 2026-08-09
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

We want the pipeline to be easy for a person or an AI to read, and easy to test.
Running the real embedding model needs a ~440 MB download, and real search needs
a running Qdrant. If tests call those directly, tests become slow and can break
for reasons unrelated to our code.

## Decision

Put the real work behind two small front doors: `ingest(pdf_path)` and
`search(question, top_k)`. The command line now, and the web page later, are thin
wrappers that call these same two functions. Put a seam (a swappable slot) in
front of the embedding model and in front of the Qdrant store. The running app
plugs in the real `e5-base` and real Qdrant; tests plug in fast in-memory fakes.

## Alternatives Considered

### Alternative 1: Logic inside the command-line script
- **Pros**: simplest to write right now.
- **Cons**: the future web page would have to duplicate the logic.
- **Why not**: causes rework and two copies of the same behavior.

### Alternative 2: Make the vector DB and embedding model swappable providers
- **Pros**: could swap Qdrant or the model later.
- **Cons**: we have only one of each, so the slot has nothing else to plug in.
- **Why not**: over-engineering. Rule: add a seam only when two real things use
  it. One thing = hard-wire it.

### Alternative 3: No seams; test against the real model and real Qdrant
- **Pros**: fewer layers of code.
- **Cons**: slow, network-dependent, fragile tests.
- **Why not**: testability is a core goal. The embedder and store seams each have
  two real adapters (the real one plus a test fake), so they earn their place.

## Consequences

### Positive
- Two clear entry points make the system easy to read and navigate.
- Tests run fast with no model download or live server.
- The web page reuses the core functions with almost no new code.

### Negative
- A little indirection: one interface layer for the embedder and the store.

### Risks
- Seam scope creep (adding slots we do not need). Mitigated by the
  "two real adapters" rule from this ADR.
