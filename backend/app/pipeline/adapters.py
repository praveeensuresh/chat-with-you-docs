from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

from app.pipeline.seams import VECTOR_SIZE, Chunk, ChunkPayload, SearchResult

_PASSAGE_PREFIX = "passage: "
_QUERY_PREFIX = "query: "


class E5Embedder:
    def __init__(self, model_name: str = "intfloat/e5-base") -> None:
        self._model = SentenceTransformer(model_name)

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        prefixed = [_PASSAGE_PREFIX + text for text in texts]
        return self._model.encode(prefixed, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode(_QUERY_PREFIX + text, normalize_embeddings=True).tolist()


class QdrantStore:
    def __init__(
        self,
        url: str,
        api_key: str,
        collection: str,
        _client: QdrantClient | None = None,
    ) -> None:
        self._client = _client or QdrantClient(url=url, api_key=api_key or None)
        self._collection = collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )

    def upsert(self, chunks: list[Chunk]) -> None:
        points = [
            PointStruct(
                id=chunk.id,
                vector=chunk.vector,
                payload={
                    "text": chunk.payload.text,
                    "document_name": chunk.payload.document_name,
                    "page": chunk.payload.page,
                    "document_id": chunk.payload.document_id,
                    "chunk_index": chunk.payload.chunk_index,
                },
            )
            for chunk in chunks
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def delete_by_document(self, document_id: str) -> None:
        self._client.delete(
            collection_name=self._collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id", match=MatchValue(value=document_id)
                        )
                    ]
                )
            ),
        )

    def search(self, query_vector: list[float], top_k: int) -> list[SearchResult]:
        response = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            SearchResult(
                payload=ChunkPayload(
                    text=point.payload["text"],
                    document_name=point.payload["document_name"],
                    page=point.payload["page"],
                    document_id=point.payload["document_id"],
                    chunk_index=point.payload["chunk_index"],
                ),
                score=point.score,
            )
            for point in response.points
        ]

    def clear(self) -> None:
        self._client.delete_collection(self._collection)
        self._ensure_collection()
