# Rapport d'audit des données DiagOps — M2

## Méthode utilisée

Pipeline Python (pandas + Pandera) sous `src/data_pipeline/`, exécuté avec :

```bash
python -m src.data_pipeline --input ../../data_pack/2026-S1 --output ./output
```

Environnement : Python 3.11, `requirements.lock` du starter. Les contrôles
sont rejoués intégralement à chaque exécution ; les fichiers reçus
(`data_pack/2026-S1/{equipment,events,maintenance}/...`) ne sont jamais
modifiés. Le détail des règles et du code est expliqué dans
[`README.md`](README.md).

## Règles contrôlées

| `rule_id` | Table | Raison métier |
|---|---|---|
| `EQUIPMENT_ID` / `EVENT_ID` / `MAINTENANCE_ID` unicité | les trois | un identifiant doit désigner une seule ligne |
| `DUPLICATE_ROW` | les trois | une ligne strictement identique à une autre n'apporte pas d'information et fausse les comptages |
| `*_ISIN_...` (catégories) | les trois | `equipment_type`, `site_id`, `criticality`, `event_type`, `severity`, `intervention_type`, `outcome` sont des domaines fermés (`contracts/schemas.py`) |
| `COMMISSIONING_DATE_...FUTUR` | equipment | un équipement ne peut pas être mis en service dans le futur |
| `RATED_POWER_KW_...POSITIF` | equipment | une puissance nominale négative est physiquement impossible |
| `UNKNOWN_EQUIPMENT_ID` | events, maintenance | référence vers un équipement qui n'existe pas dans `equipment.csv` |
| `UNKNOWN_EVENT_ID` | maintenance | référence vers un événement qui n'existe pas dans `events.csv` |
| `LIGNE_END_AT_...START_AT` | events | une fin ne peut pas précéder un début |
| `LIGNE_CLOSED_AT_...OPENED_AT` | maintenance | une clôture ne peut pas précéder une ouverture |
| `DOWNTIME_MINUTES_...NEGATIF` | maintenance | une indisponibilité négative est impossible |
| `DOWNTIME_MINUTES_...SEUIL_PLAUSIBLE` (ajoutée) | maintenance | borne de 20 160 min (14 jours) ajoutée faute de borne fournie ; motivée par la présence d'une valeur `99999`, incohérente avec toute intervention réelle du corpus |
| `PARTS_COST_EUR_...` | maintenance | un coût de pièces négatif est impossible |
| `*_CATEGORY_NORMALIZED` | les trois | variante de casse/espace/traduction sans ambiguïté (corrigée, pas exclue) |
| `PII_DETECTED_IN_NOTE` | maintenance | e-mail ou téléphone détecté dans `work_order_note` (masqué, pas exclu) |

## Résultats

### 1. Que représente chaque fichier et comment les trois sources sont-elles reliées ?

- `equipment.csv` (420 lignes) : un équipement par ligne, identifié par
  `equipment_id`, avec son type, son site, sa date de mise en service, sa
  criticité, son fabricant et sa puissance nominale.
- `events.csv` (520 lignes) : un événement par ligne (incident, intervention,
  observation, alerte), rattaché à un équipement, avec une fenêtre
  temporelle et une sévérité.
- `maintenance_history.csv` (1 800 lignes) : une intervention de maintenance
  par ligne, rattachée à un équipement et à un événement, avec durée
  d'indisponibilité, temps de travail, coût de pièces et une note libre.

Relations : `events.equipment_id → equipment.equipment_id`,
`maintenance_history.equipment_id → equipment.equipment_id`,
`maintenance_history.event_id → events.event_id`.

### 2. Les données nécessaires au cas DiagOps sont-elles présentes et lisibles ?

Oui : les trois fichiers sont lisibles par `pandas.read_csv` sans option
particulière, les volumes reçus (420 / 520 / 1 800) correspondent à ceux
annoncés par `data_pack/DATA_CARD.md`, et les colonnes obligatoires
(`equipment_id`, `event_id`, `maintenance_id`, etc.) sont présentes sur 100 %
des lignes.

### 3. Quels problèmes d'identifiants, de doublons ou de relations avez-vous détectés ?

- Doublons stricts (ligne entière identique) : **4** dans `equipment.csv`,
  **4** dans `events.csv`, **5** dans `maintenance_history.csv`.
- Ruptures de référence : **1** événement référence un équipement inexistant
  (`EQ-ORPHAN-999`), **1** intervention référence un équipement inexistant
  (`EQ-ORPHAN-998`), **1** intervention référence un événement inexistant
  (`EVT-ORPHAN-999`).

Aucun `equipment_id`/`event_id`/`maintenance_id` n'est manquant ou dupliqué
en dehors de ces doublons de ligne complète.

### 4. Quelles règles métier ne sont pas respectées ?

- `equipment.csv` : 1 puissance nominale négative (`-12.5` kW), 1 date de
  mise en service future (`2031-04-17`), 1 variante de catégorie
  (`"Pump "`).
- `events.csv` : 1 sévérité hors domaine (`URGENT`), 1 événement dont la fin
  précède le début, 1 variante de catégorie (`"Incident "`).
- `maintenance_history.csv` : 1 indisponibilité négative (`-45` min), 1
  indisponibilité de `99999` min (valeur sentinelle implausible), 1 coût de
  pièces négatif (`-350 €`), 1 intervention dont la clôture précède
  l'ouverture, 1 variante de catégorie (`"Correctif"`).

### 5. Quelles anomalies peuvent être corrigées de manière certaine ?

Les trois variantes de catégorie (`"Pump "` → `pump`, `"Incident "` →
`incident`, `"Correctif"` → `corrective`) : la casse, l'espace ou la
traduction ne laissent aucune ambiguïté sur la valeur du domaine fermé
visée. Corrigées et tracées avant/après dans `output/corrections.csv`.

### 6. Quelles anomalies doivent être mises à l'écart ou examinées par un expert métier ?

Toutes les autres : doublons (mise à l'écart, la ligne conservée suffit),
ruptures référentielles (mise à l'écart, la ligne ne peut être rattachée à
rien), et les valeurs métier impossibles ou incohérentes (puissance et coût
négatifs, date future, sévérité `URGENT`, indisponibilité négative ou
sentinelle, dates de clôture antérieures à l'ouverture) : ces dernières
signalent probablement une erreur de saisie ou d'export, mais la correction
supposerait de deviner une valeur (ex. inverser le signe, ou choisir entre
`high` et `critical` pour `URGENT`) — décision laissée à un expert métier,
ligne isolée en quarantaine (`decision = a_examiner`).

### 7. Les notes contiennent-elles des informations relatives à des personnes et quelle décision prenez-vous à leur sujet ?

Oui : 2 notes sur 1 800 contiennent une information personnelle détectable
par expression régulière — un numéro de téléphone (`MNT-2026S1-1121`) et une
adresse e-mail (`MNT-2026S1-1334`). Ce ne sont pas des identifiants
techniques nécessaires à DiagOps (contrairement à `equipment_id`,
`event_id`). Décision : masquage du texte détecté dans la table préparée
(`[donnée personnelle masquée]`), conservation de la ligne (le reste de la
note reste exploitable), trace de la valeur originale dans
`output/corrections.csv` pour audit. Cette recherche est fondée sur une
expression régulière (e-mail, téléphone français) ; elle ne couvre pas les
noms propres isolés ni les adresses postales et ne doit donc pas être
présentée comme exhaustive.

### 8. Certaines catégories de sites, d'équipements, de criticité ou de sévérité sont-elles peu représentées ?

Sur `equipment.csv` préparé (414 lignes) :

- sites : SITE-NORD 172, SITE-SUD 135, SITE-EST 91, **SITE-OUEST 16** —
  nettement sous-représenté (< 4 % du parc) ;
- types d'équipement les moins représentés : `lift` (5), `steam_unit` (5),
  `motor` (7), `packaging_machine` (7), `gearbox` (8), `dryer` (8), contre
  57 pour `pump` ;
- criticité : `critical` (46) est la catégorie la moins représentée, sans
  être extrême (~11 % du parc).

Toute statistique croisant ces catégories avec un faible effectif (ex.
`SITE-OUEST`, `lift`, `steam_unit`) doit être lue comme indicative, pas
comme une conclusion fiable.

### 9. Les erreurs historiques de M1 semblent-elles plus fréquentes dans certaines catégories, et quelles sont les limites de ce constat ?

La matrice `data_pack/2026-S1/reference_runs/m1_for_m2/analyses/matrice_erreurs_m1.csv`
(80 exemples de validation M1, référence commune déjà consultée) a été jointe
à `equipment.csv` préparé sur `equipment_id`. **7 des 80 lignes** ne trouvent
pas d'équipement correspondant et sont donc exclues du croisement.

Sur les 73 lignes restantes, le taux d'erreur de sévérité global est de
15,0 % ; par sous-groupe :

| Regroupement | Effectif | Taux d'erreur `severity` |
|---|---:|---:|
| `criticality = critical` | 7 | 28,6 % |
| `criticality = low` | 9 | 22,2 % |
| `criticality = high` | 26 | 15,4 % |
| `criticality = medium` | 31 | 12,9 % |
| `equipment_type = fan` | 7 | 57,1 % |
| `equipment_type = press` | 8 | 50,0 % |
| `equipment_type = pump` | 13 | 15,4 % |
| `site_id = SITE-OUEST` | 2 | 50,0 % |
| `site_id = SITE-SUD` | 24 | 25,0 % |
| `site_id = SITE-EST` | 12 | 8,3 % |

Les taux les plus élevés (`fan`, `press`, `SITE-OUEST`) portent sur des
effectifs de 2 à 8 exemples : une différence de 1 ou 2 cas change fortement
le pourcentage affiché. **Ce constat ne démontre ni qu'un type d'équipement
ni qu'un site cause davantage d'erreurs** : il s'agit d'un comptage simple
sur un historique déjà consulté, à confirmer (ou non) sur des volumes plus
larges, pas d'une analyse causale.

### 10. Les données préparées peuvent-elles être transmises à M3, et sous quelles conditions ?

Oui, sous conditions (voir décision ci-dessous) : les tables préparées
(`output/processed/*.csv`) sont valides au regard des contrats déclarés
(`PROCESSED_TABLE_SCHEMA_VALID` = vrai pour les trois tables), et
`output/quarantine.csv` documente individuellement chaque ligne écartée.

## Couverture et erreurs historiques M1

Voir question 8 (représentativité) et question 9 (croisement M1). Aucune
conclusion causale n'est tirée ; les effectifs faibles sont signalés
explicitement.

## Limites

- Les règles couvrent les anomalies trouvées par inspection directe des
  fichiers ; le brief indique que l'inventaire exact des anomalies injectées
  par le formateur n'est pas distribué et n'a pas vocation à être retrouvé
  en totalité.
- La détection PII est une expression régulière (e-mail, téléphone
  français), pas une revue exhaustive des notes.
- Le croisement avec la matrice d'erreurs M1 porte sur un historique déjà
  consulté (80 exemples) ; il ne doit pas servir à ajuster ou reconduire une
  évaluation M1.
- `commissioning_date` est comparée à la date d'exécution du pipeline : un
  ré-exécution à une date ultérieure peut légèrement changer le résultat de
  la règle « date future » si la donnée n'est pas corrigée entre-temps.

## Décision

**Statut : `utilisable sous conditions`.**

24 lignes sur 2 740 (0,9 %) ont été isolées en quarantaine
(`output/quarantine.csv`) : 13 doublons stricts, 3 ruptures d'intégrité
référentielle, 8 valeurs métier impossibles ou incohérentes (puissance et
coût négatifs, date future, sévérité hors domaine, indisponibilité négative
ou sentinelle, chronologie inversée). 5 valeurs ont été corrigées ou masquées
et tracées (`output/corrections.csv`) : 3 variantes de catégorie, 2
informations personnelles.

Conditions avant intégration en M3 :

- les 24 lignes de `output/quarantine.csv` doivent être tranchées par un
  expert métier (correction, exclusion définitive, ou confirmation) avant
  toute utilisation où elles compteraient ;
- les catégories sous-représentées identifiées en question 8
  (`SITE-OUEST`, `lift`, `steam_unit`, `motor`, `packaging_machine`,
  `gearbox`, `dryer`) doivent être signalées dans toute analyse qui les
  utilise isolément ;
- le constat de la question 9 ne doit pas être présenté comme une cause
  d'erreur du modèle M1.

M2 statue sur l'état des données, pas sur la promotion du modèle M1.
