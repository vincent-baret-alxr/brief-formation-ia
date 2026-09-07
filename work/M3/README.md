# Starter — Module 3

Ce starter fournit le chargement des quatre sources ouvertes, des primitives
descriptives pour une série temporelle, un registre de règles, le format de
quarantaine unifié, un squelette de persistance, des tests d'exemple et les
notebooks présentiel et online.

Il ne constitue pas une architecture imposée. Il ne contient ni les règles
métier, ni les plages physiques, ni le rapprochement temporel, ni la liste des
anomalies injectées.

## Installation

Depuis `work/M3/` après `python tools/init_module.py M3`, ou depuis
`M3/starter/` pour vérifier le starter de référence :

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

Les quatre sources se trouvent dans le `data_pack/` du dépôt :

```text
data_pack/2026-S1/equipment/equipment.csv
data_pack/2026-S1/events/events.csv
data_pack/2026-S1/maintenance/maintenance_history.csv
data_pack/2026-S1/sensors/sensor_readings.csv
```

L'état préparé de référence issu de M2 :

```text
data_pack/2026-S1/reference_runs/m2_for_m3/processed/
data_pack/2026-S1/reference_runs/m2_for_m3/quarantine/quarantine_m2.csv
data_pack/2026-S1/reference_runs/m2_for_m3/regles_m2.md
```

## Structure

```text
starter/
├── contracts/
│   └── schemas.py
├── notebooks/
│   ├── notebook_multisource_m3.ipynb
│   └── m3_base_de_donnees_atlas.ipynb
├── src/data_pipeline/
│   ├── __main__.py
│   ├── cli.py
│   ├── io.py
│   ├── quarantine.py
│   ├── rules.py
│   ├── timeseries.py
│   └── validation.py
├── src/db/
│   ├── import_sources.py
│   ├── models.py
│   └── session.py
├── templates/
│   ├── couverture_et_risques.md
│   ├── diagnostic_multisource.md
│   ├── flux_et_cycle_de_vie.md
│   ├── journal_bord.md
│   ├── registre_regles.md
│   └── validation_report.example.json
├── tests/
└── requirements.lock
```

## Brief présentiel

Le notebook d'investigation reprend la situation et les axes du brief sans
imposer une démarche pas à pas :

```bash
jupyter lab notebooks/notebook_multisource_m3.ipynb
```

Le starter propose également une organisation sous forme de pipeline :

```bash
python -m src.data_pipeline --input ../../data_pack/2026-S1 --output ./output
```

Cette commande charge les quatre sources, calcule leurs empreintes, décrit les
séries temporelles dans `output/series_overview.csv` et crée la structure de
sortie. Le statut `starter_to_complete` indique volontairement que le travail
n'est pas fini.

Si vous utilisez le starter, il reste notamment à :

- donner un statut à chaque règle héritée de M2 ;
- écrire les règles temporelles et les appliquer ;
- remplir `quarantine.csv` pour les quatre sources ;
- écrire les tables préparées, les agrégats et le rapprochement ;
- démontrer la non-régression sur les tables M2 ;
- documenter le flux de traitement et le cycle de vie du jeu de données ;
- produire le diagnostic, la note de couverture et la décision.

### Ce que fournissent les primitives

`src/data_pipeline/timeseries.py` décrit, mais ne décide pas :

- `to_utc` convertit des horodatages hétérogènes et marque `NaT` ce qui est
  illisible, en supposant UTC quand le fuseau est absent : cette hypothèse est à
  confirmer ou à écarter ;
- `naive_timestamps` signale les valeurs écrites sans fuseau ;
- `duplicated_keys` retourne toutes les lignes partageant une clé, sans
  distinguer doublon strict et valeur divergente ;
- `observed_steps` et `series_overview` mesurent le pas réel, la période
  couverte et la complétude, série par série ;
- `window_bounds` construit des bornes d'observation à partir de paramètres que
  vous choisissez.

Le rapprochement lui-même, les plages physiques et le schéma de validation sont
des contrats à écrire dans `contracts/schemas.py`.

## Brief online

Le squelette de persistance se trouve dans `src/db/` :

- `session.py` fournit le moteur, la session et l'activation des clés étrangères
  sur SQLite ;
- `models.py` déclare `Equipment` comme exemple complet ; les autres entités et
  la table des mesures sont à écrire ;
- `import_sources.py` fournit un import d'équipements avec comptage des lignes
  refusées ; l'import idempotent des mesures est à écrire.

Alembic n'est pas préconfiguré : l'initialisation fait partie du travail.

```bash
alembic init alembic
# configurer sqlalchemy.url et target_metadata sur src.db.models:Base
alembic revision --autogenerate -m "schema initial"
alembic upgrade head
alembic downgrade -1
```

Le moteur par défaut est SQLite, dans `output/diagops.db`. La variable
`DIAGOPS_DATABASE_URL` permet d'utiliser PostgreSQL sans modifier le code.

```bash
jupyter lab notebooks/m3_base_de_donnees_atlas.ipynb
```

## Vérifications

```bash
python -m pytest -q
```

Les tests fournis illustrent le chargement, le format de quarantaine, le
registre de règles, les primitives temporelles et l'import en base. Ajoutez des
tests pour vos règles, vos cas de rejet et votre non-régression M2.

## Règles de travail

- ne modifiez pas les fichiers de `../../data_pack/` ;
- écrivez toutes les sorties dans `output/` ;
- signalez chaque rejet avec une règle et une raison ;
- conservez un état avant/après pour toute correction ;
- donnez un statut explicite à chaque règle héritée ;
- documentez la méthode qui permet de reproduire le résultat, et le temps
  qu'elle demande.
