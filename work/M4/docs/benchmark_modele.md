# Benchmark du modèle simple

Rejouable : `python -m src.model_eval --calibration ... --test ... --baseline-predictions ... --output-dir results`.

## Baseline M3 figée

`data_pack/2026-S1/reference_runs/m3_for_m4/baseline_rules.py` : règles sans
apprentissage (unité attendue, plage physique, grille temporelle, valeur
sentinelle, précision décimale), prédiction **par mesure**. Sur les 900
mesures de calibration : précision 0,596, rappel 0,273, F1 0,374, exactitude
0,666 (`baseline_metrics_calibration.json`, fourni).

Cette baseline prédit par mesure, notre cible est par fenêtre : elle est
ramenée au grain fenêtre par **vote majoritaire des 30 prédictions de la
fenêtre** (`src/model_eval.py::window_level_baseline`) pour que la
comparaison soit au même grain que les modèles simples. Résultat : précision
0,600, rappel 0,273, **F1 0,375**, exactitude 0,667.

## Candidats et justification

- **Régression logistique** (`class_weight="balanced"`) : linéaire,
  interprétable (poids par feature), rapide — candidat de référence pour
  vérifier qu'un modèle simple apporte quelque chose au-delà des règles.
- **Forêt aléatoire** (`n_estimators=200`, `max_depth=4`,
  `class_weight="balanced"`) : capture des interactions entre indices
  (ex. « unité incohérente ET hors grille temporelle ») qu'une baseline par
  règles indépendantes ou qu'un modèle linéaire ne pondèrent pas ensemble ;
  profondeur bornée à 4 pour limiter le surapprentissage sur 30
  observations.

Alternative écartée : un modèle plus complexe (gradient boosting, réseau de
neurones) — injustifiable sur 30 fenêtres d'apprentissage, où la variance
d'estimation domine largement toute différence de capacité du modèle (voir
stabilité ci-dessous).

## Splits et contrôle de fuite

`GroupKFold(n_splits=5)` groupé par `equipment_id` (pas seulement
`window_id`) : 22 équipements distincts pour 30 fenêtres, 5 équipements
portant plusieurs fenêtres. Aucun `equipment_id` n'apparaît à la fois dans
le pli d'apprentissage et le pli de validation d'une même itération —
vérifié par construction (propriété de `GroupKFold`, testée dans
`tests/test_model_eval.py`).

Features construites sans toucher au test (`src/features.py`) : résumé
numérique par fenêtre (moyenne, écart-type, part de valeurs manquantes) et
indices dérivés des règles connues (part de mesures à l'unité incohérente,
part de valeurs sentinelles, part hors grille temporelle 6 h, part de
valeurs à plus de deux décimales) — un modèle simple peut apprendre à
pondérer ces indices au lieu de les traiter en tout-ou-rien comme la
baseline.

## Résultats

Validation croisée groupée, 30 fenêtres de calibration :

| Candidat | Précision | Rappel | F1 | ROC-AUC | Temps d'entraînement moyen | Temps de prédiction moyen |
|---|---:|---:|---:|---:|---:|---:|
| Baseline M3 (vote majoritaire) | 0,600 | 0,273 | 0,375 | — | 0 s (sans apprentissage) | — |
| Régression logistique | 0,364 | 0,364 | 0,364 | 0,412 | 2,2 ms | 0,7 ms |
| **Forêt aléatoire (retenue)** | 0,400 | 0,364 | **0,381** | 0,502 | 62 ms | 3,0 ms |

Mémoire : les trois candidats tiennent en quelques centaines de kilooctets
(30 lignes × 6 features) — non discriminante à cette échelle, non mesurée
séparément.

La forêt aléatoire obtient le F1 le plus élevé et dépasse marginalement la
baseline (0,381 contre 0,375) — un écart de 0,006 sur 30 échantillons, à
l'intérieur du bruit d'estimation attendu à cette taille. La régression
logistique ne dépasse pas la baseline. **Aucun candidat ne bat clairement la
baseline** ; voir `matrice_decision.md`.

## Stabilité par segment

Exactitude **hors-pli** (jamais en re-substitution) du candidat retenu
(forêt aléatoire), par type de capteur :

| Capteur | n fenêtres | Exactitude hors-pli |
|---|---:|---:|
| `rpm` | 4 | 0,250 |
| `pressure_bar` | 3 | 0,333 |
| `current_a` | 6 | 0,500 |
| `vibration_mm_s` | 8 | 0,500 |
| `temperature_c` | 9 | 0,889 |

Rappel de la classe `fabriquée`, minimum et maximum observés sur les 5 plis
de validation croisée : **0,00 à 0,67** — le modèle rate parfois toutes les
fenêtres fabriquées d'un pli entier. Cette instabilité, comme la variation
de 0,25 à 0,89 par capteur (effectifs de 3 à 9 par segment), n'est pas un
défaut d'implémentation : c'est la conséquence directe de 30 échantillons
répartis sur 22 groupes et 5 capteurs. Aucune conclusion de stabilité fiable
ne peut être tirée par segment à ce volume.

## Limites et décision

- 30 échantillons de calibration ne permettent pas de trancher entre les
  deux modèles simples, ni entre un modèle simple et la baseline, avec
  confiance.
- Le grain de comparaison (vote majoritaire pour la baseline) est un choix
  d'agrégation parmi d'autres (l'agrégation « au moins une mesure signalée »
  donne un F1 de 0,353 pour la baseline, légèrement inférieur) — documenté,
  pas neutre.
- Aucun modèle ne doit être présenté comme fiable pour détecter une
  provenance fabriquée en production à ce stade. Décision détaillée dans
  `matrice_decision.md` : **évaluer davantage** (recueillir plus de fenêtres
  étiquetées avant tout arbitrage définitif entre baseline et modèle
  simple).
