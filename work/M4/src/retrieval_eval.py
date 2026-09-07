"""Compare : sans retrieval, lexical, vectoriel, hybride.

Métriques : hit rate documentaire (au moins un `document_id` attendu dans le
contexte *admissible* renvoyé), précision du contexte (part du contexte
admissible qui est effectivement attendue), latence, taille de l'index.
Calculées uniquement sur les 10 questions de calibration répondables
(`answerable=true`) : le hit rate n'a pas de sens sur les 2 questions
volontairement sans preuve, ni sur le split test scellé.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .io_contracts import load_manifest, load_questions
from .retrieval import admissible, rank_lexical
from .vector_retrieval import build_index, rank_hybrid, rank_vector

TOP_K = 3


def load_documents(manifest: list[dict[str, str]], documents_dir: Path) -> list[dict[str, Any]]:
    documents = []
    for row in manifest:
        text = (documents_dir / row["asset_path"]).read_text(encoding="utf-8")
        documents.append({**row, "text": text})
    return documents


def admissible_top_k(ranked: list[dict], role: str, top_k: int = TOP_K) -> list[dict]:
    return [document for document in ranked if admissible(document, role)][:top_k]


def evaluate_strategy(
    name: str,
    rank_fn,
    documents: list[dict[str, Any]],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    answerable = [q for q in questions if q["split"] == "calibration" and q["answerable"]]
    hits = 0
    precisions: list[float] = []
    latencies: list[float] = []

    for question in answerable:
        t0 = time.perf_counter()
        ranked = rank_fn(question["question"], documents)
        context = admissible_top_k(ranked, question["role"])
        latencies.append(time.perf_counter() - t0)

        expected = set(question["expected_document_ids"])
        retrieved_ids = {document["document_id"] for document in context}
        hit = bool(expected & retrieved_ids)
        hits += hit
        precision = len(expected & retrieved_ids) / len(retrieved_ids) if retrieved_ids else 0.0
        precisions.append(precision)

    return {
        "strategy": name,
        "n_questions": len(answerable),
        "hit_rate": round(hits / len(answerable), 4) if answerable else None,
        "mean_context_precision": round(sum(precisions) / len(precisions), 4) if precisions else None,
        "mean_latency_seconds": round(sum(latencies) / len(latencies), 6) if latencies else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--documents", required=True, type=Path)
    parser.add_argument("--questions", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(args.manifest, args.documents)
    questions = load_questions(args.questions)
    documents = load_documents(manifest, args.documents)

    t0 = time.perf_counter()
    embeddings = build_index(documents)
    index_build_seconds = time.perf_counter() - t0
    index_size_bytes = embeddings.nbytes

    def strategy_none(_query, _documents):
        return []

    def strategy_lexical(query, documents):
        return rank_lexical(query, documents, top_k=TOP_K)

    def strategy_vector(query, documents):
        return rank_vector(query, documents, embeddings, top_k=TOP_K)

    def strategy_hybrid(query, documents):
        return rank_hybrid(query, documents, embeddings, top_k=TOP_K)

    results = [
        evaluate_strategy("sans_retrieval", strategy_none, documents, questions),
        evaluate_strategy("lexical", strategy_lexical, documents, questions),
        evaluate_strategy("vectoriel", strategy_vector, documents, questions),
        evaluate_strategy("hybride", strategy_hybrid, documents, questions),
    ]
    for result in results:
        result["index_build_seconds"] = round(index_build_seconds, 4) if result["strategy"] in {
            "vectoriel", "hybride"
        } else None
        result["index_size_bytes"] = index_size_bytes if result["strategy"] in {"vectoriel", "hybride"} else None

    (args.output_dir / "retrieval_comparison.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
