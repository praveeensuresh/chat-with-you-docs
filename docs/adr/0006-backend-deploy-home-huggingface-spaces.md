# ADR-0006: Backend deploy home is Hugging Face Spaces (not Render)

**Date**: 2026-08-09
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

We keep the `e5-base` embedding model loaded inside the backend process. That
model plus its runtime needs about 0.5-1 GB of memory just to switch on. The
spec listed Render free tier as a backend option, but Render free gives only
512 MB of memory, which is not enough and would crash the backend on startup.

## Decision

Deploy the backend on the Hugging Face Spaces free tier (about 16 GB memory,
CPU only). Do not use Render free tier for this backend.

## Alternatives Considered

### Alternative 1: Render free tier
- **Pros**: familiar, simple setup.
- **Cons**: 512 MB memory cannot load `e5-base`; it would run out of memory.
- **Why not**: too little memory for the chosen model.

### Alternative 2: Switch to `all-MiniLM-L6-v2` to fit small hosts
- **Pros**: lighter model, more host choices.
- **Cons**: weaker retrieval quality.
- **Why not**: we chose `e5-base` for better answers (ADR-0004).

## Consequences

### Positive
- `e5-base` runs with plenty of spare memory.
- Matches the CPU-only Docker image (ADR-0003).

### Negative
- Tied to one host for the demo.

### Risks
- Free Spaces suspend after being idle. Mitigated by opening the demo now and
  then to keep it awake.
