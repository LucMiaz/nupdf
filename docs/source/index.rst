nuPDF
=====

.. image:: https://img.shields.io/github/actions/workflow/status/LucMiaz/nupdf/ci.yml?branch=main&label=tests
   :alt: CI status

.. image:: https://img.shields.io/pypi/pyversions/nupdf
   :alt: Python versions

.. image:: https://img.shields.io/github/license/LucMiaz/nupdf
   :alt: License

**nuPDF** is a lightweight Python utility for merging, rotating and
reordering PDF and image files.  It ships both a clean Python API
(:mod:`nupdf.core`) and an optional PyQt5 desktop GUI (:mod:`nupdf.gui`).

Features
--------

- Merge any number of PDF/image files into a single PDF
- Rotate individual pages or entire documents
- Recto-verso interleaving for duplex scans
- Add PDF bookmarks (outline entries) from file names
- Automatically convert JPEG, PNG, GIF and RAW images to PDF
- Standalone desktop GUI built with PyQt5
- Pre-built executables available for Windows, Ubuntu and macOS

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   usage
   api
