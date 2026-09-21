# Contrat de versions

## Ce que ce document garantit

Toute réponse produite par DiagOps peut être reliée aux versions exactes du
code, du modèle, du corpus, de l'index, du prompt et du jeu d'évaluation qui
l'ont produite. Le service expose ces versions en direct via `GET /version`
(`src/app.py`) — ce document explique comment chaque valeur est calculée et
comment revenir en arrière.

Référence saine actuellement retenue :
`data_pack/2026-S1/reference_runs/m4_for_m5/release_manifest.json`
(`release_id = diagops-m4-reference-r1`), admise par `decision_m4.md` comme
« référence saine de préproduction pour M5 ».

## Table des versions

| Unité | Version | Checksum ou digest | Source | Compatible avec | Procédure de retour |
|---|---|---|---|---|---|
| Release (le paquet complet) | `diagops-m4-reference-r1` | — (identifiant, pas un checksum) | `release_manifest.json`, `release_id` | toutes les unités ci-dessous, liées entre elles par ce fichier | `pipelines/rollback_release.py` restaure ce fichier complet depuis `artifacts/history/` |
| Code | `m4-baseline-r1` | — | `release_manifest.json`, `code_version` | `index_version = lexical-*`, logique déterministe de `src/versioning.py` | `git checkout` du commit associé (à consigner ici lors du premier vrai commit de code M5) |
| Corpus documentaire | `knowledge-3b3dfb356eee` | `3b3dfb35...0fe3f5a` (sha256 de `manifest.csv`) | calculé par `pipelines/build_index.py` : `"knowledge-" + sha256(manifest.csv)[:12]` | `index_version = lexical-dfb8faf0c9b4` (reconstruit à partir de ce même manifeste) | recharger le `manifest.csv` dont le sha256 complet est archivé dans `components.knowledge_manifest.sha256` |
| Index de recherche | `lexical-dfb8faf0c9b4` | `d250e85b...86c7021` (sha256 de `index_manifest.json`) | calculé par `build_index()` : sha256 de la concaténation triée `document_id:revision:checksum` de chaque document actif, tronqué à 12 caractères | corpus `knowledge-3b3dfb356eee` (7 documents actifs) | ne jamais écraser l'index en place : reconstruire dans `artifacts/candidates/`, ne promouvoir qu'après un gate `passed` (voir `pipelines/promote_release.py`) |
| « Modèle » (logique de réponse déterministe, pas un LLM — voir décision M4) | `diagops-grounded-reference-v1` | — | `release_manifest.json`, `model_version` | prompt `prompt-5f66e3c2e1d2` | pas de ré-entraînement : revenir au `release_id` précédent restaure cette valeur avec lui |
| Prompt / gabarit de réponse | `prompt-5f66e3c2e1d2` | `5f66e3c2...bc054f2e1d` (sha256 de `prompts/grounded_answer.txt`) | calculé de la même façon que le corpus : `"prompt-" + sha256(fichier)[:12]` | modèle `diagops-grounded-reference-v1` | recharger `prompts/grounded_answer.txt` dont le sha256 complet est dans `components.prompt.sha256` |
| Jeu d'évaluation (calibration) | `diagops-rag-calibration-2026-S1-r1` | `6f47a6b7...500ccc7b` (sha256 de `metrics_calibration.json`) | `release_manifest.json`, `evaluation_version` | seuils de `configs/gates.json` (document_count ≥ 7, hit@3 ≥ 0,8, citations résolubles = 1,0, abstentions correctes = 1,0) | jeu figé côté formateur ; toute évolution exige un nouveau `evaluation_version` et un nouveau gel |

## Comment chaque version est calculée (rejouable)

```bash
# Corpus et index : reconstruits localement, comparés à la référence
python pipelines/build_index.py \
  --manifest ../../data_pack/2026-S1/knowledge/manifest.csv \
  --documents ../../data_pack/2026-S1/knowledge/documents \
  --output artifacts/candidates/local/index.json
```

Vérifié le 2026-09-07 : cette commande, exécutée sur le corpus reçu, produit
`"index_version": "lexical-dfb8faf0c9b4"` — **identique** à la référence
distribuée (`index/index_manifest.json`). C'est la preuve concrète que la
version est déterministe et reproductible : reconstruire l'index à partir du
même corpus donne toujours la même empreinte, sur n'importe quelle machine.

`code_version`, `model_version` et `evaluation_version` ne sont pas
recalculés par un script ici : ce sont des identifiants attribués côté
formateur pour cette référence figée (`m4-baseline-r1`,
`diagops-grounded-reference-v1`, `diagops-rag-calibration-2026-S1-r1`).
Un futur candidat construit par l'équipe M5 devra attribuer ses propres
identifiants selon le même principe (voir `configs/release.example.json`,
qui laisse `REPLACE_WITH_GIT_COMMIT`, `REPLACE_AFTER_BUILD`,
`REPLACE_WITH_PROMPT_CHECKSUM` à remplacer par les valeurs réelles avant tout
gel).

## Comment interroger la version en cours (service démarré)

```bash
uvicorn src.app:app --reload
curl http://127.0.0.1:8000/version
```

Vérifié le 2026-09-07 : renvoie exactement le contenu de
`release_manifest.json` ci-dessus. `/health/ready` renvoie en plus le
`release_id` seul, pour un contrôle de vivacité rapide sans tout le détail.

## Procédure de retour arrière (rollback)

Mécanique déjà fournie par le starter (`src/versioning.py`) :

- `promote(candidate, current, history)` : avant de remplacer la release
  active, archive l'ancienne dans `artifacts/history/<release_id>.json` (si
  elle n'y est pas déjà), puis écrit la nouvelle de façon atomique (fichier
  temporaire + renommage, jamais d'écriture partielle visible).
- `rollback(current, history, release_id)` : relit une release archivée par
  son `release_id` et la réécrit comme active, de la même façon atomique.

Aucune promotion ne doit avoir lieu sans un `gate_report` marqué `passed`
(règle du starter, voir `pipelines/promote_release.py` et
`pipelines/evaluate_release.py` — étape suivante du brief).

## Ce qui reste ouvert à cette étape

- `code_version` n'est pour l'instant qu'un identifiant transmis par le
  formateur (`m4-baseline-r1`), pas encore lié à un commit Git réel de ce
  dépôt de travail : à faire lors du premier commit effectif du code M5.
- Aucun candidat personnel n'a encore été construit et gelé : cette table
  documente la référence saine de départ, pas encore un cycle complet
  build → évaluer → promouvoir → archiver.
