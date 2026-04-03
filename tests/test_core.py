"""Tests for :mod:`nupdf.core`."""

import pypdf
import pytest

from nupdf.core import merge_pdfs, read_pdf, rotate_pages


# ===========================================================================
# read_pdf
# ===========================================================================

class TestReadPdf:
    """Tests for :func:`nupdf.core.read_pdf`."""

    def test_reads_valid_pdf(self, simple_pdf):
        """read_pdf should return a PdfReader for a valid PDF path."""
        reader = read_pdf(str(simple_pdf))
        assert isinstance(reader, pypdf.PdfReader)

    def test_multi_page_pdf_page_count(self, multi_page_pdf):
        """read_pdf should expose the correct number of pages."""
        reader = read_pdf(str(multi_page_pdf))
        assert len(reader.pages) == 4

    def test_missing_file_raises(self, tmp_path):
        """read_pdf should raise FileNotFoundError for a non-existent path."""
        with pytest.raises(FileNotFoundError):
            read_pdf(str(tmp_path / "nonexistent.pdf"))

    def test_unsupported_extension_raises(self, tmp_path):
        """read_pdf should raise ValueError for unsupported file extensions."""
        bad = tmp_path / "file.xyz"
        bad.write_bytes(b"dummy")
        with pytest.raises(ValueError, match="Cannot open"):
            read_pdf(str(bad))

    def test_png_conversion(self, small_png, tmp_path):
        """read_pdf should accept a PNG path and return a PdfReader."""
        reader = read_pdf(str(small_png))
        assert isinstance(reader, pypdf.PdfReader)

    def test_png_creates_pdf_file(self, small_png, tmp_path):
        """read_pdf on a PNG should save a .pdf file in the same folder."""
        read_pdf(str(small_png))
        expected = small_png.parent / (small_png.name + ".pdf")
        assert expected.exists()


# ===========================================================================
# rotate_pages
# ===========================================================================

class TestRotatePages:
    """Tests for :func:`nupdf.core.rotate_pages`."""

    def test_page_count_preserved(self, simple_pdf, tmp_path):
        """Rotating all pages should keep the same page count."""
        out = tmp_path / "rotated.pdf"
        rotate_pages(str(simple_pdf), str(out), angle=90)
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 1

    def test_partial_rotation_page_count(self, multi_page_pdf, tmp_path):
        """Rotating a subset of pages should keep all pages in the output."""
        out = tmp_path / "partial.pdf"
        rotate_pages(str(multi_page_pdf), str(out), pages=[0, 2], angle=90)
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 4

    def test_angle_normalisation_450(self, simple_pdf, tmp_path):
        """An angle of 450° should normalise to 90° (no error)."""
        out = tmp_path / "norm450.pdf"
        rotate_pages(str(simple_pdf), str(out), angle=450)
        assert out.exists()

    def test_angle_normalisation_negative(self, simple_pdf, tmp_path):
        """An angle of -90° should normalise to 270° (no error)."""
        out = tmp_path / "norm_neg.pdf"
        rotate_pages(str(simple_pdf), str(out), angle=-90)
        assert out.exists()

    def test_zero_angle_identity(self, multi_page_pdf, tmp_path):
        """Rotating by 0° should produce an output file with same page count."""
        out = tmp_path / "zero.pdf"
        rotate_pages(str(multi_page_pdf), str(out), angle=0)
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 4

    def test_output_file_created(self, simple_pdf, tmp_path):
        """rotate_pages should create the saving path file."""
        out = tmp_path / "out.pdf"
        rotate_pages(str(simple_pdf), str(out))
        assert out.exists()


# ===========================================================================
# merge_pdfs
# ===========================================================================

class TestMergePdfs:
    """Tests for :func:`nupdf.core.merge_pdfs`."""

    def test_two_file_total_page_count(self, simple_pdf, multi_page_pdf, tmp_path):
        """Merging a 1-page and a 4-page PDF should produce 5 pages."""
        out = tmp_path / "merged.pdf"
        merge_pdfs(
            [str(simple_pdf), str(multi_page_pdf)],
            str(out),
            recto_verso=False,
            same_file=None,
            bookmark=False,
        )
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 5

    def test_bookmark_adds_outline(self, simple_pdf, multi_page_pdf, tmp_path):
        """When bookmark=True, the output PDF should have outline items."""
        out = tmp_path / "bookmarked.pdf"
        merge_pdfs(
            [str(simple_pdf), str(multi_page_pdf)],
            str(out),
            recto_verso=False,
            same_file=None,
            bookmark=True,
        )
        reader = pypdf.PdfReader(str(out))
        assert len(reader.outline) >= 2

    def test_no_bookmark_no_outline(self, simple_pdf, multi_page_pdf, tmp_path):
        """When bookmark=False, the output PDF should have no outline items."""
        out = tmp_path / "no_bm.pdf"
        merge_pdfs(
            [str(simple_pdf), str(multi_page_pdf)],
            str(out),
            recto_verso=False,
            same_file=None,
            bookmark=False,
        )
        reader = pypdf.PdfReader(str(out))
        assert len(reader.outline) == 0

    def test_empty_list_raises(self, tmp_path):
        """Passing an empty list should raise ValueError."""
        out = tmp_path / "empty.pdf"
        with pytest.raises(ValueError, match="at least one"):
            merge_pdfs([], str(out), recto_verso=False, same_file=None, bookmark=False)

    def test_recto_verso_even(self, multi_page_pdf, tmp_path):
        """recto_verso=True on a 4-page PDF should interleave correctly (4 pages out)."""
        out = tmp_path / "rv_even.pdf"
        merge_pdfs(
            [str(multi_page_pdf)],
            str(out),
            recto_verso=True,
            same_file=None,
            bookmark=False,
        )
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 4

    def test_recto_verso_odd(self, five_page_pdf, tmp_path):
        """recto_verso=True on a 5-page PDF should produce 5 pages out."""
        out = tmp_path / "rv_odd.pdf"
        merge_pdfs(
            [str(five_page_pdf)],
            str(out),
            recto_verso=True,
            same_file=None,
            bookmark=False,
        )
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 5

    def test_bookmark_title_is_stem(self, simple_pdf, tmp_path):
        """Bookmark title should be the file stem (no extension, no directory)."""
        out = tmp_path / "titled.pdf"
        merge_pdfs(
            [str(simple_pdf)],
            str(out),
            recto_verso=False,
            same_file=None,
            bookmark=True,
        )
        reader = pypdf.PdfReader(str(out))
        assert reader.outline  # at least one entry
        title = reader.outline[0].title
        assert title == simple_pdf.stem
