from __future__ import annotations

import pytest

from app.pipeline.fakes import FakeEmbedder, FakeVectorStore
from app.pipeline.ingest import ingest


def test_ingest_basic_chunk_metadata(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    pdf = make_pdf(["Simple page text."], name="report.pdf")
    count, name = ingest(pdf, embedder, store)

    assert name == "report.pdf"
    assert count >= 1
    assert count == len(store.points)

    stored = sorted(store.points.values(), key=lambda c: c.payload.chunk_index)
    assert stored[0].payload.document_name == "report.pdf"
    assert stored[0].payload.document_id == "report.pdf"
    assert stored[0].payload.page == 1
    assert stored[0].payload.chunk_index == 0


def test_chunk_index_is_document_wide_and_zero_based(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    page1_text = "word " * 200
    pdf = make_pdf([page1_text, "Second page text."], name="doc.pdf")
    ingest(pdf, embedder, store)

    indices = sorted(c.payload.chunk_index for c in store.points.values())
    assert indices == list(range(len(store.points)))


def test_chunk_respects_size_and_page_boundary(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    page1 = "word " * 200
    page2 = "thing " * 200
    pdf = make_pdf([page1, page2], name="two.pdf")
    ingest(pdf, embedder, store)

    chunks = list(store.points.values())
    assert len(chunks) >= 2

    for chunk in chunks:
        assert len(chunk.payload.text) <= 800
        assert chunk.payload.page in (1, 2)

    pages_seen = {c.payload.page for c in chunks}
    assert 1 in pages_seen
    assert 2 in pages_seen


def test_ingest_uses_passage_label_for_all_text(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    pdf = make_pdf(["Some text on this page."])
    ingest(pdf, embedder, store)

    assert len(embedder.calls) >= 1
    assert all(label == "passage" for label, _ in embedder.calls)


def test_reingest_same_file_does_not_double_chunks(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    pdf = make_pdf(["Page text here."])
    count1, _ = ingest(pdf, embedder, store)
    count2, _ = ingest(pdf, embedder, store)

    assert count1 == count2
    assert len(store.points) == count2


def test_reingest_shorter_file_removes_old_chunks(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    long_text = "word " * 200
    pdf_long = make_pdf([long_text], name="doc.pdf")
    count1, _ = ingest(pdf_long, embedder, store)
    assert count1 >= 2

    pdf_short = make_pdf(["Short."], name="doc.pdf")
    count2, _ = ingest(pdf_short, embedder, store)

    assert count2 < count1
    assert len(store.points) == count2


def test_no_text_page_produces_no_chunks(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    pdf = make_pdf([""])
    count, _ = ingest(pdf, embedder, store)

    assert count == 0
    assert len(store.points) == 0


def test_no_text_reingest_clears_old_chunks(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    pdf_with_text = make_pdf(["Some real content."], name="doc.pdf")
    count1, _ = ingest(pdf_with_text, embedder, store)
    assert count1 >= 1

    pdf_empty = make_pdf([""], name="doc.pdf")
    count2, _ = ingest(pdf_empty, embedder, store)

    assert count2 == 0
    assert len(store.points) == 0

def test_missing_file_raises_before_any_store_op():
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    with pytest.raises(FileNotFoundError):
        ingest("/tmp/does_not_exist_xyz.pdf", embedder, store)

    assert store.calls == []


def test_non_pdf_file_raises_before_any_store_op(tmp_path):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("some text")

    with pytest.raises(ValueError):
        ingest(txt_file, embedder, store)

    assert store.calls == []


def test_ingest_returns_chunk_count_and_document_name(make_pdf):
    embedder = FakeEmbedder()
    store = FakeVectorStore()

    pdf = make_pdf(["Hello world."], name="my_report.pdf")
    count, name = ingest(pdf, embedder, store)

    assert isinstance(count, int)
    assert name == "my_report.pdf"
    assert count == len(store.points)
