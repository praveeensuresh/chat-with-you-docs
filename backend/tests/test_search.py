from __future__ import annotations

from app.pipeline.fakes import FakeEmbedder, FakeVectorStore
from app.pipeline.seams import Chunk, ChunkPayload
from app.pipeline.search import search


def _make_chunk(text: str, document_name: str, page: int, chunk_index: int) -> Chunk:
    vector = FakeEmbedder().embed_passages([text])[0]
    return Chunk(
        id=f"{document_name}:{chunk_index}",
        vector=vector,
        payload=ChunkPayload(
            text=text,
            document_name=document_name,
            page=page,
            document_id=document_name,
            chunk_index=chunk_index,
        ),
    )


def test_search_embeds_question_as_query():
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    search("what is the capital?", embedder, store)
    assert len(embedder.calls) == 1
    label, text = embedder.calls[0]
    assert label == "query"
    assert text == "what is the capital?"


def test_search_returns_hits_with_all_fields():
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    chunk = _make_chunk("Paris is the capital of France", "report.pdf", page=2, chunk_index=0)
    store.upsert([chunk])
    hits = search("capital city", embedder, store, top_k=1)
    assert len(hits) == 1
    hit = hits[0]
    assert hit.text == "Paris is the capital of France"
    assert hit.document_name == "report.pdf"
    assert hit.page == 2
    assert isinstance(hit.score, float)


def test_search_honours_top_k():
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    chunks = [_make_chunk(f"chunk text {i}", "doc.pdf", page=1, chunk_index=i) for i in range(5)]
    store.upsert(chunks)
    hits = search("some question", embedder, store, top_k=3)
    assert len(hits) == 3


def test_search_top_k_larger_than_store_returns_all():
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    chunks = [_make_chunk(f"chunk text {i}", "doc.pdf", page=1, chunk_index=i) for i in range(2)]
    store.upsert(chunks)
    hits = search("some question", embedder, store, top_k=10)
    assert len(hits) == 2


def test_search_empty_store_returns_empty_list():
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    hits = search("some question", embedder, store)
    assert hits == []


def test_search_returns_hits_in_score_descending_order():
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    chunks = [_make_chunk(f"text about topic {i}", "doc.pdf", page=1, chunk_index=i) for i in range(3)]
    store.upsert(chunks)
    hits = search("text about topic 0", embedder, store, top_k=3)
    assert len(hits) >= 2
    scores = [hit.score for hit in hits]
    assert scores == sorted(scores, reverse=True)
