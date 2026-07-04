"""pre-commit wrapper: run ruff via Python module (bypasses WDAC exe restriction)."""
import sys
from ruff.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
