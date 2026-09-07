from pathlib import Path

from src.data_pipeline.io import file_sha256


def test_file_sha256_known_content(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("diagops\n", encoding="utf-8")
    assert file_sha256(sample) == "38cc32b04546d8571adbe5542929faa4aefef0d904ca62340a55685844f1b64b"
