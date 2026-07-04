"""
SciAgent pre-commit quality check script.
Runs mypy (type check) + bandit (security scan).
ruff is skipped on this machine due to WDAC policy blocking native binaries.
Usage: .venv\Scripts\python.exe scripts\check.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(ROOT / ".venv" / "Scripts" / "python.exe")


def run(name, args):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")
    result = subprocess.run(args, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"  FAILED (exit code {result.returncode})")
        return False
    return True


def main():
    ok = True

    # mypy type check
    ok &= run("mypy (type check)", [
        PYTHON, str(ROOT / "scripts" / "precommit_mypy.py"),
        "--config-file=pyproject.toml",
        "-p", "backend",
    ])

    # bandit security scan
    ok &= run("bandit (security)", [
        PYTHON, str(ROOT / "scripts" / "precommit_bandit.py"),
        "-c", "pyproject.toml",
        "-r", "backend/",
        "-x", "backend/tests",
    ])

    print(f"\n  ruff (lint+format) — skipped: WDAC blocks native binary on this machine")

    if not ok:
        print("\nSome checks FAILED. Fix before committing.")
        sys.exit(1)
    print("\nAll checks PASSED.")


if __name__ == "__main__":
    main()
