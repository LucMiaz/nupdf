"""nuPDF — PDF and image manipulation library and GUI.

Typical usage
-------------
>>> from nupdf import merge_pdfs, rotate_pages
>>> merge_pdfs(["a.pdf", "b.pdf"], "out.pdf")
>>> rotate_pages("scan.pdf", "rotated.pdf", angle=90)
"""

from nupdf.core import merge_pdfs, read_pdf, rotate_pages

__version__ = "1.0.0"
__all__ = ["merge_pdfs", "read_pdf", "rotate_pages"]
