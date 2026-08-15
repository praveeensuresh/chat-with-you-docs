from __future__ import annotations

import hashlib
import math

from app.pipeline.seams import VECTOR_SIZE, Chunk, SearchResult


def _deterministic_vector(text: str) -> list[float]:
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    numbers: list[float] = []
    counter = 0
    while len(numbers) < VECTOR_SIZE:
        block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for byte in block:
            numbers.append(byte / 255.0)
            if len(numbers) == VECTOR_SIZE:
                break
        counter += 1
    return numbers


def _cosine(a: list[float], b: list[float]) -> float:
    assert len(a) == len(b) == VECTOR_SIZE
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class FakeEmbedder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            self.calls.append(("passage", text))
            vectors.append(_deterministic_vector(text))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        self.calls.append(("query", text))
        return _deterministic_vector(text)


class FakeVectorStore:
    def __init__(self) -> None:
        self.points: dict[str, Chunk] = {}
        self.calls: list[tuple[str, ...]] = []

    def upsert(self, chunks: list[Chunk]) -> None:
        self.calls.append(("upsert", len(chunks)))
        for chunk in chunks:
            self.points[chunk.id] = chunk

    def delete_by_document(self, document_id: str) -> None:
        self.calls.append(("delete_by_document", document_id))
        self.points = {
            point_id: chunk
            for point_id, chunk in self.points.items()
            if chunk.payload.document_id != document_id
        }

    def search(self, query_vector: list[float], top_k: int) -> list[SearchResult]:
        self.calls.append(("search", top_k))
        scored = [
            (_cosine(query_vector, chunk.vector), chunk)
            for chunk in self.points.values()
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            SearchResult(payload=chunk.payload, score=score)
            for score, chunk in scored[:top_k]
        ]

    def clear(self) -> None:
        self.calls.append(("clear",))
        self.points = {}
