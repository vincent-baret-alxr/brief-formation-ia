# Runbook DiagOps M5

## Responsables et escalade

À compléter.

## Démarrage et test de fumée

### En local (sans Docker), pour un développement rapide

```bash
cd work/M5
source .venv/bin/activate
uvicorn src.app:app --reload
```

Test de fumée (dans un autre terminal) :

```bash
curl http://127.0.0.1:8000/health/live    # attendu : {"status":"live"}
curl http://127.0.0.1:8000/health/ready   # attendu : {"status":"ready","release_id":"diagops-m4-reference-r1"}
curl http://127.0.0.1:8000/version        # attendu : le contrat de versions complet, voir docs/contrat_versions.md
curl http://127.0.0.1:8000/metrics        # attendu : 3 jauges à 1 (ready, dependency_up, index_valid)
```

Vérifié le 2026-09-07 : les 4 commandes renvoient exactement ce qui est
attendu ci-dessus sur la référence M4 saine.

### Avec la stack conteneurisée (3 services séparés)

```bash
docker compose -f deploy/compose.yaml up --build
```

Ordre de démarrage attendu : `indexer` construit l'index et s'arrête avec
succès → `api` démarre seulement ensuite (`depends_on:
service_completed_successfully`) → une fois `api` en bonne santé
(`healthy`), `prometheus` démarre. Un `api` qui ne passerait jamais
`healthy` bloquerait donc `prometheus` — comportement voulu, pas un bug.

Test de fumée identique au local, plus :

```bash
curl http://127.0.0.1:9090/-/healthy      # attendu : Prometheus Server is Healthy.
curl http://127.0.0.1:9090/targets        # attendu : la cible diagops-api en état "up"
```

Arrêt :

```bash
docker compose -f deploy/compose.yaml down
```

### Configuration externalisée (hors code)

| Variable | Où | Rôle | Valeur par défaut |
|---|---|---|---|
| `DIAGOPS_REFERENCE_MANIFEST` | `src/app.py` | chemin vers le `release_manifest.json` que l'API expose comme version active | référence M4 distribuée (`data_pack/.../m4_for_m5/release_manifest.json`) |
| `DIAGOPS_FAULT_FILE` | `src/app.py` | chemin vers un fichier JSON simulant une panne (`readiness_delay_ms`, `dependency_available`, `index_valid`) — voir « Incident et rollback » | `artifacts/runtime/faults.json`, absent par défaut (= aucune panne simulée) |

Limites de ressources (Docker uniquement, `deploy/compose.yaml`) : `indexer`
et `prometheus` 0,5 CPU / 256 Mo, `api` 1 CPU / 512 Mo — dimensionnées pour
ce laboratoire pédagogique (corpus de 8 documents), à revoir avant tout
usage à plus grande échelle.

## Arrêt contrôlé

À compléter.

## Construction et publication d'un index

À compléter avec les gates et l'atomicité observée.

## Incident et rollback

À compléter avec conditions de décision, objectif de reprise et vérifications.

## Sauvegarde, restauration et rotation des secrets

À compléter.

## Traces, accès et rétention

À compléter sans données personnelles ni documents sensibles en clair.
