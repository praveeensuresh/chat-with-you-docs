from __future__ import annotations

import uuid
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.pipeline.seams import Chunk, ChunkPayload, Embedder, VectorStore

_INGEST_NS = uuid.UUID("c2b7f1a0-5d9e-4b8c-a3f6-1e2d3c4b5a67")
_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 150


def _chunk_id(document_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(_INGEST_NS, f"{document_id}:{chunk_index}"))


def ingest(
    pdf_path: str | Path,
    embedder: Embedder,
    store: VectorStore,
) -> tuple[int, str]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {pdf_path}")

    document_id = path.name
    document_name = path.name

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=_CHUNK_SIZE,
        chunk_overlap=_CHUNK_OVERLAP,
    )

    reader = PdfReader(path)
    pairs: list[tuple[str, int]] = []
    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for chunk_text in splitter.split_text(page_text):
            if chunk_text.strip():
                pairs.append((chunk_text, page_num))

    store.delete_by_document(document_id)

    if not pairs:
        return 0, document_name

    texts = [text for text, _ in pairs]
    vectors = embedder.embed_passages(texts)

    chunks = [
        Chunk(
            id=_chunk_id(document_id, index),
            vector=vectors[index],
            payload=ChunkPayload(
                text=text,
                document_name=document_name,
                page=page_num,
                document_id=document_id,
                chunk_index=index,
            ),
        )
        for index, (text, page_num) in enumerate(pairs)
    ]

    store.upsert(chunks)
    return len(chunks), document_name
