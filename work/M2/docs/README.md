# Démarche retenue — Brief 1 module 2

Ce document explique **ce qui a été implémenté et pourquoi**, indépendamment
du diagnostic de données lui-même (voir
[`diagnostic_donnees.md`](diagnostic_donnees.md) pour les réponses aux dix
questions du brief et la décision).

## Choix de forme

Le brief laisse le choix entre notebook, scripts ou pipeline. Le starter
fourni ([`src/data_pipeline/`](../src/data_pipeline/)) proposait déjà une
commande (`python -m src.data_pipeline`) avec chargement, checksums et un
format de quarantaine imposé, mais aucune règle métier (statut
`starter_to_complete`). Ce point de départ a été retenu et complété plutôt que
remplacé par un notebook, pour deux raisons :

- les contrôles et corrections sont ainsi rejouables par une commande unique
  et testables avec `pytest`, ce qui répond directement à l'exigence du brief
  (« une autre personne doit pouvoir comprendre les règles, rejouer les
  traitements ») ;
- le format de quarantaine (`source_file`, `row_identifier`, `rule_id`,
  `column`, `observed_value`, `reason`, `decision`) était déjà défini par
  `quarantine.py` et correspondait exactement à ce que demande le brief.

Le notebook `notebooks/notebook_audit_m2.ipynb` fourni par le starter n'a pas
été rempli : la restitution passe par le pipeline exécutable et par
`docs/diagnostic_donnees.md`.

## Ce qui a été ajouté

### `contracts/schemas.py`

Les trois `DataFrameSchema` Pandera (`equipment_schema`, `events_schema`,
`maintenance_schema`) étaient à écrire entièrement (`NotImplementedError`).
Ils encodent, colonne par colonne, les règles issues de `SCHEMA.md` et de
l'inspection directe des fichiers reçus :

- domaines fermés (`criticality`, `severity`, `event_type`,
  `intervention_type`, `outcome`, `equipment_type`, `site_id`) via
  `Check.isin` ;
- nullabilité fidèle au schéma : `manufacturer`, `rated_power_kw`, `end_at`,
  `closed_at` sont explicitement nullables (une intervention ou un événement
  encore ouvert n'est pas une anomalie) ;
- deux règles ajoutées et justifiées, faute de borne fournie par
  `SCHEMA.md` : `rated_power_kw` doit être strictement positif, et
  `downtime_minutes` ne dépasse pas 20 160 minutes (14 jours), au-delà de
  quoi une valeur ressemble à une valeur sentinelle plutôt qu'à une mesure
  réelle (voir la donnée `99999` trouvée dans le fichier reçu) ;
- deux contrôles inter-colonnes (`end_at >= start_at`,
  `closed_at >= opened_at`).

Valider les fichiers **bruts** avec ces schémas échoue volontairement : c'est
ce que le pipeline utilise pour lister les anomalies (`schema.validate(df,
lazy=True)` capture toutes les violations d'un coup via
`pandera.errors.SchemaErrors.failure_cases`).

### `src/data_pipeline/rules.py` (nouveau)

Contient ce qu'un schéma par table ne peut pas exprimer :

- **doublons stricts** (`duplicate_row_mask`) : 4 lignes intégralement
  dupliquées dans `equipment.csv`, 4 dans `events.csv`, 5 dans
  `maintenance.csv` — probablement une réinjection ou un problème d'export,
  pas des équipements distincts ;
- **intégrité référentielle** (`referential_breaks`) : `events.equipment_id
  → equipment.equipment_id`, `maintenance.equipment_id →
  equipment.equipment_id`, `maintenance.event_id → events.event_id` ; une
  ligne par relation référence un identifiant `*-ORPHAN-*` inexistant ;
- **corrections non ambiguës, tracées avant/après**
  (`apply_category_fixes`) : trois variantes de casse/espace/traduction qui
  désignent sans ambiguïté une valeur déjà valide (`"Pump "` → `pump`,
  `"Incident "` → `incident`, `"Correctif"` → `corrective`). Aucune valeur
  n'est devinée : seules des variantes strictement identifiables sont
  corrigées ;
- **détection et masquage des informations personnelles**
  (`mask_pii_in_notes`) : recherche d'adresses e-mail et de numéros de
  téléphone français dans `work_order_note` par expression régulière. Deux
  occurrences trouvées sur 1 800 lignes ; le texte est masqué dans la table
  préparée, la valeur détectée reste tracée dans `output/corrections.csv`
  pour audit (ce corpus est synthétique — voir `data_pack/DATA_CARD.md`,
  « informations personnelles synthétiques »).

### `src/data_pipeline/cli.py` (réécrit)

Le point d'entrée orchestre, table par table : correction des catégories,
masquage PII, exclusion des doublons, exclusion des ruptures référentielles,
validation Pandera du reste, puis une revalidation finale des tables
retenues (pour vérifier qu'elles respectent bien le contrat déclaré). Il
écrit :

- `output/processed/{equipment,events,maintenance}.csv` — tables préparées,
  lignes en anomalie exclues, corrections appliquées ;
- `output/quarantine.csv` — anomalies exclues, au format imposé par le
  brief ;
- `output/corrections.csv` — corrections et masquages appliqués, avec valeur
  avant/après (format demandé par les « règles de travail » du starter :
  « conservez un état avant/après pour toute correction ») ;
- `output/validation_report.json` — un enregistrement par règle contrôlée
  (`rule_id`, `source`, `passed`, `affected_rows`), un résumé et la décision.

Les fichiers sources dans `data_pack/` ne sont jamais modifiés : ils sont
uniquement lus et hashés (`sha256`).

### `tests/test_rules.py` (nouveau)

Un cas valide et au moins un cas invalide par règle significative : schémas
Pandera (valeur nulle acceptée là où c'est légitime, valeur hors domaine ou
hors borne rejetée), doublons, ruptures référentielles, normalisation de
catégorie, masquage des données personnelles. `python -m pytest -q` exécute
22 tests, tous verts, sans charger aucune donnée réelle (fixtures en dur).

## Comment rejouer

```bash
cd M2/starter
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
python -m src.data_pipeline --input ../../data_pack/2026-S1 --output ./output
```

`output/` est régénéré à l'identique à chaque exécution (aucun aléa, seed non
nécessaire ici : les règles sont déterministes).

## Limites de cette implémentation

- Les règles couvrent les anomalies identifiées par inspection directe des
  trois fichiers (doublons, valeurs impossibles, catégories mal formées,
  dates incohérentes, ruptures de référence, PII simple par regex). Le brief
  indique explicitement qu'il n'est pas demandé de retrouver l'inventaire
  exact des anomalies injectées par le formateur ; d'autres cas peuvent donc
  exister sans être couverts.
- La détection d'informations personnelles est une expression régulière
  (e-mail, téléphone français) : elle ne détecte pas les noms propres seuls
  ni les adresses postales.
- Le brief M2 « online » (notebook `m2_statistiques_atlas.ipynb`, statistiques
  descriptives et visualisations Pandas/Seaborn) est un livrable séparé,
  non couvert par ce travail.
