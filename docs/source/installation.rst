Installation
============

From PyPI (core library)
------------------------

.. code-block:: bash

    pip install nupdf

With the optional GUI
---------------------

.. code-block:: bash

    pip install "nupdf[gui]"

From source
-----------

.. code-block:: bash

    git clone https://github.com/LucMiaz/nupdf.git
    cd nupdf
    pip install -e ".[gui]"

Pre-built executables
---------------------

Download the latest release from the
`GitHub Releases page <https://github.com/LucMiaz/nupdf/releases>`_.
Standalone executables are provided for:

- **Windows** (``nuPDF-windows.exe``)
- **Ubuntu Linux** (``nuPDF-ubuntu``)
- **macOS** (``nuPDF-macos``)

No Python installation is required to use these executables.

Building your own executable
----------------------------

Install the dev extras and run PyInstaller:

.. code-block:: bash

    pip install "nupdf[dev]"

    # Single-file executable (slower startup, simpler distribution)
    pyinstaller --onefile --windowed --name="nuPDF" nupdf/gui.py

    # Directory-based build (faster startup)
    pyinstaller --onedir --windowed --name="nuPDF" nupdf/gui.py
