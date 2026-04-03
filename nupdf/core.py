"""Core PDF and image manipulation utilities for nuPDF.

This module provides three public functions:

* :func:`read_pdf`      — open a PDF or convert an image to PDF
* :func:`rotate_pages` — rotate selected pages of a PDF
* :func:`merge_pdfs`   — merge multiple PDFs/images into one PDF

Dependencies: ``pypdf`` for PDF I/O, ``Pillow`` for image conversion.

Example
-------
>>> from nupdf.core import merge_pdfs, rotate_pages
>>> merge_pdfs(["scan_front.pdf", "scan_back.pdf"], "merged.pdf", recto_verso=True)
>>> rotate_pages("merged.pdf", "merged_rotated.pdf", pages=[0], angle=90)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Sequence, Union

from PIL import Image
from pypdf import PdfReader, PdfWriter

# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------
PathLike = Union[str, os.PathLike]


def read_pdf(path: PathLike) -> PdfReader:
    """Open *path* as a :class:`~pypdf.PdfReader`.

    If *path* is not a valid PDF — for example a JPEG, PNG, GIF, or RAW image
    — it is first converted to a single-page PDF saved next to the original
    file (with ``.pdf`` appended to its full name).  The PdfReader for that
    converted file is then returned.

    Parameters
    ----------
    path:
        Path to a PDF or a Pillow-readable image file.

    Returns
    -------
    pypdf.PdfReader
        An open reader for the (possibly converted) PDF.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist on disk.
    ValueError
        If the file cannot be opened as a PDF or as a Pillow image.

    Examples
    --------
    >>> reader = read_pdf("document.pdf")
    >>> print(len(reader.pages))
    3
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # First attempt: open directly as PDF
    try:
        reader = PdfReader(str(path))
        _ = len(reader.pages)  # raises PdfReadError if not valid
        return reader
    except Exception:  # pylint: disable=broad-exception-caught
        pass

    # Second attempt: convert image → PDF via Pillow
    try:
        img = Image.open(path).convert("RGB")
    except Exception as exc:
        raise ValueError(
            f"Cannot open '{path}' as a PDF or as an image: {exc}"
        ) from exc

    pdf_path = path.with_suffix(path.suffix + ".pdf")
    img.save(str(pdf_path))
    return PdfReader(str(pdf_path))


def rotate_pages(
    path: PathLike,
    savingpath: PathLike,
    pages: Optional[Sequence[int]] = None,
    angle: int = 90,
) -> None:
    """Rotate one or more pages of a PDF and write the result to *savingpath*.

    The rotation is **clockwise**.  Only multiples of 90° are supported by the
    PDF specification; non-multiples are rounded down to the nearest 90°.
    Angles outside ``[0, 360)`` are normalised automatically.

    Parameters
    ----------
    path:
        Input PDF or image file.
    savingpath:
        Destination path for the output PDF.  Created or overwritten.
    pages:
        Sequence of **0-indexed** page numbers to rotate.  When *None*
        (the default) every page is rotated.
    angle:
        Clockwise rotation angle in degrees.  Non-multiples of 90 are
        truncated; values outside ``[0, 360)`` are normalised.

    Raises
    ------
    ValueError
        If *path* cannot be opened as a PDF or image.
    FileNotFoundError
        If *path* does not exist.

    Examples
    --------
    Rotate the first page 90° clockwise:

    >>> rotate_pages("input.pdf", "output.pdf", pages=[0], angle=90)

    Rotate all pages 180°:

    >>> rotate_pages("input.pdf", "output.pdf", angle=180)
    """
    # Normalise: snap to nearest 90°, then wrap into [0, 360)
    angle = 90 * int(angle / 90)
    angle = ((angle % 360) + 360) % 360

    reader = read_pdf(path)
    writer = PdfWriter()

    n_pages = len(reader.pages)
    pages_set = set(pages) if pages is not None else set(range(n_pages))

    for i in range(n_pages):
        page = reader.pages[i]
        if i in pages_set:
            page.rotate(angle)
        writer.add_page(page)

    with open(savingpath, "wb") as fh:
        writer.write(fh)


def merge_pdfs(  # pylint: disable=too-many-locals
    pdffiles: Sequence[PathLike],
    savingpath: PathLike,
    recto_verso: bool = False,
    same_file: Optional[bool] = None,
    bookmark: bool = True,
) -> None:
    """Merge multiple PDF/image files into a single output PDF.

    Parameters
    ----------
    pdffiles:
        Ordered list of PDF or image paths to include in the merge.
    savingpath:
        Destination path for the merged PDF.  Created or overwritten.
    recto_verso:
        When *True* the pages of each source file are interleaved in a
        *zipper* pattern: the first half of the document is paired
        page-by-page with the second half.

        **Use-case:** scanning a double-sided document with a single-pass
        scanner.  Scan all front pages into one run (pages 0 … n/2−1),
        flip the paper stack and scan the backs (pages n/2 … n−1).  The
        resulting file has fronts then backs; enable *recto_verso* to
        interleave them into reading order.
    same_file:
        Only meaningful when *recto_verso* is *True*.  Set to *True* when
        the front and back pages are stored in **two separate files** in
        *pdffiles*.  The files are first concatenated normally, then the
        recto-verso interleaving is applied to the combined result.
    bookmark:
        When *True* (default) a named bookmark is added at the first page
        of each source document using the source filename stem as the title.

    Raises
    ------
    ValueError
        If *pdffiles* is empty.

    Examples
    --------
    Simple merge with bookmarks:

    >>> merge_pdfs(["chapter1.pdf", "chapter2.pdf"], "book.pdf")

    Recto-verso from a single combined scan file:

    >>> merge_pdfs(["both_sides.pdf"], "sorted.pdf", recto_verso=True)

    Recto-verso from two separate scan files (fronts then backs):

    >>> merge_pdfs(["fronts.pdf", "backs.pdf"], "sorted.pdf",
    ...            recto_verso=True, same_file=True)
    """
    if not pdffiles:
        raise ValueError("pdffiles must contain at least one entry.")

    # same_file + recto_verso: merge linearly first, then interleave
    if same_file and recto_verso:
        recto_verso = False

    writer = PdfWriter()

    for pdf_path in pdffiles:
        reader = read_pdf(pdf_path)
        n_pages = len(reader.pages)

        if recto_verso:
            mid = (n_pages + 1) // 2
            recto: list[int] = list(range(mid))
            verso: list[int] = list(range(mid, n_pages))
            page_order: list[int] = []
            while recto or verso:
                if recto:
                    page_order.append(recto.pop(0))
                if verso:
                    page_order.append(verso.pop(0))
        else:
            page_order = list(range(n_pages))

        start_page = len(writer.pages)
        for i in page_order:
            writer.add_page(reader.pages[i])

        if bookmark:
            title = Path(pdf_path).stem
            writer.add_outline_item(title, start_page)

    with open(savingpath, "wb") as fh:
        writer.write(fh)

    # Second pass: apply recto-verso interleaving to the combined file
    if same_file:
        merge_pdfs(
            [savingpath],
            savingpath,
            recto_verso=True,
            same_file=False,
            bookmark=bookmark,
        )
