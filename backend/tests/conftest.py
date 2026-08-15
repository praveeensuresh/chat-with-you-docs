from __future__ import annotations

from pathlib import Path

import pytest


def _build_pdf_bytes(pages: list[str]) -> bytes:
    n = len(pages)
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    buf = bytearray()
    offsets: dict[int, int] = {}

    def w(b: bytes) -> None:
        buf.extend(b)

    def add_obj(num: int, content: str) -> None:
        offsets[num] = len(buf)
        w(f"{num} 0 obj\n{content}\nendobj\n".encode("latin-1"))

    def add_stream_obj(num: int, stream: bytes) -> None:
        offsets[num] = len(buf)
        w(f"{num} 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1"))
        w(stream)
        w(b"\nendstream\nendobj\n")

    w(b"%PDF-1.4\n")
    add_obj(1, "<< /Type /Catalog /Pages 2 0 R >>")
    add_obj(2, f"<< /Type /Pages /Kids [{kids}] /Count {n} >>")

    for i, text in enumerate(pages):
        page_num = 3 + 2 * i
        content_num = 4 + 2 * i
        add_obj(
            page_num,
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_num} 0 R "
                f"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 "
                f"/BaseFont /Helvetica >> >> >> >>"
            ),
        )
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1")
        add_stream_obj(content_num, stream)

    xref_pos = len(buf)
    total_objs = 2 + 2 * n + 1

    w(f"xref\n0 {total_objs}\n".encode())
    w(b"0000000000 65535 f \n")
    for obj_num in range(1, total_objs):
        offset = offsets.get(obj_num, 0)
        w(f"{offset:010d} 00000 n \n".encode())

    w(
        f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )

    return bytes(buf)


@pytest.fixture
def make_pdf(tmp_path: Path):
    counter = [0]

    def _factory(pages: list[str], name: str = "test.pdf") -> Path:
        subdir = tmp_path / str(counter[0])
        subdir.mkdir()
        counter[0] += 1
        path = subdir / name
        path.write_bytes(_build_pdf_bytes(pages))
        return path

    return _factory
