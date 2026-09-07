# Journal de bord M4

| Date | Hypothèse ou décision | Action | Preuve observée | Écart | Suite |
|---|---|---|---|---|---|
| 2026-09-01 | La cible « provenance » ne doit pas être confondue avec une anomalie de qualité ou une panne future | Cadrage explicite dans `docs/protocole_evaluation.md` avant toute feature | Aucune feature ni métrique ne référence une panne | Aucun | — |
| 2026-09-01 | Un modèle simple entraîné sur les indices de la baseline M3 peut la dépasser | Comparaison régression logistique / forêt aléatoire / baseline M3, validation croisée groupée par `equipment_id` | Forêt aléatoire F1 0,381 vs baseline 0,375 : écart de 0,006, dans le bruit (rappel 0,00–0,67 selon le pli) | L'hypothèse n'est ni confirmée ni infirmée avec certitude à 30 échantillons | Décision « évaluer davantage », pas « adopter » |
| 2026-09-01 | La stabilité par capteur calculée en réentraînant sur toutes les données (re-substitution) donnait une exactitude quasi parfaite (0,89–1,00) — repérée comme trompeuse avant publication | Recalcul à partir des prédictions **hors-pli** de la validation croisée | Exactitude hors-pli 0,25–0,89 selon le capteur : image nettement moins favorable, mais honnête | Écart corrigé avant que le chiffre optimiste soit documenté | `src/model_eval.py::stability_by_sensor` utilise désormais les prédictions hors-pli |
| 2026-09-01 | Lexical et vectoriel sont l'un et l'autre stables (condition du brief pour tenter l'hybride) | Hit rate mesuré séparément sur les 10 questions de calibration répondables | Lexical 1,00, vectoriel 0,90 : condition remplie | Aucun | Hybride construite et retenue (hit rate 1,00, précision contexte 0,517, meilleure des trois) |
| 2026-09-01 | Un bon score de récupération ne doit pas rendre un document obsolète admissible | Test dédié avec une requête calquée sur le vocabulaire de `DOC-LOTO-001` (remplacé) | `DOC-LOTO-001` classé 1er lexicalement, exclu par `admissible()` (statut `superseded`) | Aucun | Comportement conforme, testé (`tests/test_threat_model.py`) |
| 2026-09-01 | Une donnée restreinte demandée par un rôle `public` (RAG-CAL-008) ne doit jamais être citée, même si elle est le document le plus pertinent | Réponse composée pour n'utiliser que `DOC-RAG-OPS-001` (admissible à tous les rôles), jamais `DOC-DATA-ACCESS-001` (restreint) | 0 citation du document restreint sur l'ensemble des traces | Aucun | Cas ajouté explicitement au threat model |
| 2026-09-01 | Les 12 réponses de calibration composées respectent le contrat de citation et l'abstention attendue | `validate_citations` + comparaison à `answerable` sur les 12 questions | 0 erreur de contrat, 12/12 abstentions conformes, 10/10 citations correctes | Aucun | Gel des réponses dans `src/rag_answers.py::CALIBRATION_ANSWERS` |
| 2026-09-01 | Gel du candidat capteur et prédiction sur le lot de test scellé | `python -m src.model_eval` avec réentraînement sur la calibration complète | 60 prédictions produites (`results/predictions_test.csv`), aucune étiquette de test consultée | Aucun | Notation finale par le formateur sur l'oracle scellé, hors de ce dépôt |
| 2026-09-01 | Décision finale modèle + RAG | Synthèse dans `docs/matrice_decision.md` | — | — | `évaluer davantage` (modèle capteur), `adopter` (RAG hybride, sous conditions) |

## Veille réglementaire M4 (§9 du brief)

**Non traité dans cette session.** Le dossier `veille_diagops/` (ouvert en
M0 selon `M0/brief3_module0_veille_ai_act.md`) n'existe dans aucun module
antérieur de ce dépôt de travail — sa consolidation en M4 suppose un travail
de recherche à sources primaires (état du règlement européen sur l'IA,
lignes directrices) distinct du reste de ce module, non entamé ici. À
reprendre séparément avant de considérer M4 comme clos au sens strict du
brief.

## Non traité dans cette session

- Brief M4 « online » (persistance base de données, `src/db/`, notebook
  `m3_base_de_donnees_atlas.ipynb`) — hors périmètre de ce passage.
- `veille_diagops/` (voir ci-dessus).
- Documents `approfondissement/` (défense, qualification d'un nouveau lot,
  rapport de reproduction, remédiation) — non traités.
