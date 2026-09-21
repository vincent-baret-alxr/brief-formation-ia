import json

from src.versioning import load_json, promote, rollback


def release(release_id: str) -> dict[str, str]:
    return {
        "release_id": release_id,
        "code_version": f"code-{release_id}",
        "model_version": "model-v1",
        "corpus_version": "corpus-v1",
        "index_version": f"index-{release_id}",
        "prompt_version": "prompt-v1",
        "evaluation_version": "eval-v1",
    }


def write(path, value) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_promotion_and_explicit_rollback(tmp_path) -> None:
    current = tmp_path / "current.json"
    history = tmp_path / "history"
    candidate_v1 = tmp_path / "v1.json"
    candidate_v2 = tmp_path / "v2.json"
    write(candidate_v1, release("v1"))
    write(candidate_v2, release("v2"))

    promote(candidate_v1, current, history)
    promote(candidate_v2, current, history)
    assert load_json(current)["release_id"] == "v2"
    assert (history / "v1.json").is_file()

    rollback(current, history, "v1")
    assert load_json(current)["release_id"] == "v1"
