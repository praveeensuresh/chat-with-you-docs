from __future__ import annotations

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from app.cli import app
from app.pipeline.fakes import FakeEmbedder, FakeVectorStore
from app.pipeline.seams import Chunk, ChunkPayload

runner = CliRunner()


def _make_seeded_store(text: str, document_name: str, page: int) -> FakeVectorStore:
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    vector = embedder.embed_passages([text])[0]
    chunk = Chunk(
        id="seed-id-0",
        vector=vector,
        payload=ChunkPayload(
            text=text,
            document_name=document_name,
            page=page,
            document_id=document_name,
            chunk_index=0,
        ),
    )
    store.upsert([chunk])
    return store


# --- ingest command ---


def test_cli_ingest_prints_chunk_count_and_document_name(make_pdf):
    pdf = make_pdf(["hello world " * 50], "report.pdf")
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=FakeVectorStore()
    ):
        result = runner.invoke(app, ["ingest", str(pdf)])
    assert result.exit_code == 0
    assert "report.pdf" in result.output
    assert "Stored" in result.output


def test_cli_ingest_prints_zero_chunks_for_empty_pdf(make_pdf):
    pdf = make_pdf([""], "empty.pdf")
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=FakeVectorStore()
    ):
        result = runner.invoke(app, ["ingest", str(pdf)])
    assert result.exit_code == 0
    assert "0" in result.output
    assert "empty.pdf" in result.output


def test_cli_ingest_missing_pdf_exits_nonzero():
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=FakeVectorStore()
    ):
        result = runner.invoke(app, ["ingest", "/tmp/does_not_exist_at_all.pdf"])
    assert result.exit_code != 0


def test_cli_ingest_non_pdf_file_exits_nonzero(tmp_path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("some text")
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=FakeVectorStore()
    ):
        result = runner.invoke(app, ["ingest", str(txt_file)])
    assert result.exit_code != 0


# --- search command ---


def test_cli_search_prints_hits_with_document_name_page_and_text():
    store = _make_seeded_store("Paris is the capital of France", "report.pdf", page=2)
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=store
    ):
        result = runner.invoke(app, ["search", "capital city"])
    assert result.exit_code == 0
    assert "report.pdf" in result.output
    assert "page 2" in result.output
    assert "Paris is the capital of France" in result.output


def test_cli_search_prints_no_results_message_when_store_is_empty():
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=FakeVectorStore()
    ):
        result = runner.invoke(app, ["search", "anything"])
    assert result.exit_code == 0
    assert "No results" in result.output


def test_cli_search_honors_top_k_flag():
    embedder = FakeEmbedder()
    store = FakeVectorStore()
    for i in range(5):
        text = f"chunk number {i}"
        vector = embedder.embed_passages([text])[0]
        store.upsert(
            [
                Chunk(
                    id=f"id-{i}",
                    vector=vector,
                    payload=ChunkPayload(
                        text=text,
                        document_name="doc.pdf",
                        page=1,
                        document_id="doc.pdf",
                        chunk_index=i,
                    ),
                )
            ]
        )
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=store
    ):
        result = runner.invoke(app, ["search", "chunk", "--top-k", "2"])
    assert result.exit_code == 0
    hit_lines = [line for line in result.output.splitlines() if "[doc.pdf" in line]
    assert len(hit_lines) == 2


# --- reset command ---


def test_cli_reset_prints_confirmation():
    store = FakeVectorStore()
    with patch("app.cli._make_store", return_value=store):
        result = runner.invoke(app, ["reset"])
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()


def test_cli_reset_calls_store_clear():
    store = FakeVectorStore()
    with patch("app.cli._make_store", return_value=store):
        runner.invoke(app, ["reset"])
    assert ("clear",) in store.calls


def test_cli_search_top_k_larger_than_stored_returns_all_hits():
    store = _make_seeded_store("some text about a topic", "doc.pdf", page=1)
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=store
    ):
        result = runner.invoke(app, ["search", "topic", "--top-k", "100"])
    assert result.exit_code == 0
    hit_lines = [line for line in result.output.splitlines() if "[doc.pdf" in line]
    assert len(hit_lines) == 1


def test_cli_search_infrastructure_error_exits_nonzero():
    broken_store = MagicMock()
    broken_store.search.side_effect = RuntimeError("Qdrant unreachable")
    with patch("app.cli._make_embedder", return_value=FakeEmbedder()), patch(
        "app.cli._make_store", return_value=broken_store
    ):
        result = runner.invoke(app, ["search", "anything"])
    assert result.exit_code != 0


def test_cli_reset_infrastructure_error_exits_nonzero():
    broken_store = MagicMock()
    broken_store.clear.side_effect = RuntimeError("Qdrant unreachable")
    with patch("app.cli._make_store", return_value=broken_store):
        result = runner.invoke(app, ["reset"])
    assert result.exit_code != 0
