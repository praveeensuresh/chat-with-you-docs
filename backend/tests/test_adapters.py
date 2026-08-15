from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.pipeline.adapters import E5Embedder, QdrantStore
from app.pipeline.seams import VECTOR_SIZE, Chunk, ChunkPayload

_ID_NS = uuid.UUID("c2b7f1a0-5d9e-4b8c-a3f6-1e2d3c4b5a67")


def _make_chunk(
    chunk_id: str,
    vector: list[float],
    document_id: str,
    text: str,
    page: int = 1,
    index: int = 0,
) -> Chunk:
    real_id = str(uuid.uuid5(_ID_NS, chunk_id))
    return Chunk(
        id=real_id,
        vector=vector,
        payload=ChunkPayload(
            text=text,
            document_name=document_id,
            page=page,
            document_id=document_id,
            chunk_index=index,
        ),
    )


def _in_memory_store(collection: str = "test") -> QdrantStore:
    client = QdrantClient(":memory:")
    return QdrantStore(url="", api_key="", collection=collection, _client=client)


def _mock_model_returning(vectors: list[list[float]]) -> MagicMock:
    mock = MagicMock()
    mock.encode.return_value = np.array(vectors)
    return mock


# --- E5Embedder ---


def test_e5_embedder_applies_passage_prefix_to_single_text():
    model = _mock_model_returning([[0.1] * VECTOR_SIZE])
    with patch("app.pipeline.adapters.SentenceTransformer", return_value=model):
        embedder = E5Embedder()
        embedder.embed_passages(["hello world"])
    model.encode.assert_called_once_with(
        ["passage: hello world"], normalize_embeddings=True
    )


def test_e5_embedder_applies_passage_prefix_to_multiple_texts():
    model = _mock_model_returning([[0.1] * VECTOR_SIZE, [0.2] * VECTOR_SIZE])
    with patch("app.pipeline.adapters.SentenceTransformer", return_value=model):
        embedder = E5Embedder()
        embedder.embed_passages(["first", "second"])
    model.encode.assert_called_once_with(
        ["passage: first", "passage: second"], normalize_embeddings=True
    )


def test_e5_embedder_applies_query_prefix():
    model = MagicMock()
    model.encode.return_value = np.array([0.1] * VECTOR_SIZE)
    with patch("app.pipeline.adapters.SentenceTransformer", return_value=model):
        embedder = E5Embedder()
        embedder.embed_query("what is this?")
    model.encode.assert_called_once_with(
        "query: what is this?", normalize_embeddings=True
    )


def test_e5_embedder_returns_768_floats_per_passage():
    model = _mock_model_returning([[0.5] * VECTOR_SIZE])
    with patch("app.pipeline.adapters.SentenceTransformer", return_value=model):
        embedder = E5Embedder()
        result = embedder.embed_passages(["some text"])
    assert len(result) == 1
    assert len(result[0]) == VECTOR_SIZE
    assert all(isinstance(v, float) for v in result[0])


def test_e5_embedder_returns_one_vector_per_passage_for_multiple_texts():
    model = _mock_model_returning(
        [[0.1] * VECTOR_SIZE, [0.2] * VECTOR_SIZE, [0.3] * VECTOR_SIZE]
    )
    with patch("app.pipeline.adapters.SentenceTransformer", return_value=model):
        embedder = E5Embedder()
        result = embedder.embed_passages(["a", "b", "c"])
    assert len(result) == 3


def test_e5_embedder_returns_768_floats_for_query():
    model = MagicMock()
    model.encode.return_value = np.array([0.5] * VECTOR_SIZE)
    with patch("app.pipeline.adapters.SentenceTransformer", return_value=model):
        embedder = E5Embedder()
        result = embedder.embed_query("a question")
    assert len(result) == VECTOR_SIZE
    assert all(isinstance(v, float) for v in result)


# --- QdrantStore ---


def test_qdrant_store_creates_collection_on_init():
    client = QdrantClient(":memory:")
    QdrantStore(url="", api_key="", collection="mydocs", _client=client)
    names = [c.name for c in client.get_collections().collections]
    assert "mydocs" in names


def test_qdrant_store_collection_uses_vector_size_768_and_cosine():
    client = QdrantClient(":memory:")
    QdrantStore(url="", api_key="", collection="mydocs", _client=client)
    info = client.get_collection("mydocs")
    params = info.config.params.vectors
    assert isinstance(params, VectorParams)
    assert params.size == VECTOR_SIZE
    assert params.distance == Distance.COSINE


def test_qdrant_store_does_not_error_if_collection_already_exists():
    client = QdrantClient(":memory:")
    QdrantStore(url="", api_key="", collection="mydocs", _client=client)
    QdrantStore(url="", api_key="", collection="mydocs", _client=client)


def test_qdrant_store_upsert_and_search_round_trip():
    store = _in_memory_store()
    vector = [0.1] * VECTOR_SIZE
    chunk = _make_chunk("id-1", vector, "report.pdf", "some text about Paris", page=3)
    store.upsert([chunk])
    results = store.search(vector, top_k=1)
    assert len(results) == 1
    r = results[0]
    assert r.payload.text == "some text about Paris"
    assert r.payload.document_name == "report.pdf"
    assert r.payload.page == 3
    assert isinstance(r.score, float)


def test_qdrant_store_search_respects_top_k():
    store = _in_memory_store()
    for i in range(5):
        v = [float(i + 1) / 10] * VECTOR_SIZE
        store.upsert([_make_chunk(f"id-{i}", v, "doc.pdf", f"text {i}", index=i)])
    results = store.search([0.3] * VECTOR_SIZE, top_k=2)
    assert len(results) == 2


def test_qdrant_store_top_k_larger_than_stored_returns_all():
    store = _in_memory_store()
    store.upsert([_make_chunk("id-1", [0.1] * VECTOR_SIZE, "doc.pdf", "text", index=0)])
    results = store.search([0.1] * VECTOR_SIZE, top_k=50)
    assert len(results) == 1


def test_qdrant_store_delete_by_document_removes_only_that_document():
    store = _in_memory_store()
    store.upsert(
        [
            _make_chunk("id-a", [0.1] * VECTOR_SIZE, "a.pdf", "text A", index=0),
            _make_chunk("id-b", [0.2] * VECTOR_SIZE, "b.pdf", "text B", index=0),
        ]
    )
    store.delete_by_document("a.pdf")
    results = store.search([0.1] * VECTOR_SIZE, top_k=10)
    doc_ids = {r.payload.document_id for r in results}
    assert doc_ids == {"b.pdf"}


def test_qdrant_store_delete_by_document_does_not_error_when_none_match():
    store = _in_memory_store()
    store.delete_by_document("nonexistent.pdf")


def test_qdrant_store_clear_empties_the_store():
    store = _in_memory_store()
    store.upsert([_make_chunk("id-1", [0.1] * VECTOR_SIZE, "doc.pdf", "text", index=0)])
    store.clear()
    results = store.search([0.1] * VECTOR_SIZE, top_k=10)
    assert results == []


def test_qdrant_store_search_returns_all_payload_fields():
    store = _in_memory_store()
    chunk = _make_chunk(
        "id-x", [0.5] * VECTOR_SIZE, "spec.pdf", "detailed text here", page=7, index=3
    )
    store.upsert([chunk])
    results = store.search([0.5] * VECTOR_SIZE, top_k=1)
    p = results[0].payload
    assert p.document_id == "spec.pdf"
    assert p.chunk_index == 3
    assert p.document_name == "spec.pdf"
    assert p.page == 7
    assert p.text == "detailed text here"


def test_qdrant_store_search_returns_results_in_score_descending_order():
    store = _in_memory_store()
    near = _make_chunk("near", [1.0] + [0.0] * (VECTOR_SIZE - 1), "doc.pdf", "near text", index=0)
    far = _make_chunk("far", [0.0] + [1.0] + [0.0] * (VECTOR_SIZE - 2), "doc.pdf", "far text", index=1)
    store.upsert([far, near])
    query = [1.0] + [0.0] * (VECTOR_SIZE - 1)
    results = store.search(query, top_k=2)
    assert len(results) == 2
    assert results[0].score >= results[1].score
    assert results[0].payload.text == "near text"
