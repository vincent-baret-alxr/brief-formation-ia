# Starter — Module 4

Ce starter fournit les contrats de données, un retrieval lexical minimal, les
bornes de l’agent, des tests de sécurité et les modèles documentaires du M4. Il
ne contient ni modèle entraîné, ni embeddings choisis, ni réponse au brief.

## Installation

Depuis la racine du dépôt pédagogique :

```bash
python tools/init_module.py M4
cd work/M4
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
```

Sous PowerShell, l’activation est `.venv\Scripts\Activate.ps1`.

## Données

Les chemins sont relatifs à `work/M4/` :

```text
../../data_pack/2026-S1/model_eval/sensor_calibration.csv
../../data_pack/2026-S1/model_eval/sensor_test.csv
../../data_pack/2026-S1/reference_runs/m3_for_m4/
../../data_pack/2026-S1/knowledge/manifest.csv
../../data_pack/2026-S1/knowledge/documents/
../../data_pack/2026-S1/rag_eval/questions.jsonl
```

Le test capteur et les labels RAG `test` restent scellés côté formateur. Ils ne
servent jamais au réglage. `window_id` est la clé de groupe obligatoire pour les
partitions capteurs.

## Structure

```text
starter/
├── configs/
├── src/
├── tests/
├── templates/
├── approfondissement/
├── results/
├── journal_bord.md
└── requirements.lock
```

## Premières vérifications

```bash
python -m src.io_contracts \
  --manifest ../../data_pack/2026-S1/knowledge/manifest.csv \
  --documents ../../data_pack/2026-S1/knowledge/documents \
  --questions ../../data_pack/2026-S1/rag_eval/questions.jsonl
python -m pytest -q
```

## Travail restant

- geler un protocole et des splits groupés ;
- construire les features sans utiliser le test ;
- comparer deux modèles simples à la baseline M3 ;
- documenter et mesurer un modèle d’embeddings ;
- comparer sans retrieval, lexical et vectoriel ;
- produire les réponses citées et les abstentions ;
- compléter les tests de menaces ;
- renseigner les modèles de livrables et défendre la décision.

Les sorties vont dans `results/`. Ne copiez jamais le data pack dans le module.
