from __future__ import annotations

from app.pipeline.seams import Embedder, Hit, VectorStore


def search(
    question: str,
    embedder: Embedder,
    store: VectorStore,
    top_k: int = 5,
) -> list[Hit]:
    query_vector = embedder.embed_query(question)
    results = store.search(query_vector, top_k)
    results = sorted(results, key=lambda r: r.score, reverse=True)
    return [
        Hit(
            text=result.payload.text,
            document_name=result.payload.document_name,
            page=result.payload.page,
            score=result.score,
        )
        for result in results
    ]
