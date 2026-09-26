# ADR-0001: Split FastAPI backend and separate frontend

**Date**: 2026-08-08
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

This is a greenfield portfolio project, "Chat With Your Docs". The main goal is
to show real backend engineering to hiring managers. The embedding model
(`e5-base` + torch) needs about 0.5-1 GB RAM to load, so where it runs shapes the
whole repository. We had to fix the app shape before scaffolding any folders.

## Decision

Build two apps: a FastAPI backend that holds the RAG pipeline and the embedding
model, and a separate Next.js frontend that calls it over HTTP.

## Alternatives Considered

### Alternative 1: One Streamlit app
- **Pros**: fastest to build; one deploy; Streamlit Cloud has enough RAM.
- **Cons**: weaker backend signal; a UI-only app hides the engineering.
- **Why not**: the main goal is to show backend skill.

### Alternative 2: Split, embeddings via a hosted endpoint
- **Pros**: tiny backend that fits a 512 MB host.
- **Cons**: adds an outside service and possible cost or rate limits.
- **Why not**: extra dependency not worth it for v1.

## Consequences

### Positive
- Clear backend/frontend separation and real API skill on show.
- The backend can hold the model and the retrieval logic in one place.

### Negative
- Two deploys instead of one.
- The frontend must call the backend across origins, so CORS is required.

### Risks
- The backend needs a RAM-capable host, not Render free (512 MB). Mitigated by
  deploying the backend on Hugging Face Spaces (see ADR-0006).
