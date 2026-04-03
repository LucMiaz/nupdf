"""pytest fixtures shared across all nuPDF test modules."""

import io
import pytest

# ---------------------------------------------------------------------------
# PDF helpers (no external PDF files required)
# ---------------------------------------------------------------------------

def _make_minimal_pdf(num_pages: int = 1) -> bytes:
    """Return the raw bytes of a minimal valid PDF with *num_pages* pages."""
    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")

    # Object layout:
    #   1 = Catalog  (/Pages 2 0 R)
    #   2 = Pages    (/Kids [3 0 R … ] /Count num_pages)
    #   3 … 2+num_pages = Page objects  (/Parent 2 0 R)

    page_obj_nums = list(range(3, 3 + num_pages))
    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)

    all_objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>".encode(),
    ] + [b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>"] * num_pages

    offsets: list[int] = []
    for i, obj_content in enumerate(all_objects, start=1):
        offsets.append(buf.tell())
        buf.write(f"{i} 0 obj\n".encode())
        buf.write(obj_content)
        buf.write(b"\nendobj\n")

    xref_offset = buf.tell()
    total = len(all_objects)
    buf.write(b"xref\n")
    buf.write(f"0 {total + 1}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for offset in offsets:
        buf.write(f"{offset:010d} 00000 n \n".encode())
    buf.write(
        f"trailer\n<< /Size {total + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return buf.getvalue()


@pytest.fixture()
def simple_pdf(tmp_path):
    """A temporary 1-page PDF file."""
    p = tmp_path / "simple.pdf"
    p.write_bytes(_make_minimal_pdf(1))
    return p


@pytest.fixture()
def multi_page_pdf(tmp_path):
    """A temporary 4-page PDF file."""
    p = tmp_path / "multi.pdf"
    p.write_bytes(_make_minimal_pdf(4))
    return p


@pytest.fixture()
def five_page_pdf(tmp_path):
    """A temporary 5-page PDF file (odd page count for recto-verso tests)."""
    p = tmp_path / "five.pdf"
    p.write_bytes(_make_minimal_pdf(5))
    return p


@pytest.fixture()
def small_png(tmp_path):
    """A temporary 1×1 white PNG file."""
    from PIL import Image  # optional; skip if not installed
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    p = tmp_path / "pixel.png"
    img.save(str(p))
    return p
