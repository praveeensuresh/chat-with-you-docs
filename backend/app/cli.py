from __future__ import annotations

import typer

from app.config import settings
from app.pipeline.adapters import E5Embedder, QdrantStore
from app.pipeline.ingest import ingest as _ingest
from app.pipeline.search import search as _search

app = typer.Typer()


def _make_embedder() -> E5Embedder:
    return E5Embedder(settings.embedding_model)


def _make_store() -> QdrantStore:
    return QdrantStore(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection=settings.qdrant_collection,
    )


@app.command()
def ingest(pdf: str = typer.Argument(..., help="Path to the PDF file to ingest")) -> None:
    try:
        embedder = _make_embedder()
        store = _make_store()
        count, name = _ingest(pdf, embedder, store)
    except Exception as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    typer.echo(f"Stored {count} chunks from '{name}'")


@app.command()
def search(
    question: str = typer.Argument(..., help="Question to search for"),
    top_k: int = typer.Option(5, "--top-k", help="Maximum number of results to return"),
) -> None:
    try:
        hits = _search(question, _make_embedder(), _make_store(), top_k=top_k)
    except Exception as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    if not hits:
        typer.echo("No results found.")
        return
    for hit in hits:
        typer.echo(f"[{hit.document_name}, page {hit.page}] {hit.text}")


@app.command()
def reset() -> None:
    try:
        _make_store().clear()
    except Exception as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    typer.echo("Store cleared.")

