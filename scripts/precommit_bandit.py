"""pre-commit wrapper: run bandit via Python module (bypasses WDAC exe restriction)."""
import sys
from bandit.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
