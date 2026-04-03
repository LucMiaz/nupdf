Usage
=====

Python API
----------

Reading a file
~~~~~~~~~~~~~~

:func:`nupdf.core.read_pdf` opens a PDF or converts a supported image format
(JPEG, PNG, GIF, RAW) to PDF on the fly.

.. code-block:: python

    from nupdf.core import read_pdf

    reader = read_pdf("document.pdf")
    print(f"Pages: {len(reader.pages)}")

    # Works with images too — saves document.pdf.pdf alongside the image
    reader = read_pdf("scan.jpg")

Rotating pages
~~~~~~~~~~~~~~

:func:`nupdf.core.rotate_pages` rotates all or a subset of pages.

.. code-block:: python

    from nupdf.core import rotate_pages

    # Rotate all pages 90° clockwise
    rotate_pages("input.pdf", "output.pdf", angle=90)

    # Rotate only pages 0 and 2 (0-indexed) by 180°
    rotate_pages("input.pdf", "output.pdf", pages=[0, 2], angle=180)

Merging files
~~~~~~~~~~~~~

:func:`nupdf.core.merge_pdfs` combines several PDF/image files.

.. code-block:: python

    from nupdf.core import merge_pdfs

    merge_pdfs(
        ["front.pdf", "back.pdf"],
        "merged.pdf",
        recto_verso=False,
        same_file=None,
        bookmark=True,
    )

Recto-verso interleaving
~~~~~~~~~~~~~~~~~~~~~~~~

If you have a duplex scanner that outputs fronts and backs in separate files:

.. code-block:: python

    merge_pdfs(
        ["fronts.pdf", "backs.pdf"],
        "interleaved.pdf",
        recto_verso=True,
        same_file=True,   # fronts and backs are separate files
        bookmark=False,
    )

If all pages are in a single file (fronts in the first half, backs in the
second):

.. code-block:: python

    merge_pdfs(
        ["both_sides.pdf"],
        "interleaved.pdf",
        recto_verso=True,
        same_file=None,
        bookmark=False,
    )

Page-range syntax (GUI)
-----------------------

When entering pages in the GUI input field, use the following syntax:

+-------------------+-------------------------------+
| Input             | Pages selected (1-indexed)    |
+===================+===============================+
| ``3``             | Page 3                        |
+-------------------+-------------------------------+
| ``1-4``           | Pages 1, 2, 3, 4              |
+-------------------+-------------------------------+
| ``1-3;5``         | Pages 1, 2, 3, 5              |
+-------------------+-------------------------------+
| ``2;4-6;9``       | Pages 2, 4, 5, 6, 9           |
+-------------------+-------------------------------+
| *(empty)*         | All pages                     |
+-------------------+-------------------------------+

Supported input formats
-----------------------

+---------------------+------------------------------------------+
| Extension(s)        | Notes                                    |
+=====================+==========================================+
| ``.pdf``            | Native; no conversion needed             |
+---------------------+------------------------------------------+
| ``.jpg`` / ``.jpeg``| Converted to PDF via Pillow              |
+---------------------+------------------------------------------+
| ``.png``            | Converted to PDF via Pillow              |
+---------------------+------------------------------------------+
| ``.gif``            | Converted to PDF via Pillow              |
+---------------------+------------------------------------------+
| ``.raw``            | Converted to PDF via Pillow              |
+---------------------+------------------------------------------+

GUI controls
------------

+-----------------------+--------------------------------------------------+
| Control               | Description                                      |
+=======================+==================================================+
| Insert files          | Open a multi-file dialog                         |
+-----------------------+--------------------------------------------------+
| Insert folder         | Recursively add all supported files in a tree    |
+-----------------------+--------------------------------------------------+
| Up / Down             | Reorder the selected files                       |
+-----------------------+--------------------------------------------------+
| Merge multiple files? | Combine all listed files into one PDF            |
+-----------------------+--------------------------------------------------+
| Add bookmarks         | Insert PDF outline entries named after files     |
+-----------------------+--------------------------------------------------+
| Recto verso?          | Interleave pages for duplex scans                |
+-----------------------+--------------------------------------------------+
| Fronts/backs separate | Fronts and backs are in distinct files           |
+-----------------------+--------------------------------------------------+
| Rotation angle        | Clockwise degrees (e.g. 90, 180, 270)            |
+-----------------------+--------------------------------------------------+
| Pages to rotate       | Page-range string; empty = rotate all            |
+-----------------------+--------------------------------------------------+
| Select saving path    | Choose where to write the output PDF             |
+-----------------------+--------------------------------------------------+
| Start                 | Execute the operation                            |
+-----------------------+--------------------------------------------------+
