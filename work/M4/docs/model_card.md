# Model card M4

Deux composants distincts sont couverts : le modèle capteur (provenance) et
le système RAG (retrieval + réponse citée + agent borné).

## Usage prévu et utilisateurs

- **Modèle capteur** : usage pédagogique d'évaluation, pas de déploiement —
  voir décision (`docs/matrice_decision.md`). Utilisateur prévu à terme :
  équipe DiagOps qualifiant un lot de mesures avant analyse.
- **RAG** : assistant de triage documentaire pour `technicien`,
  `superviseur`, `auditeur` ; consultation restreinte pour `public` (accès
  refusé aux documents restreints, explication de la règle autorisée).

## Cible et données

- **Modèle capteur** : cible `provenance` (`réelle`/`fabriquée`) d'une
  fenêtre de 30 mesures. Donnée : `data_pack/2026-S1/model_eval/`,
  30 fenêtres de calibration (22 équipements), 60 fenêtres de test scellées.
  Ce n'est ni un détecteur d'anomalie de qualité, ni un prédicteur de panne
  future (brief M4, axe 1).
- **RAG** : corpus de 8 documents synthétiques
  (`data_pack/2026-S1/knowledge/`), 24 questions d'évaluation (12
  calibration visibles, 12 test scellées,
  `data_pack/2026-S1/rag_eval/questions.jsonl`).

## Modèle et configuration

- **Modèle capteur retenu** : `RandomForestClassifier` (`n_estimators=200`,
  `max_depth=4`, `class_weight="balanced"`, graine 42), features :
  moyenne/écart-type/part manquante par fenêtre + 5 indices dérivés des
  règles M3 (unité, sentinelle, grille temporelle, précision décimale,
  horodatage illisible). Pipeline complet et graine :
  `src/model_eval.py`.
- **RAG** : retrieval lexical (`src/retrieval.py`) + vectoriel
  (`sentence-transformers/all-MiniLM-L6-v2`, `src/vector_retrieval.py`) +
  fusion hybride pondérée (0,5/0,5). Génération : réponses composées et
  validées par contrat (`src/grounded_answer.py`), **aucun modèle génératif
  connecté** à ce stade. Agent : `src/bounded_agent.py`, 3 actions
  possibles (`answer_without_tool`, `search_knowledge`, `abstain`).

## Métriques globales et par segment

Voir le détail dans `docs/benchmark_modele.md` et
`docs/benchmark_retrieval.md`. Résumé :

| Composant | Métrique clé | Valeur |
|---|---|---:|
| Modèle capteur (forêt aléatoire) | F1 fenêtre (validation croisée groupée) | 0,381 |
| Modèle capteur | Baseline M3 (vote majoritaire, même grain) | 0,375 |
| Modèle capteur | Rappel `fabriquée`, min–max entre plis | 0,00–0,67 |
| RAG hybride | Hit rate documentaire (calibration répondable) | 1,00 |
| RAG hybride | Précision du contexte admissible | 0,517 |
| RAG (12 réponses de calibration) | Abstention conforme à l'attendu | 12/12 |
| RAG (12 réponses de calibration) | Erreur de contrat de citation | 0 |

## Limites, biais et usages exclus

- Le modèle capteur est entraîné sur 30 fenêtres (22 équipements) : aucune
  garantie de généralisation à un parc plus large ou à d'autres types de
  fabrication non représentés dans ce lot.
- Le corpus RAG est synthétique et pédagogique (`data_pack/DATA_CARD.md`) :
  les seuils cités (vibration, température, pression, courant) ne sont pas
  des seuils industriels réels et ne doivent jamais être appliqués à un site
  réel sans validation métier.
- Aucun des deux composants ne prédit de panne future ni ne prouve une
  causalité (hors périmètre explicite du brief M4).
- Le RAG ne connecte aucun modèle génératif : les réponses de calibration
  sont composées manuellement et vérifiées par contrat, pas produites
  automatiquement à partir d'une question arbitraire. Une génération libre
  connectée ultérieurement devra revalider entièrement `docs/threat_model.md`.

## Risques et supervision humaine

- Toute ligne en quarantaine ou en `conserve_signale` dans les préparations
  amont (M2/M3) reste hors du périmètre de vérité tant qu'un expert métier
  ne l'a pas tranchée (voir `work/M3/docs/registre_regles.md`).
- Le RAG refuse par construction (`abstain()`) plutôt que de deviner ; toute
  levée d'une abstention doit rester une décision humaine documentée.
- L'agent ne peut exécuter aucune action à effet (pas d'écriture, pas de
  commande) — voir `docs/threat_model.md`, cas « contournement des
  limites ».

## Version, empreinte et conditions de réévaluation

- Empreinte du modèle capteur figé : `results/frozen_candidate.json`
  (candidat, métriques de calibration, temps de ré-entraînement).
- Empreinte des réponses RAG : `src/rag_answers.py::CALIBRATION_ANSWERS`
  (versionné avec le code, pas un artefact binaire séparé).
- Réévaluation requise si : le volume de fenêtres étiquetées augmente
  significativement (modèle capteur), le corpus documentaire est modifié ou
  étendu (RAG — recalculer les checksums et rejouer
  `docs/benchmark_retrieval.md`), ou un modèle génératif est connecté au
  pipeline de réponse (RAG — revalider `docs/threat_model.md` dans son
  intégralité).
