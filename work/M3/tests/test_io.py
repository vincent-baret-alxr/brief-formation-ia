from pathlib import Path

import pytest

from src.data_pipeline.io import file_sha256, load_sources, source_paths


def test_file_sha256_known_content(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    sample.write_text("diagops\n", encoding="utf-8")
    assert file_sha256(sample) == "38cc32b04546d8571adbe5542929faa4aefef0d904ca62340a55685844f1b64b"


def test_source_paths_cover_the_four_open_sources(tmp_path: Path):
    paths = source_paths(tmp_path)
    assert set(paths) == {"equipment", "events", "maintenance", "sensors"}
    assert paths["sensors"].name == "sensor_readings.csv"


def test_load_sources_reports_missing_files(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_sources(tmp_path)
