from app.pipeline.fakes import FakeEmbedder, FakeVectorStore
from app.pipeline.seams import VECTOR_SIZE, Chunk, ChunkPayload


def _chunk(point_id: str, vector: list[float], document_id: str, text: str, index: int) -> Chunk:
    payload = ChunkPayload(
        text=text,
        document_name=document_id,
        page=1,
        document_id=document_id,
        chunk_index=index,
    )
    return Chunk(id=point_id, vector=vector, payload=payload)


def _axis_vector(*leading: float) -> list[float]:
    vector = list(leading) + [0.0] * (VECTOR_SIZE - len(leading))
    return vector


def test_fake_embedder_records_operation_and_text():
    embedder = FakeEmbedder()

    passages = embedder.embed_passages(["first piece", "second piece"])
    query = embedder.embed_query("a question")

    assert embedder.calls == [
        ("passage", "first piece"),
        ("passage", "second piece"),
        ("query", "a question"),
    ]
    assert len(passages) == 2
    assert all(len(vector) == VECTOR_SIZE for vector in passages)
    assert len(query) == VECTOR_SIZE


def test_fake_embedder_is_deterministic():
    embedder = FakeEmbedder()

    assert embedder.embed_query("same text") == embedder.embed_query("same text")
    assert embedder.embed_query("one") != embedder.embed_query("two")


def test_fake_store_records_calls():
    store = FakeVectorStore()
    chunk = _chunk("a", _axis_vector(1.0), "doc.pdf", "hello", 0)

    store.upsert([chunk])
    store.search(_axis_vector(1.0), top_k=5)
    store.delete_by_document("doc.pdf")
    store.clear()

    assert store.calls == [
        ("upsert", 1),
        ("search", 5),
        ("delete_by_document", "doc.pdf"),
        ("clear",),
    ]


def test_fake_store_returns_closest_first():
    store = FakeVectorStore()
    near = _chunk("near", _axis_vector(1.0, 0.0), "doc.pdf", "near", 0)
    mid = _chunk("mid", _axis_vector(0.7, 0.7), "doc.pdf", "mid", 1)
    far = _chunk("far", _axis_vector(0.0, 1.0), "doc.pdf", "far", 2)
    store.upsert([far, mid, near])

    results = store.search(_axis_vector(1.0, 0.0), top_k=3)

    assert [result.payload.text for result in results] == ["near", "mid", "far"]
    assert results[0].score >= results[1].score >= results[2].score


def test_fake_store_top_k_larger_than_stored_returns_all():
    store = FakeVectorStore()
    store.upsert([_chunk("only", _axis_vector(1.0), "doc.pdf", "only", 0)])

    results = store.search(_axis_vector(1.0), top_k=10)

    assert len(results) == 1


def test_fake_store_delete_by_document_removes_only_that_document():
    store = FakeVectorStore()
    store.upsert(
        [
            _chunk("a", _axis_vector(1.0), "a.pdf", "text a", 0),
            _chunk("b", _axis_vector(1.0), "b.pdf", "text b", 0),
        ]
    )

    store.delete_by_document("a.pdf")
    results = store.search(_axis_vector(1.0), top_k=10)

    assert [result.payload.document_id for result in results] == ["b.pdf"]
