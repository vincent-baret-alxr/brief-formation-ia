# Benchmark retrieval et réponse citée

Rejouable : `python -m src.retrieval_eval --manifest ... --documents ... --questions ... --output-dir results`
puis `python -m src.rag_answers --manifest ... --documents ... --questions ... --output-dir results`.

## Corpus admis et exclusions

8 documents dans `data_pack/2026-S1/knowledge/manifest.csv`, tous à
checksum, révision, droits et sensibilité déclarés (condition d'ouverture du
module, brief M4). Chargement et vérification via
`src/io_contracts.py::load_manifest` (checksum SHA-256, `document_id`
unique, fichier présent).

Exclusions par construction :

- `DOC-LOTO-001` (révision remplacée, statut `superseded`) : jamais
  admissible, quel que soit son score de récupération — voir la section
  « Analyse par risque » ;
- `DOC-DATA-ACCESS-001` (sensibilité restreinte, rôles
  `superviseur;auditeur`) : inadmissible pour les rôles `technicien` et
  `public`.

## Configurations comparées

Modèle vectoriel retenu : `sentence-transformers/all-MiniLM-L6-v2`, local,
sans clé ni service externe — justification complète dans
`src/vector_retrieval.py` (taille, absence de dépendance à une API,
alternative TF-IDF écartée pour sa moindre robustesse aux reformulations).
Index : 8 vecteurs de 384 dimensions, 12 288 octets, construit en 8,9 s
(dominé par le chargement du modèle, une fois par exécution).

Mesuré sur les 10 questions de calibration répondables
(`results/retrieval_comparison.json`) :

| Variante | Hit rate | Précision contexte | Latence moyenne | Taille index |
|---|---:|---:|---:|---:|
| Sans retrieval | 0,00 | 0,00 | < 1 µs | — |
| Lexical | 1,00 | 0,45 | 0,38 ms | — |
| Vectoriel | 0,90 | 0,45 | 18,1 ms | 12 288 octets |
| **Hybride (retenue)** | 1,00 | **0,517** | 4,2 ms | 12 288 octets |

L'hybride n'a été construite qu'après avoir vérifié que lexical et
vectoriel étaient l'un et l'autre stables (hit rate ≥ 0,9), condition posée
par le brief. Fusion : moyenne pondérée à parts égales du score lexical
normalisé et du cosinus vectoriel normalisé
(`src/vector_retrieval.py::rank_hybrid`).

**Citations exactes et refus corrects** (12 questions de calibration,
répondables et non répondables, `results/grounded_answer_summary.json`) :
taux d'abstention conforme à l'attendu **1,00** (12/12), taux de citation
correcte **1,00** (10/10 questions répondables citent au moins un document
attendu), **0** erreur de contrat de citation
(`src/grounded_answer.py::validate_citations`, exécuté sur les 12 réponses
composées dans `src/rag_answers.py`).

## Analyse par risque

- **`revision`** (RAG-CAL-001, RAG-CAL-010) : le retrieval hybride classe
  `DOC-LOTO-001` en tête par score lexical brut (variante de casse et de
  vocabulaire proche de la question), mais le filtre d'admissibilité
  l'exclut systématiquement du contexte utilisable — voir
  `tests/test_threat_model.py::test_a_superseded_document_ranked_first_is_still_inadmissible`.
  Un bon score ne suffit pas à rendre une source admissible, exactement
  comme prévu par `data_pack/2026-S1/knowledge/README.md`.
- **`restricted_data`** (RAG-CAL-008) : le document le plus topiquement
  pertinent (`DOC-DATA-ACCESS-001`) est lui-même inadmissible pour le rôle
  `public` de la question. La réponse composée s'appuie uniquement sur
  `DOC-RAG-OPS-001` (admissible à tous les rôles) pour expliquer le refus,
  sans jamais citer ni reproduire le contenu restreint.
- **`abstention` / `missing_evidence` / `unsupported_prediction`**
  (RAG-CAL-004, RAG-CAL-006, RAG-CAL-011, RAG-CAL-012) : un contexte
  topiquement proche peut exister (ex. `DOC-PUMP-VIB-001` est récupéré pour
  la question sur la marque de lubrifiant, score 0,94) sans contenir la
  réponse précise demandée. Le hit rate mesure la récupération, pas la
  suffisance de preuve : la décision d'abstenir est prise à la génération,
  pas au retrieval — d'où l'écart entre hit rate de retrieval et taux
  d'abstention correcte, calculés séparément.

## Écarts calibration / test

Le pipeline (retrieval hybride + décision d'agent) a été exécuté sur les 12
questions du split test scellé pour produire des traces
(`results/agent_traces.json`), **sans aucune réponse composée ni score
calculé** : les labels et documents attendus du test restent scellés côté
formateur, conformément au brief. Aucun ajustement du retrieval ni des
réponses de calibration n'a été fait à partir de ces traces.

## Limites et décision

- 10 questions répondables en calibration est un échantillon très réduit
  pour un hit rate ; un écart d'une question change le résultat de 10
  points.
- La précision du contexte (0,45–0,52) reste modeste : le top-3 documentaire
  contient souvent 1 à 2 documents non pertinents en plus du bon — sans
  conséquence ici car l'admissibilité et la lecture des extraits filtrent
  correctement, mais un grain plus fin (top-1 ou reranking) réduirait le
  bruit pour un futur usage à plus grande échelle.
- La fusion hybride (poids 0,5/0,5) n'a pas été optimisée : elle a été
  fixée a priori et évaluée telle quelle, pas choisie a posteriori sur le
  résultat calibration (qui aurait été un réglage sur le seul jeu
  disponible, donc une forme de fuite).

Décision : retenir la configuration **hybride** pour le RAG, avec les
conditions d'abstention et d'admissibilité déjà démontrées — voir
`matrice_decision.md` pour la décision globale (modèle + RAG + agent).
