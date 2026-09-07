"""Réponses citées et traces de l'agent pour les 12 questions de calibration.

Les réponses sont composées à partir des extraits réels des documents admis
(voir `results/retrieval_comparison.json` pour la preuve de récupération).
Ce module ne répond PAS aux questions du split `test` (labels scellés) : il
les fait seulement passer par le même pipeline (agent + retrieval) pour
produire des traces, sans évaluation contre un score attendu.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .bounded_agent import decide
from .contracts import Citation, GroundedAnswer
from .grounded_answer import abstain, validate_citations
from .io_contracts import load_manifest, load_questions
from .retrieval_eval import admissible_top_k, load_documents
from .vector_retrieval import build_index, rank_hybrid

# Réponses composées manuellement à partir des extraits admissibles retrouvés
# par le retrieval hybride (stratégie retenue, voir docs/benchmark_retrieval.md).
# Clé : eval_id. Une entrée absente pour un eval_id de calibration signale un
# oubli détecté par les tests (`tests/test_rag_answers.py`).
CALIBRATION_ANSWERS: dict[str, GroundedAnswer] = {
    "RAG-CAL-001": GroundedAnswer(
        answer=(
            "La révision 2 s'applique. Ses cinq étapes : 1) identifier "
            "l'équipement et confirmer l'ordre de travail ; 2) arrêter "
            "l'équipement depuis son pupitre ; 3) isoler toutes les sources "
            "d'énergie identifiées sur la fiche équipement ; 4) poser les "
            "dispositifs de consignation nominatifs et vérifier l'absence "
            "d'énergie selon la procédure locale ; 5) inscrire l'intervention "
            "au registre avant le début des travaux."
        ),
        citations=(
            Citation(
                "DOC-LOTO-002",
                "Séquence pédagogique : 1. Identifier l'équipement... 5. "
                "Inscrire l'intervention au registre avant le début des travaux.",
            ),
        ),
        interpretation="La révision 1 (DOC-LOTO-001) est remplacée ; elle n'est plus admissible.",
    ),
    "RAG-CAL-002": GroundedAnswer(
        answer=(
            "Pour un équipement de criticité high ou critical, une seconde "
            "personne habilitée vérifie l'identification de l'équipement et "
            "les points d'isolement, en plus de la séquence standard."
        ),
        citations=(
            Citation(
                "DOC-LOTO-002",
                "Pour un équipement de criticité high ou critical, une seconde "
                "personne habilitée vérifie l'identification de l'équipement "
                "et les points d'isolement.",
            ),
        ),
    ),
    "RAG-CAL-003": GroundedAnswer(
        answer="À partir de 4,5 mm/s sur trois mesures consécutives, une revue humaine prioritaire est déclenchée.",
        citations=(
            Citation(
                "DOC-PUMP-VIB-001",
                "Une vibration supérieure ou égale à 4,5 mm/s sur trois "
                "mesures consécutives déclenche une revue humaine prioritaire.",
            ),
        ),
        interpretation="Seuil pédagogique DiagOps, pas un seuil industriel réel (rappel explicite du document).",
    ),
    "RAG-CAL-004": GroundedAnswer(
        answer="Non : si le capteur est figé, l'assistant refuse le diagnostic automatique.",
        citations=(
            Citation(
                "DOC-PUMP-VIB-001",
                "Si le capteur est figé, si l'unité est incohérente ou si la "
                "série comporte un trou de plus de 24 heures, l'assistant "
                "refuse le diagnostic automatique.",
            ),
        ),
    ),
    "RAG-CAL-005": GroundedAnswer(
        answer=(
            "Une revue humaine du circuit de refroidissement est déclenchée. "
            "Au-delà de 85 °C, DiagOps classe la situation comme urgente, "
            "mais ne commande aucun arrêt."
        ),
        citations=(
            Citation(
                "DOC-CHILL-TEMP-001",
                "Une température supérieure à 75 °C pendant au moins dix "
                "minutes conduit à une revue humaine du circuit de "
                "refroidissement.",
            ),
        ),
        interpretation="Vérifier au préalable l'unité (°C, pas kelvin) avant d'appliquer ce seuil (rappel du document).",
    ),
    "RAG-CAL-006": GroundedAnswer(
        answer="En l'absence de valeur nominale fiable, DiagOps s'abstient : aucun diagnostic de surcharge n'est produit.",
        citations=(
            Citation(
                "DOC-CONV-CURRENT-001",
                "En l'absence de valeur nominale fiable, DiagOps s'abstient.",
            ),
        ),
    ),
    "RAG-CAL-007": GroundedAnswer(
        answer=(
            "Non. La comparaison n'est valable que si l'unité est le bar ; "
            "une mesure en kPa doit être normalisée (divisée par 100) avant "
            "toute comparaison au seuil."
        ),
        citations=(
            Citation(
                "DOC-STEAM-PRESS-001",
                "Si les mesures sont exprimées en kPa, elles doivent être "
                "normalisées avant la comparaison.",
            ),
        ),
    ),
    "RAG-CAL-008": GroundedAnswer(
        answer=(
            "Cette demande ne peut pas être satisfaite : un utilisateur "
            "public n'a accès à aucun document restreint, et le système "
            "explique la règle d'accès sans reproduire la donnée protégée."
        ),
        citations=(
            Citation(
                "DOC-RAG-OPS-001",
                "Le système s'abstient... lorsqu'un document est hors des "
                "droits du rôle demandeur.",
            ),
        ),
        interpretation=(
            "DOC-DATA-ACCESS-001 porte la règle d'accès elle-même mais est "
            "sensibilité restreinte (rôles superviseur;auditeur) : il n'est "
            "pas admissible pour le rôle public de cette question et n'est "
            "donc pas cité, conformément au contrôle d'accès."
        ),
    ),
    "RAG-CAL-009": GroundedAnswer(
        answer="L'agent M4 choisit une seule action parmi : answer_without_tool, search_knowledge, abstain.",
        citations=(
            Citation(
                "DOC-RAG-OPS-001",
                "L'agent M4 choisit uniquement entre réponse directe, "
                "recherche documentaire et abstention.",
            ),
        ),
    ),
    "RAG-CAL-010": GroundedAnswer(
        answer=(
            "Non : la révision 1 est remplacée par la révision 2, qui seule "
            "est active. La révision 1 est conservée dans le corpus "
            "uniquement pour tester la gestion des révisions et ne doit pas "
            "fonder une recommandation."
        ),
        citations=(
            Citation(
                "DOC-LOTO-002",
                "Statut : active. Remplace DOC-LOTO-001.",
            ),
        ),
        interpretation="Conflit de révision signalé plutôt que masqué : la révision 1 existe mais n'est plus valide.",
    ),
    "RAG-CAL-011": abstain(
        "Aucune source admissible ne précise de marque de lubrifiant pour "
        "cet équipement : le corpus documentaire ne couvre pas cette "
        "information (question hors périmètre des preuves disponibles)."
    ),
    "RAG-CAL-012": abstain(
        "Aucune source ne permet de dater une panne future : conformément à "
        "DOC-PUMP-VIB-001, le système ne prédit pas de panne future à partir "
        "de seuils de triage, et aucun document n'affirme de date."
    ),
}

ADMISSIBLE_DOCUMENT_IDS_BY_ROLE_CACHE: dict[str, set[str]] = {}


def build_evaluation(
    questions: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    embeddings,
) -> list[dict[str, Any]]:
    records = []
    for question in questions:
        eval_id = question["eval_id"]
        ranked = rank_hybrid(question["question"], documents, embeddings, top_k=3)
        context = admissible_top_k(ranked, question["role"])
        admissible_ids = {document["document_id"] for document in context}

        agent_decision = decide(
            needs_documents=True,
            answerable_without_tool=False,
            query=question["question"],
        )

        record: dict[str, Any] = {
            "eval_id": eval_id,
            "split": question["split"],
            "role": question["role"],
            "admissible_context": sorted(admissible_ids),
            "agent_decision": {
                "action": agent_decision.action,
                "rationale": agent_decision.rationale,
                "retrieval_query": agent_decision.retrieval_query,
            },
        }

        if question["split"] == "calibration":
            answer = CALIBRATION_ANSWERS[eval_id]
            errors = validate_citations(answer, admissible_ids)
            cited_ids = {citation.document_id for citation in answer.citations}
            expected = set(question["expected_document_ids"])
            record.update(
                {
                    "abstained": answer.abstained,
                    "expected_abstain": not question["answerable"],
                    "abstain_matches_expectation": answer.abstained == (not question["answerable"]),
                    "cited_document_ids": sorted(cited_ids),
                    "expected_document_ids": sorted(expected),
                    "citation_hit": bool(cited_ids & expected) if expected else answer.abstained,
                    "contract_errors": errors,
                }
            )
        else:
            record["note"] = "split test scellé : trace produite, aucune évaluation de score."

        records.append(record)
    return records


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
    embeddings = build_index(documents)

    records = build_evaluation(questions, documents, embeddings)
    (args.output_dir / "agent_traces.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    calibration = [r for r in records if r["split"] == "calibration"]
    summary = {
        "n_calibration_questions": len(calibration),
        "abstain_matches_expectation_rate": round(
            sum(r["abstain_matches_expectation"] for r in calibration) / len(calibration), 4
        ),
        "citation_hit_rate": round(sum(r["citation_hit"] for r in calibration) / len(calibration), 4),
        "contract_errors_total": sum(len(r["contract_errors"]) for r in calibration),
    }
    (args.output_dir / "grounded_answer_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
