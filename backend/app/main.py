"""FastAPI entry point for the Chat With Your Docs backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(title="Chat With Your Docs API")

# The Next.js frontend runs on a different origin, so we must allow it (ADR-0001).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check. Also confirms config loaded."""
    return {"status": "ok", "embedding_model": settings.embedding_model}
