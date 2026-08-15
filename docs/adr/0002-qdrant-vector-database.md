# ADR-0002: Qdrant as the vector database

**Date**: 2026-08-08
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

The RAG pipeline stores document chunks as vectors and searches them by
relevance. We need a vector store for local development and for the live demo,
at $0, that a solo junior can run without heavy setup.

## Decision

Use Qdrant. Run it in Docker locally for development, and use the Qdrant Cloud
free tier for the deployed demo.

## Alternatives Considered

### Alternative 1: pgvector (Postgres)
- **Pros**: one database for vectors and metadata; SQL.
- **Cons**: must run and manage a full Postgres.
- **Why not**: heavier setup than needed for v1.

### Alternative 2: Qdrant local file mode
- **Pros**: no Docker needed.
- **Cons**: less like a real production server.
- **Why not**: we chose Docker for a more production-like dev loop.

## Consequences

### Positive
- Purpose-built vector search.
- The same `qdrant-client` talks to dev and demo; only the URL changes.

### Negative
- Docker must be installed and running for local development.

### Risks
- The free cloud cluster suspends after 1 week of no use. Mitigated by opening
  the demo now and then to keep it warm.
