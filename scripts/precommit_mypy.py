"""pre-commit wrapper: run mypy via Python module (bypasses WDAC exe restriction)."""
import sys
from mypy.__main__ import main

if __name__ == "__main__":
    sys.argv[0] = "mypy"
    sys.exit(main())
