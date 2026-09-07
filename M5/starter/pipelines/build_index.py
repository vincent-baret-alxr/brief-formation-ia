#!/usr/bin/env python3
"""Construit hors ligne un index lexical versionné sans écraser le slot sain."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.versioning import atomic_write_json, sha256  # noqa: E402


TOKEN = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)
REQUIRED_FIELDS = {
    "document_id", "revision", "asset_path", "license", "sensitivity",
    "status", "allowed_roles", "checksum_sha256",
}


def build_index(manifest_path: Path, documents: Path) -> dict:
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Champs absents du manifeste : {sorted(missing)}")
        rows = list(reader)

    indexed: list[dict] = []
    seen: set[str] = set()
    for row in rows:
        document_id = row["document_id"]
        if document_id in seen:
            raise ValueError(f"document_id dupliqué : {document_id}")
        seen.add(document_id)
        asset = documents / row["asset_path"]
        if not asset.is_file():
            raise FileNotFoundError(asset)
        actual = sha256(asset)
        if actual != row["checksum_sha256"]:
            raise ValueError(f"Checksum invalide : {document_id}")
        if row["status"] != "active":
            continue
        text = asset.read_text(encoding="utf-8")
        indexed.append({
            "document_id": document_id,
            "revision": row["revision"],
            "checksum_sha256": actual,
            "allowed_roles": sorted(filter(None, row["allowed_roles"].split(";"))),
            "token_count": len(TOKEN.findall(text)),
        })

    fingerprint_input = "\n".join(
        f"{item['document_id']}:{item['revision']}:{item['checksum_sha256']}"
        for item in sorted(indexed, key=lambda item: item["document_id"])
    )
    fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()
    return {
        "schema_version": 1,
        "index_version": f"lexical-{fingerprint[:12]}",
        "manifest_sha256": sha256(manifest_path),
        "document_count": len(indexed),
        "documents": indexed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_index(args.manifest, args.documents)
    atomic_write_json(args.output, result)
    print(f"Index écrit : {args.output} ({result['document_count']} documents)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
