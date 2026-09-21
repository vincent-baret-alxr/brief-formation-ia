#!/usr/bin/env python3
"""Restaure explicitement une release archivée, sans sélection implicite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.versioning import rollback  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_id")
    parser.add_argument("--current", type=Path, default=Path("artifacts/current.json"))
    parser.add_argument("--history", type=Path, default=Path("artifacts/history"))
    args = parser.parse_args()
    restored = rollback(args.current, args.history, args.release_id)
    print(f"Release restaurée : {restored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
