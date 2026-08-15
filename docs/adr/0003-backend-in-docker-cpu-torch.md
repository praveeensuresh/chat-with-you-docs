# ADR-0003: Backend in Docker with CPU-only torch

**Date**: 2026-08-08
**Status**: accepted
**Deciders**: Praveen, AI assistant

## Context

We chose a split backend (ADR-0001) and wanted one-command startup plus deploy
parity. On this machine `torch` installed as a CUDA (GPU) build, which made the
backend image 8.7 GB and filled the dev disk to 100%. The demo host (Hugging
Face Spaces free) is CPU-only, and `e5-base` runs fine on CPU for this workload.

## Decision

Ship a deploy-style Docker image for the backend, wired into docker-compose next
to Qdrant, with `torch` pinned to the CPU-only wheel index.

## Alternatives Considered

### Alternative 1: Dev container with live reload
- **Pros**: edits show without a rebuild.
- **Cons**: more setup; the virtual env must be kept separate from mounted code.
- **Why not**: more complexity than needed right now.

### Alternative 2: CUDA torch
- **Pros**: GPU speed for local work.
- **Cons**: 8.7 GB image; GPU unused on the CPU demo host; filled the disk.
- **Why not**: too big for no benefit on the demo.

## Consequences

### Positive
- Image is about 2 GB and matches the CPU demo.
- One command starts the backend and Qdrant together.

### Negative
- No live reload inside Docker; update with `docker compose up -d --build backend`.
- No local GPU acceleration (not needed by this project).

### Risks
- Rebuilds re-download packages. Mitigated by the uv cache mount in the
  Dockerfile; daily coding can still use `uv run uvicorn --reload` on the host.
