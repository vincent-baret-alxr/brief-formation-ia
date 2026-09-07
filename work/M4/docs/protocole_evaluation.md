# Protocole d'évaluation M4

- Date de gel : 2026-09-01
- Auteur : session de reconstruction M4 (voir `journal_bord.md`)
- Commit ou empreinte du candidat : modèle capteur `random_forest`, empreinte
  du run dans `results/frozen_candidate.json` ; réponses RAG figées dans
  `src/rag_answers.py::CALIBRATION_ANSWERS`.
- Environnement, versions et graine : Python 3.11, `requirements.lock`
  (scikit-learn 1.7.1, sentence-transformers 5.1.0, pandas 2.3.1, numpy
  2.3.2) ; graine `SEED = 42` (`src/model_eval.py`).

## Décision modèle

- Cible observable : `provenance` (`réelle` / `fabriquée`) d'une fenêtre de
  30 mesures (`window_id`). **Pas** une anomalie de qualité capteur, **pas**
  une panne future — ces deux cibles ne sont pas prouvables sur ce lot
  (brief M4, axe 1 ; voir aussi `data_pack/DATA_CARD.md`, section « Actifs
  ouverts en M4 »).
- Unité de décision : la fenêtre (`window_id`), pas la mesure individuelle
  (la baseline M3 prédit par mesure ; ramenée à la fenêtre par vote
  majoritaire pour une comparaison équitable, voir `benchmark_modele.md`).
- Erreurs coûteuses : un faux négatif (fenêtre fabriquée classée réelle)
  laisse une donnée fabriquée entrer dans une analyse sans avertissement ;
  un faux positif écarte à tort une mesure réelle. Le brief ne fixe pas de
  coût relatif explicite entre les deux ; à défaut, le F1 sur la classe
  `fabriquée` est retenu comme critère de sélection unique, documenté et
  reproductible plutôt qu'une pondération inventée.
- Groupes utilisés pour les splits : `equipment_id` (pas seulement
  `window_id`) — 5 équipements du lot de calibration portent plusieurs
  fenêtres ; les regrouper évite qu'un même équipement instruise et évalue
  un même pli.
- Calibration : `data_pack/2026-S1/model_eval/sensor_calibration.csv`,
  30 fenêtres étiquetées, 22 `equipment_id` distincts.
- Test scellé : `data_pack/2026-S1/model_eval/sensor_test.csv`, 60 fenêtres,
  sans étiquette. Non ouvert pour l'ajustement ; seules des prédictions y
  sont produites après gel (`results/predictions_test.csv`).
- Métriques et seuils fixés avant le test : matrice de confusion,
  précision/rappel/F1 sur la classe `fabriquée`, ROC-AUC, exactitude par
  segment (`sensor_name`), latence d'entraînement et de prédiction. Seuil
  d'acceptation : le candidat retenu doit au moins égaler le F1 de la
  baseline M3 ramenée au grain fenêtre (0,375) — sans quoi la décision par
  défaut est de maintenir la baseline (voir `matrice_decision.md`).

## Décision RAG

- Utilisateurs et rôles : `technicien`, `superviseur`, `auditeur`, `public`
  (`data_pack/2026-S1/knowledge/documents/DOC-DATA-ACCESS-001.md`).
- Documents admissibles : statut `active` **et** rôle demandeur dans
  `allowed_roles` (`src/retrieval.py::admissible`). Un document `superseded`
  n'est jamais admissible, quel que soit son score de récupération.
- Baselines : sans retrieval, lexical (`src/retrieval.py`), vectoriel
  (`sentence-transformers/all-MiniLM-L6-v2`, `src/vector_retrieval.py`),
  hybride (fusion pondérée des deux) — retenue seulement après avoir
  constaté que lexical et vectoriel sont l'un et l'autre stables (hit rate
  ≥ 0,9 sur la calibration), condition posée par le brief.
- Métriques : hit rate documentaire, précision du contexte admissible,
  latence, taille d'index — sur les 10 questions de calibration
  répondables. Citations exactes et refus corrects mesurés séparément
  (`results/grounded_answer_summary.json`).
- Conditions d'abstention : citation vers un document non admissible,
  question hors couverture documentaire (aucune preuve précise, même si un
  document est topiquement proche), ou conflit de révisions actives sans
  succession explicite (`src/conflict_check.py`).

## Règle de changement

Tout nouveau gel exige : (1) une nouvelle empreinte de configuration
(graine, versions, jeu de features) enregistrée dans
`results/frozen_candidate.json` ou son équivalent, (2) la réexécution
complète du protocole ci-dessus sur la même calibration, jamais sur un
sous-ensemble choisi après coup, et (3) une nouvelle entrée datée du journal
de bord expliquant le motif du changement. Un run dont la configuration
diffère de celle figée ici ne peut pas être comparé au run précédent comme
s'il s'agissait du même candidat.
