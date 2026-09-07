"""Chargement et validation des contrats distribués en M4."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


REQUIRED_MANIFEST_FIELDS = {
    "document_id", "revision", "asset_path", "license", "sensitivity",
    "status", "allowed_roles", "checksum_sha256",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path, documents: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_MANIFEST_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Champs absents du manifeste : {sorted(missing)}")
        rows = list(reader)
    ids: set[str] = set()
    for row in rows:
        document_id = row["document_id"]
        if document_id in ids:
            raise ValueError(f"document_id dupliqué : {document_id}")
        ids.add(document_id)
        asset = documents / row["asset_path"]
        if not asset.is_file():
            raise FileNotFoundError(asset)
        if sha256(asset) != row["checksum_sha256"]:
            raise ValueError(f"Checksum invalide : {document_id}")
    return rows


def load_questions(path: Path) -> list[dict]:
    questions: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL invalide ligne {number}") from exc
            if item["split"] == "test" and item["label_visibility"] != "sealed":
                raise ValueError(f"Label test exposé : {item['eval_id']}")
            questions.append(item)
    return questions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--questions", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest, args.documents)
    questions = load_questions(args.questions)
    print(json.dumps({"documents": len(manifest), "questions": len(questions)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
