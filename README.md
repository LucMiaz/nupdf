# nuPDF

[![CI](https://img.shields.io/github/actions/workflow/status/LucMiaz/nupdf/ci.yml?branch=main&label=tests)](https://github.com/LucMiaz/nupdf/actions)
[![Python](https://img.shields.io/pypi/pyversions/nupdf)](https://pypi.org/project/nupdf/)
[![License](https://img.shields.io/github/license/LucMiaz/nupdf)](LICENSE)
[![Docs](https://nupdf.readthedocs.io/en/latest/)](https://nupdf.readthedocs.io)

**nuPDF** merges, rotates and reorders PDF and image files.  
The module can be used via Python API or aa optional PyQt5 desktop Graphical User Interface (GUI). The GUI is available under *Releases* on this page, on the right panel.

---

## Features

| Feature | Description |
|---|---|
| Merge | Combine any number of PDF/image files into a single PDF |
| Rotate | Rotate individual pages or entire documents |
| Recto-verso | Interleave pages for duplex scanner output |
| Bookmarks | Add PDF outline entries named after the source files |
| Image support | Auto-convert JPEG, PNG, GIF and RAW to PDF via Pillow |
| GUI | Optional PyQt5 desktop interface |
| Executables | Pre-built binaries for Windows, Ubuntu and macOS |

---

## Installation

```bash
# Core library only
pip install nupdf

# With the optional GUI
pip install "nupdf[gui]"
```

---

## Quick start — Python API

```python
from nupdf.core import read_pdf, rotate_pages, merge_pdfs

# Open a PDF (or convert an image on the fly)
reader = read_pdf("scan.jpg")
print(f"Pages: {len(reader.pages)}")

# Rotate all pages 90° clockwise
rotate_pages("input.pdf", "rotated.pdf", angle=90)

# Rotate only pages 0 and 2 (0-indexed) by 180°
rotate_pages("input.pdf", "rotated.pdf", pages=[0, 2], angle=180)

# Merge two files (with PDF bookmarks)
merge_pdfs(
    ["report.pdf", "appendix.pdf"],
    "combined.pdf",
    recto_verso=False,
    same_file=None,
    bookmark=True,
)
```

### Recto-verso interleaving

Duplex scanners often output fronts and backs as separate files.
`merge_pdfs` can interleave them in the correct reading order:

```python
# Fronts and backs in separate files
merge_pdfs(
    ["fronts.pdf", "backs.pdf"],
    "interleaved.pdf",
    recto_verso=True,
    same_file=True,
)

# All pages in one file (fronts in first half, backs in second half)
merge_pdfs(
    ["both_sides.pdf"],
    "interleaved.pdf",
    recto_verso=True,
    same_file=None,
)
```

---

## GUI

Launch the graphical interface:

```bash
# From source
nupdf

# Or run directly
python -m nupdf.gui
```

```
┌─────────────────────────────────────┐
│  nuPDF                              │
│                                     │
│  [Insert files]  [Insert folder]    │
│                                     │
│  ☑ Merge multiple files?            │
│  ☑ Add bookmarks using file title?  │
│  ☐ Recto verso?                     │
│  ☐ Fronts and backs separate?       │
│                                     │
│  Rotation angle (°): [  0  ]        │
│  Pages to rotate:    [     ]        │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ /path/to/file1.pdf            │  │
│  │ /path/to/file2.pdf            │  │
│  └───────────────────────────────┘  │
│  [Up]  [Down]                       │
│                                     │
│  [Clear files list]                 │
│  [Select saving path]               │
│  saving/path/output.pdf             │
│                                     │
│  [          Start          ]        │
│                                     │
│  Status: Ready                      │
└─────────────────────────────────────┘
```

### Page-range syntax

| Input | Pages selected (1-indexed) |
|---|---|
| `3` | Page 3 |
| `1-4` | Pages 1, 2, 3, 4 |
| `1-3;5` | Pages 1, 2, 3, 5 |
| `2;4-6;9` | Pages 2, 4, 5, 6, 9 |
| *(empty)* | All pages |

### Supported input formats

| Extension | Notes |
|---|---|
| `.pdf` | Native; no conversion needed |
| `.jpg` / `.jpeg` | Converted to PDF via Pillow |
| `.png` | Converted to PDF via Pillow |
| `.gif` | Converted to PDF via Pillow |
| `.raw` | Converted to PDF via Pillow |

---

## Project structure

```
nupdf/
├── nupdf/
│   ├── __init__.py      # Public API surface
│   ├── core.py          # PDF/image manipulation logic
│   └── gui.py           # PyQt5 desktop interface
├── tests/
│   ├── conftest.py      # pytest fixtures
│   └── test_core.py     # Unit tests for core module
├── docs/
│   └── source/          # Sphinx documentation
├── .github/workflows/
│   ├── ci.yml           # pytest + pylint on push/PR
│   └── release.yml      # PyInstaller binaries on version tag
├── rotatepdf.py         # Backward-compatibility shim
└── pyproject.toml
```

---

## Development

```bash
git clone https://github.com/youruser/nupdf.git
cd nupdf
pip install -e ".[gui,dev]"

# Run tests
pytest

# Lint
pylint nupdf/core.py
pylint nupdf/gui.py --disable=import-error

# Build docs
cd docs && make html
```

### Creating a release

Tag a commit with a version number to trigger the automated release workflow:

```bash
git tag v1.2.3
git push origin v1.2.3
```

GitHub Actions will build standalone executables for Windows, Ubuntu and
macOS and attach them to a new GitHub Release automatically.

---

## License

MIT — see [LICENSE](LICENSE).
