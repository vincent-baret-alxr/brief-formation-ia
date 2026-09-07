# Starter — Module 5

Ce starter fournit une API minimale instrumentée, un constructeur d'index
atomique, un gate de livraison, une promotion réversible et les modèles de
preuve du game day. Il ne constitue pas la solution du brief : les apprenants
doivent compléter le retrieval, les tableaux de bord, les alertes et le
runbook.

## Installation locale

Depuis la racine du dépôt pédagogique :

```bash
python tools/init_module.py M5
cd work/M5
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
```

Sous PowerShell, l'activation est `.venv\Scripts\Activate.ps1`.

## Vérifier l'état de référence

```bash
python pipelines/build_index.py \
  --manifest ../../data_pack/2026-S1/knowledge/manifest.csv \
  --documents ../../data_pack/2026-S1/knowledge/documents \
  --output artifacts/candidates/local/index.json

python pipelines/evaluate_release.py \
  --index artifacts/candidates/local/index.json \
  --metrics ../../data_pack/2026-S1/reference_runs/m4_for_m5/evaluation/metrics_calibration.json \
  --gates configs/gates.json \
  --output artifacts/candidates/local/gate_report.json
```

## Lancer l'API

```bash
uvicorn src.app:app --reload
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:8000/version
curl http://127.0.0.1:8000/metrics
```

La variable `DIAGOPS_REFERENCE_MANIFEST` permet de sélectionner un autre
manifeste. Par défaut, l'API utilise la référence M4 distribuée.

## Lancer la stack conteneurisée

```bash
docker compose -f deploy/compose.yaml up --build
```

La stack contient trois responsabilités séparées : construction de l'index,
API et collecte Prometheus. Le profil par défaut reste local et n'utilise aucun
service externe.

Les tags d'images servent uniquement à initialiser le laboratoire. Avant toute
promotion, relevez leurs digests résolus dans `docs/contrat_versions.md` afin
que la version restaurée soit immuable.

## Structure

```text
work/M5/
├── configs/              # gates et release locale
├── deploy/               # Dockerfile, Compose et Prometheus
├── pipelines/            # build, évaluation, promotion et rollback
├── monitoring/           # contrat de métriques et dashboards
├── src/                  # API et primitives de versionnement
├── tests/                # smoke tests du starter
├── docs/                 # modèles des livrables d'exploitation
├── game_day/             # modèles de préparation et post-incident
├── artifacts/            # candidats et slots locaux, jamais le data pack
└── journal_bord.md
```

## Règles

- ne copiez pas le corpus ou les références dans `work/M5/` ;
- ne promouvez jamais un candidat qui n'a pas un gate `passed` ;
- conservez la version saine avant toute promotion ;
- ne placez aucun secret ni contenu documentaire sensible dans les traces ;
- les scénarios d'incident sont remis séparément par le formateur.
