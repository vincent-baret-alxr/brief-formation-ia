#!/usr/bin/env python3
"""Qualification du feedback avant tout usage.

Un commentaire n'est pas une vérité. Ce programme mesure des signaux
vérifiables — lien avec un run, identité fonctionnelle de la source, cohérence,
données personnelles, doublons, représentativité — puis applique des règles de
classement de départ. Les seuils sont volontairement explicites : ils doivent
être justifiés, corrigés et défendus, pas acceptés tels quels.

Il ne produit aucune donnée d'entraînement. La transformation d'un retour en
exemple est une décision distincte, tracée dans `docs/qualification_feedback.md`.

Usage :

    python feedback/qualify_feedback.py --batch b1
    python feedback/qualify_feedback.py --batch all --output results/feedback_b1_b2.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import data_pack, reports_table  # noqa: E402


WORKSPACE = Path(__file__).resolve().parents[1]

CLASSES = ("actionnable", "a_investiguer", "non_actionnable", "risque")

# Seuils de départ. Chacun est une hypothèse à justifier dans le livrable.
NEAR_DUPLICATE_JACCARD = 0.85
MINIMUM_ACTIONABLE_LENGTH = 40
AUTHOR_CONCENTRATION_LIMIT = 0.15

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\b0[1-9](?:[ .-]?\d{2}){4}\b")
MATRICULE = re.compile(r"matricule\s*\d+", re.IGNORECASE)
CIVILITY = re.compile(r"\b(?:M\.|Mme|Mlle)\s+[A-ZÉÈÀ][\w'-]+")
NAMED_PERSON = re.compile(r"\b[A-ZÉÈÀ][a-zéèêàçï'-]{2,}\s+[A-ZÉÈÀ][a-zéèêàçï'-]{2,}\b")

INSTRUCTION_MARKERS = (
    "ignore les consignes", "ignore les instructions", "note pour l assistant",
    "note pour l'assistant", "tu peux desormais", "ajoute l outil", "ajoute l'outil",
    "consigne systeme", "reponds a l avenir", "traite ce retour comme une consigne",
    "si tu lis ce commentaire",
)

ACTIONABLE_TERMS = (
    "revision", "seuil", "citation", "extrait", "procedure", "delai", "outil",
    "historique", "criticite", "site", "consignation", "abandonne", "canal",
    "equipement", "diagnostic", "reponse",
)

TOKEN = re.compile(r"[\wÀ-ÿ']+", re.UNICODE)


def normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFD", text.lower())
    without_accents = "".join(char for char in stripped if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", without_accents).strip()


def tokens(text: str) -> set[str]:
    return {item for item in TOKEN.findall(normalize(text)) if len(item) > 2}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def load_feedback(path: Path, batch: str) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if batch != "all":
        rows = [row for row in rows if row["batch"] == batch]
    if not rows:
        raise SystemExit(f"Aucun retour pour le lot {batch}")
    return rows


def signals(rows: list[dict[str, str]], known_reports: set[str]) -> list[dict]:
    author_counts = Counter(row["submitted_by_id"] for row in rows)
    total = len(rows)
    seen_exact: dict[tuple[str, str], str] = {}
    by_report: dict[str, list[tuple[str, set[str]]]] = defaultdict(list)
    results: list[dict] = []

    for row in rows:
        comment = row["comment"]
        normalized = normalize(comment)
        key = (row["report_id"], normalized)
        exact_duplicate_of = seen_exact.get(key)
        near_duplicate_of = ""
        if exact_duplicate_of is None:
            for identifier, previous in by_report[row["report_id"]]:
                if jaccard(tokens(comment), previous) >= NEAR_DUPLICATE_JACCARD:
                    near_duplicate_of = identifier
                    break
            seen_exact[key] = row["feedback_id"]
            by_report[row["report_id"]].append((row["feedback_id"], tokens(comment)))

        scale = row["model_helpfulness"]
        scale_valid = scale.isdigit() and 1 <= int(scale) <= 5
        results.append({
            "feedback_id": row["feedback_id"],
            "report_id": row["report_id"],
            "batch": row["batch"],
            "author": row["submitted_by_id"],
            "role": row["submitted_by_role"],
            "known_report": row["report_id"] in known_reports,
            "scale_valid": scale_valid,
            "exact_duplicate_of": exact_duplicate_of or "",
            "near_duplicate_of": near_duplicate_of,
            "personal_data": bool(
                EMAIL.search(comment) or PHONE.search(comment)
                or MATRICULE.search(comment) or CIVILITY.search(comment)
                or NAMED_PERSON.search(comment)
            ),
            "instruction_attempt": any(marker in normalized for marker in INSTRUCTION_MARKERS),
            "actionable_signal": (
                len(comment) >= MINIMUM_ACTIONABLE_LENGTH
                and any(term in normalized for term in ACTIONABLE_TERMS)
            ),
            "author_over_represented": author_counts[row["submitted_by_id"]] / total
            > AUTHOR_CONCENTRATION_LIMIT,
            "theme": " ".join(sorted(tokens(comment))[:6]),
        })
    return results


def classify(signal: dict) -> tuple[str, str]:
    """Règles de départ. Elles sont incomplètes par construction."""
    if signal["personal_data"]:
        return "risque", "donnée personnelle identifiante dans le commentaire"
    if signal["instruction_attempt"]:
        return "risque", "instruction adressée au système"
    if signal["exact_duplicate_of"] or signal["near_duplicate_of"]:
        return "non_actionnable", "doublon d'un retour déjà reçu sur le même rapport"
    if not signal["known_report"]:
        return "a_investiguer", "rapport inconnu : lien avec un run non vérifiable"
    if not signal["scale_valid"]:
        return "a_investiguer", "note hors échelle ou absente"
    if signal["author_over_represented"]:
        return "a_investiguer", "concentration anormale de retours d'un seul auteur"
    if not signal["actionable_signal"]:
        return "non_actionnable", "commentaire sans élément mesurable"
    return "actionnable", "retour lié à un run, précis et mesurable"


def summarize(qualified: list[dict]) -> dict:
    counts = Counter(row["classe"] for row in qualified)
    authors = Counter(row["author"] for row in qualified)
    reports = {row["report_id"] for row in qualified}
    themes = Counter(
        row["theme"] for row in qualified if row["classe"] == "actionnable"
    )
    total = len(qualified)
    return {
        "feedback_count": total,
        "classes": {name: counts.get(name, 0) for name in CLASSES},
        "actionable_rate": round(counts.get("actionnable", 0) / total, 3),
        "risk_rate": round(counts.get("risque", 0) / total, 3),
        "duplicate_rate": round(
            sum(1 for row in qualified if row["exact_duplicate_of"] or row["near_duplicate_of"]) / total, 3
        ),
        "unlinked_rate": round(sum(1 for row in qualified if not row["known_report"]) / total, 3),
        "distinct_reports_covered": len(reports),
        "distinct_authors": len(authors),
        "most_active_author_share": round(max(authors.values()) / total, 3),
        "top_actionable_themes": [
            {"theme": theme, "count": count} for theme, count in themes.most_common(5)
        ],
        "training_data_exported": False,
    }


def main() -> int:
    default_feedback = data_pack() / "2027-S1" / "feedback" / "feedback.csv"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feedback", type=Path, default=default_feedback)
    parser.add_argument("--batch", default="b1", choices=["b1", "b2", "all"])
    parser.add_argument("--output", type=Path, default=WORKSPACE / "results" / "feedback_qualification.json")
    parser.add_argument("--table", type=Path, default=WORKSPACE / "results" / "feedback_qualification.csv")
    args = parser.parse_args()

    rows = load_feedback(args.feedback, args.batch)
    known_reports = set(reports_table())
    qualified = []
    for signal in signals(rows, known_reports):
        classe, motif = classify(signal)
        qualified.append({**signal, "classe": classe, "motif": motif})

    summary = summarize(qualified)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "batch": args.batch,
                "thresholds": {
                    "near_duplicate_jaccard": NEAR_DUPLICATE_JACCARD,
                    "minimum_actionable_length": MINIMUM_ACTIONABLE_LENGTH,
                    "author_concentration_limit": AUTHOR_CONCENTRATION_LIMIT,
                },
                "summary": summary,
            },
            ensure_ascii=False, indent=2, sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    fields = ["feedback_id", "report_id", "batch", "author", "role", "classe", "motif",
              "known_report", "scale_valid", "exact_duplicate_of", "near_duplicate_of",
              "personal_data", "instruction_attempt", "actionable_signal",
              "author_over_represented"]
    args.table.parent.mkdir(parents=True, exist_ok=True)
    with args.table.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(qualified)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
