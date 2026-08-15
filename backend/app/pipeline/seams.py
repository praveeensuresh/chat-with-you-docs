from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

VECTOR_SIZE = 768


@dataclass
class ChunkPayload:
    text: str
    document_name: str
    page: int
    document_id: str
    chunk_index: int


@dataclass
class Chunk:
    id: str
    vector: list[float]
    payload: ChunkPayload


@dataclass
class SearchResult:
    payload: ChunkPayload
    score: float


class Embedder(Protocol):
    def embed_passages(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    def upsert(self, chunks: list[Chunk]) -> None: ...

    def delete_by_document(self, document_id: str) -> None: ...

    def search(self, query_vector: list[float], top_k: int) -> list[SearchResult]: ...

    def clear(self) -> None: ...
