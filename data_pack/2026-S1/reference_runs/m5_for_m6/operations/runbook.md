# Runbook de la référence M5

Ce runbook décrit l'exploitation de la stack de référence, pas la production
attendue en M6.

## Démarrage

```bash
cd M5/starter
docker compose -f deploy/compose.yaml up --build
```

Sans conteneur :

```bash
export DIAGOPS_REFERENCE_MANIFEST=../../data_pack/2026-S1/reference_runs/m5_for_m6/release_manifest.json
uvicorn src.app:app --reload
```

## Test de fumée

| Vérification | Commande | Attendu |
|---|---|---|
| Vie | `curl -s localhost:8000/health/live` | `{"status":"live"}` |
| Disponibilité | `curl -s localhost:8000/health/ready` | `release_id` = `diagops-m5-reference-r1` |
| Version | `curl -s localhost:8000/version` | versions liées identiques au manifeste |
| Métriques | `curl -s localhost:8000/metrics` | séries de `monitoring/baseline_metrics.json` |

## Reconstruction de l'index

L'index se reconstruit hors du chemin actif, puis se promeut atomiquement.
Un gate en échec interdit la promotion.

## Restauration

La version saine est celle décrite par `release_manifest.json`. Toute
restauration se termine par le test de fumée ci-dessus et par la relecture du
gate.

## Traces

Les traces ne contiennent ni document en clair, ni donnée personnelle, ni
chaîne de raisonnement privée. Cette contrainte reste vraie pour les traces
d'outils ajoutées en M6.
