#!/usr/bin/env python3
"""Promeut atomiquement un manifeste candidat après vérification de son gate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.versioning import load_json, promote  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--current", type=Path, default=Path("artifacts/current.json"))
    parser.add_argument("--history", type=Path, default=Path("artifacts/history"))
    args = parser.parse_args()
    gate = load_json(args.gate)
    if gate.get("status") != "passed":
        raise SystemExit("Promotion refusée : le gate n'est pas passé.")
    release_id = promote(args.candidate, args.current, args.history)
    print(f"Release promue : {release_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
