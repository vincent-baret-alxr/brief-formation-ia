# Starter — Module 2

Ce starter fournit des fonctions de chargement, un exemple de pipeline, le
format de quarantaine, des tests d'exemple et les notebooks présentiel et
online. Il ne
constitue pas une architecture imposée et ne contient ni les règles métier
complètes ni la liste des anomalies injectées.

## Installation

Depuis `work/M2/` après `python tools/init_module.py M2`, ou depuis
`M2/starter/` pour vérifier le starter de référence :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
```

Sous Windows PowerShell :

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock
```

## Données

Les trois tables se trouvent dans le `data_pack/` du dépôt :

```text
data_pack/2026-S1/equipment/equipment.csv
data_pack/2026-S1/events/events.csv
data_pack/2026-S1/maintenance/maintenance_history.csv
```

Le présentiel peut aussi utiliser la matrice d'erreurs commune :

```text
data_pack/2026-S1/reference_runs/m1_for_m2/analyses/matrice_erreurs_m1.csv
```

## Structure

```text
starter/
├── contracts/
│   └── schemas.py
├── notebooks/
│   ├── notebook_audit_m2.ipynb
│   └── m2_statistiques_atlas.ipynb
├── src/data_pipeline/
│   ├── __main__.py
│   ├── cli.py
│   ├── io.py
│   ├── quarantine.py
│   └── validation.py
├── templates/
│   ├── audit_report.md
│   ├── journal_bord.md
│   └── validation_report.example.json
├── tests/
└── requirements.lock
```

## Exemple de démarrage pour le présentiel

Le notebook d'audit reprend la situation professionnelle et les axes du brief
sans imposer une démarche pas à pas :

```bash
jupyter lab notebooks/notebook_audit_m2.ipynb
```

Il fournit le chargement en lecture seule, les cadres du registre de règles et
de la quarantaine, l'accès à la référence M1 et le canevas des dix réponses.
Les règles métier, traitements, tests et conclusions restent à construire.

Le starter propose également une organisation sous forme de pipeline :

```bash
python -m src.data_pipeline --input ../../data_pack/2026-S1 --output ./output
```

Cette commande illustre une manière d'organiser des contrôles rejouables. Elle
vérifie que les fichiers sont lisibles, calcule leurs checksums et crée une
structure de sortie. Le statut `starter_to_complete` indique volontairement
que le travail n'est pas fini.

Vous pouvez compléter cette proposition, l'adapter ou retenir une autre forme
de travail conforme au brief : notebook accompagné de fonctions, scripts ou
pipeline. Si vous utilisez le starter, il reste notamment à :

- appliquer les règles du brief ;
- remplir `quarantine.csv` ;
- écrire les tables validées dans `output/processed/` ;
- compléter les résultats de validation ;
- produire le diagnostic et la décision.

## Vérifications

```bash
python -m pytest -q
```

Les tests fournis illustrent le chargement, le format de quarantaine et un
contrôle de colonnes obligatoires. Ajoutez des tests pour vos règles métier et
vos cas de rejet.

## Notebook online

```bash
jupyter lab notebooks/m2_statistiques_atlas.ipynb
```

Pour vérifier son exécution complète :

```bash
jupyter nbconvert --to html --execute \
  notebooks/m2_statistiques_atlas.ipynb \
  --output m2_statistiques_atlas.html
```

## Règles de travail

- ne modifiez pas les fichiers de `../../data_pack/` ;
- écrivez toutes les sorties dans `output/` ;
- signalez chaque rejet avec une règle et une raison ;
- conservez un état avant/après pour toute correction ;
- documentez la méthode qui permet de reproduire le résultat.
