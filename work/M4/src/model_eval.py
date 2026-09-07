"""Comparaison de modèles simples à la baseline M3 sur la cible de provenance.

Cible : `provenance` (`réelle` / `fabriquée`) d'une fenêtre de 30 mesures
(`window_id`), PAS une anomalie de qualité ni une panne future (brief M4,
axe 1). Protocole : validation croisée groupée par `equipment_id` sur les 30
fenêtres de calibration (aucune fenêtre de test n'entre dans ce module), afin
qu'un même équipement ne se retrouve jamais à la fois en apprentissage et en
validation interne d'un même pli.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

from .features import build_feature_table

NUMERIC_FEATURES = [
    "value_mean",
    "value_std",
    "missing_share",
    "unit_mismatch_share",
    "sentinel_share",
    "off_grid_share",
    "high_precision_share",
    "unreadable_timestamp_share",
]
CATEGORICAL_FEATURES = ["sensor_name"]
POSITIVE_LABEL = "fabriquée"

SEED = 42
N_SPLITS = 5


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_matrix(table: list[dict[str, Any]]):
    x = [{**{k: row[k] for k in NUMERIC_FEATURES}, **{k: row[k] for k in CATEGORICAL_FEATURES}} for row in table]
    groups = np.array([row["equipment_id"] for row in table])
    window_ids = [row["window_id"] for row in table]
    y = None
    if "provenance" in table[0]:
        y = np.array([1 if row["provenance"] == POSITIVE_LABEL else 0 for row in table])
    return x, y, groups, window_ids


def make_pipeline(estimator) -> Pipeline:
    preprocess = ColumnTransformer(
        [
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline([("preprocess", preprocess), ("model", estimator)])


def to_frame(x: list[dict[str, Any]]):
    import pandas as pd

    return pd.DataFrame(x)


CANDIDATES = {
    "logistic_regression": lambda: LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=SEED
    ),
    "random_forest": lambda: RandomForestClassifier(
        n_estimators=200, max_depth=4, class_weight="balanced", random_state=SEED
    ),
}


def cross_validate(
    name: str, x_df, y: np.ndarray, groups: np.ndarray, window_ids: list[str]
) -> tuple[dict[str, Any], dict[str, int]]:
    splitter = GroupKFold(n_splits=min(N_SPLITS, len(set(groups))))
    y_true_all: list[int] = []
    y_pred_all: list[int] = []
    y_score_all: list[float] = []
    fold_recalls: list[float] = []
    fit_times: list[float] = []
    predict_times: list[float] = []
    out_of_fold_predictions: dict[str, int] = {}

    for train_idx, test_idx in splitter.split(x_df, y, groups):
        pipeline = make_pipeline(CANDIDATES[name]())
        t0 = time.perf_counter()
        pipeline.fit(x_df.iloc[train_idx], y[train_idx])
        fit_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        pred = pipeline.predict(x_df.iloc[test_idx])
        predict_times.append(time.perf_counter() - t0)

        if hasattr(pipeline, "predict_proba"):
            score = pipeline.predict_proba(x_df.iloc[test_idx])[:, 1]
        else:
            score = pred.astype(float)

        y_true_all.extend(y[test_idx].tolist())
        y_pred_all.extend(pred.tolist())
        y_score_all.extend(score.tolist())
        for i, p in zip(test_idx, pred):
            out_of_fold_predictions[window_ids[i]] = int(p)
        if (y[test_idx] == 1).any():
            fold_recalls.append(recall_score(y[test_idx], pred, pos_label=1, zero_division=0))

    y_true_all = np.array(y_true_all)
    y_pred_all = np.array(y_pred_all)
    tn, fp, fn, tp = confusion_matrix(y_true_all, y_pred_all, labels=[0, 1]).ravel()

    try:
        auc = roc_auc_score(y_true_all, y_score_all)
    except ValueError:
        auc = float("nan")

    metrics = {
        "candidate": name,
        "n_windows": len(y),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "precision_fabricated": round(float(precision_score(y_true_all, y_pred_all, pos_label=1, zero_division=0)), 4),
        "recall_fabricated": round(float(recall_score(y_true_all, y_pred_all, pos_label=1, zero_division=0)), 4),
        "f1_fabricated": round(float(f1_score(y_true_all, y_pred_all, pos_label=1, zero_division=0)), 4),
        "roc_auc": round(float(auc), 4) if auc == auc else None,
        "accuracy": round(float((y_true_all == y_pred_all).mean()), 4),
        "recall_stability_across_folds": {
            "min": round(float(min(fold_recalls)), 4) if fold_recalls else None,
            "max": round(float(max(fold_recalls)), 4) if fold_recalls else None,
            "folds_with_a_positive_case": len(fold_recalls),
        },
        "mean_fit_time_seconds": round(float(np.mean(fit_times)), 6),
        "mean_predict_time_seconds": round(float(np.mean(predict_times)), 6),
    }
    return metrics, out_of_fold_predictions


def stability_by_sensor(table: list[dict[str, Any]], out_of_fold_predictions: dict[str, int]) -> dict[str, Any]:
    """Exactitude par type de capteur, à partir des prédictions **hors-pli**
    de la validation croisée (jamais des prédictions du modèle réentraîné sur
    l'ensemble des données, qui seraient en re-substitution et donc
    optimistes de façon trompeuse)."""
    by_sensor: dict[str, list[bool]] = {}
    for row in table:
        if row["window_id"] not in out_of_fold_predictions:
            continue
        correct = out_of_fold_predictions[row["window_id"]] == (1 if row["provenance"] == POSITIVE_LABEL else 0)
        by_sensor.setdefault(row["sensor_name"], []).append(correct)
    return {
        sensor: {"n": len(values), "accuracy": round(sum(values) / len(values), 4)}
        for sensor, values in sorted(by_sensor.items())
    }


def refit_full_and_predict(name: str, x_df, y: np.ndarray, x_test_df, test_window_ids: list[str]):
    pipeline = make_pipeline(CANDIDATES[name]())
    t0 = time.perf_counter()
    pipeline.fit(x_df, y)
    fit_time = time.perf_counter() - t0
    t0 = time.perf_counter()
    preds = pipeline.predict(x_test_df)
    proba = pipeline.predict_proba(x_test_df)[:, 1] if hasattr(pipeline, "predict_proba") else preds.astype(float)
    predict_time = time.perf_counter() - t0
    rows = [
        {
            "window_id": wid,
            "prediction": POSITIVE_LABEL if pred == 1 else "réelle",
            "score_fabriquee": round(float(score), 6),
        }
        for wid, pred, score in zip(test_window_ids, preds, proba)
    ]
    return rows, {"fit_time_seconds": round(fit_time, 6), "predict_time_seconds": round(predict_time, 6)}


def window_level_baseline(baseline_predictions_path: Path) -> dict[str, Any]:
    """Agrège la baseline M3 (par mesure) au grain fenêtre, par vote majoritaire.

    La baseline M3 (`data_pack/.../baseline_rules.py`) prédit par mesure, pas
    par fenêtre. Comparer un modèle par-fenêtre à une baseline par-mesure
    serait trompeur : ce vote majoritaire rend la comparaison équitable, au
    même grain que les modèles simples ci-dessus.
    """
    rows = load_rows(baseline_predictions_path)
    windows: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        windows.setdefault(row["window_id"], []).append(row)

    y_true: list[int] = []
    y_pred: list[int] = []
    for window_rows in windows.values():
        y_true.append(1 if window_rows[0]["provenance"] == POSITIVE_LABEL else 0)
        counts = {"fabriquée": 0, "réelle": 0}
        for row in window_rows:
            counts[row["prediction"]] = counts.get(row["prediction"], 0) + 1
        majority = max(counts, key=counts.get)
        y_pred.append(1 if majority == POSITIVE_LABEL else 0)

    y_true_arr, y_pred_arr = np.array(y_true), np.array(y_pred)
    tn, fp, fn, tp = confusion_matrix(y_true_arr, y_pred_arr, labels=[0, 1]).ravel()
    return {
        "candidate": "baseline_m3_regles_vote_majoritaire",
        "n_windows": len(y_true),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "precision_fabricated": round(float(precision_score(y_true_arr, y_pred_arr, pos_label=1, zero_division=0)), 4),
        "recall_fabricated": round(float(recall_score(y_true_arr, y_pred_arr, pos_label=1, zero_division=0)), 4),
        "f1_fabricated": round(float(f1_score(y_true_arr, y_pred_arr, pos_label=1, zero_division=0)), 4),
        "roc_auc": None,
        "accuracy": round(float((y_true_arr == y_pred_arr).mean()), 4),
        "recall_stability_across_folds": None,
        "mean_fit_time_seconds": 0.0,
        "mean_predict_time_seconds": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration", required=True, type=Path)
    parser.add_argument("--test", required=True, type=Path)
    parser.add_argument("--baseline-predictions", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    calibration_rows = load_rows(args.calibration)
    calibration_table = build_feature_table(calibration_rows)
    x, y, groups, window_ids = build_matrix(calibration_table)
    x_df = to_frame(x)

    cv_outputs = {name: cross_validate(name, x_df, y, groups, window_ids) for name in CANDIDATES}
    ml_results = [metrics for metrics, _ in cv_outputs.values()]
    baseline_result = window_level_baseline(args.baseline_predictions)
    results = ml_results + [baseline_result]
    (args.output_dir / "model_comparison_calibration.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    winner = max(ml_results, key=lambda r: r["f1_fabricated"])
    winner_name = winner["candidate"]
    _, winner_out_of_fold = cv_outputs[winner_name]
    stability = stability_by_sensor(calibration_table, winner_out_of_fold)
    (args.output_dir / "stability_by_sensor.json").write_text(
        json.dumps({"candidate": winner_name, "by_sensor": stability}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    test_rows = load_rows(args.test)
    test_table = build_feature_table(test_rows)
    x_test, _, _, test_window_ids = build_matrix(test_table)
    x_test_df = to_frame(x_test)

    frozen_predictions, timing = refit_full_and_predict(winner_name, x_df, y, x_test_df, test_window_ids)
    with (args.output_dir / "predictions_test.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["window_id", "prediction", "score_fabriquee"])
        writer.writeheader()
        writer.writerows(frozen_predictions)

    freeze_record = {
        "frozen_candidate": winner_name,
        "selection_rule": "f1_fabricated maximal en validation croisée groupée par equipment_id (5 plis)",
        "calibration_metrics": winner,
        "baseline_m3_metrics": baseline_result,
        "beats_baseline_f1": winner["f1_fabricated"] > baseline_result["f1_fabricated"],
        "refit_on_full_calibration_timing": timing,
        "n_test_windows_predicted": len(frozen_predictions),
        "note": (
            "Les métriques finales sur l'oracle de test scellé sont calculées "
            "côté formateur après ce gel ; seul ce résultat daté entre dans la "
            "décision de test (brief M4)."
        ),
    }
    (args.output_dir / "frozen_candidate.json").write_text(
        json.dumps(freeze_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({"comparison": results, "frozen": winner_name}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
