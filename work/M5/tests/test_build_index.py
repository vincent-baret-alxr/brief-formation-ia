import csv

import pytest

from pipelines.build_index import build_index
from src.versioning import sha256


FIELDS = [
    "document_id", "revision", "asset_path", "license", "sensitivity",
    "status", "allowed_roles", "checksum_sha256",
]


def write_manifest(path, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_index_is_content_addressed_and_excludes_inactive_documents(tmp_path) -> None:
    documents = tmp_path / "documents"
    documents.mkdir()
    active = documents / "active.md"
    inactive = documents / "inactive.md"
    active.write_text("procédure active", encoding="utf-8")
    inactive.write_text("ancienne procédure", encoding="utf-8")
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [
        {
            "document_id": "DOC-ACTIVE", "revision": "2", "asset_path": active.name,
            "license": "synthetic", "sensitivity": "internal", "status": "active",
            "allowed_roles": "technicien;auditeur", "checksum_sha256": sha256(active),
        },
        {
            "document_id": "DOC-OLD", "revision": "1", "asset_path": inactive.name,
            "license": "synthetic", "sensitivity": "internal", "status": "superseded",
            "allowed_roles": "technicien", "checksum_sha256": sha256(inactive),
        },
    ])

    result = build_index(manifest, documents)
    assert result["document_count"] == 1
    assert result["documents"][0]["document_id"] == "DOC-ACTIVE"
    assert result["index_version"].startswith("lexical-")


def test_index_rejects_a_checksum_mismatch(tmp_path) -> None:
    documents = tmp_path / "documents"
    documents.mkdir()
    document = documents / "doc.md"
    document.write_text("contenu", encoding="utf-8")
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [{
        "document_id": "DOC-1", "revision": "1", "asset_path": document.name,
        "license": "synthetic", "sensitivity": "internal", "status": "active",
        "allowed_roles": "technicien", "checksum_sha256": "0" * 64,
    }])

    with pytest.raises(ValueError, match="Checksum invalide"):
        build_index(manifest, documents)
