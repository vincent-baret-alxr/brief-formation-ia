# DiagOps Data Pack — schema

Statut : support apprenant.

Ce document decrit les tables et fichiers fournis pour les travaux DiagOps.
Les donnees sont synthetiques et servent uniquement de support de formation.

## Identifiants communs

Les sources sont reliees par des identifiants stables :

| Champ | Role |
|---|---|
| `equipment_id` | identifiant unique d'un equipement |
| `event_id` | identifiant unique d'un incident, d'une intervention ou d'un evenement suivi |
| `report_id` | identifiant unique d'un rapport technicien |
| `image_id` | identifiant unique d'une image de defaut |
| `timestamp` | horodatage ISO 8601 |
| `period` | periode de livraison des donnees, ex. `2026-S1` |

## Contrat DiagOps

Les modules utilisent le meme contrat de sortie pour les diagnostics :

```json
{
  "equipment_id": "EQ-0001",
  "symptom": "vibration anormale au demarrage",
  "severity": "low|medium|high|critical",
  "failure_hypothesis": "roulement use ou desalignement",
  "recommended_action": "inspection prioritaire du palier",
  "confidence": 0.72,
  "evidence": ["rapport RPT-0001", "mesure vibration elevee"],
  "requires_human_review": true
}
```

## Entites

### `reports`

Rapports textuels rediges par des techniciens.

| Champ | Type | Description |
|---|---|---|
| `report_id` | string | identifiant du rapport |
| `equipment_id` | string ou null | equipement concerne, si identifiable |
| `event_id` | string ou null | evenement associe, si connu |
| `timestamp` | datetime | date de saisie |
| `technician_note` | string | texte libre du rapport |
| `source_channel` | string | canal de saisie |
| `period` | string | periode de disponibilite |

Mise a disposition initiale : `2026-S1/reports/`.

### `annotated_diagnostics`

Sous-ensemble annote utilise en M1 pour entrainer et evaluer le modele DiagOps.

| Champ | Type | Description |
|---|---|---|
| `annotation_id` | string | identifiant de l'annotation |
| `report_id` | string | rapport source |
| `equipment_id` | string ou null | equipement concerne, si identifiable |
| `event_id` | string ou null | evenement associe, si connu |
| `input_text` | string | contexte donne au modele : identifiant equipement disponible, puis rapport technicien |
| `expected_output` | object | JSON DiagOps attendu |
| `split` | enum | `train` ou `test` |
| `period` | string | periode source |

Volume cible :

- `train` : environ 400 exemples ;
- `test` : environ 100 exemples.

L'identifiant d'equipement present dans le rapport structure est inclus dans
`input_text`. La tache M1 ne demande donc pas d'inventer une cle interne a
partir d'un nom d'usage tel que `Pompe P-204`.

Mise a disposition initiale : M1.

### `equipment`

Inventaire des equipements suivis.

| Champ | Type | Description |
|---|---|---|
| `equipment_id` | string | identifiant equipement |
| `equipment_type` | string | famille d'equipement |
| `site_id` | string | site ou atelier |
| `commissioning_date` | date | mise en service |
| `criticality` | enum | `low`, `medium`, `high`, `critical` |
| `manufacturer` | string ou null | fabricant declare |
| `rated_power_kw` | number ou null | puissance nominale en kW |

Mise a disposition initiale : M2. Volume distribue : 420 lignes, anomalies
pedagogiques incluses.

### `sensors`

Mesures temporelles issues des equipements.

| Champ | Type | Description |
|---|---|---|
| `equipment_id` | string | equipement mesure |
| `timestamp` | datetime | date de mesure |
| `sensor_name` | string | nom du capteur |
| `value` | number | valeur mesuree |
| `unit` | string | unite |
| `period` | string | periode de disponibilite |

Aucune colonne ne porte d'identifiant de ligne. La clé logique d'une mesure est
le triplet `equipment_id + timestamp + sensor_name`. Elle doit être reconstruite
par le travail du module ; le fichier reçu ne garantit ni son unicité, ni
l'homogénéité du format d'horodatage, ni la cohérence entre `sensor_name` et
`unit`.

Le pas d'échantillonnage nominal de la livraison `2026-S1` est de six heures. Le
parc instrumenté est un sous-ensemble du parc décrit par `equipment.csv` : la
couverture est partielle par construction et doit être décrite avant toute
conclusion.

Mise a disposition initiale : M3, dans `2026-S1/sensors/sensor_readings.csv`.
Volume distribue : 50 401 lignes, anomalies pedagogiques incluses.

### `sensors_control`

Lot de controle capteurs, ouvert au brief 2 de M3.

Le schema est celui de `sensor_readings`. Une partie des lignes est fabriquee ;
la proportion et les procedes ne sont pas communiques.

| Fichier | Colonne `provenance` | Role |
|---|---|---|
| `2026-S1/sensors_control/control_batch.csv` | absente | lot a qualifier |
| `2026-S1/sensors_control/control_sample.csv` | presente | echantillon disjoint |

Dans `control_sample.csv`, `provenance` ne prend que les valeurs `réelle` et
`fabriquée` : le lot declare l'authenticite d'une ligne, jamais le procede qui
l'a produite. L'echantillon est disjoint du lot a qualifier ; aucune ligne de
`control_sample.csv` ne figure dans `control_batch.csv`.

Les lignes reelles proviennent de `sensor_readings.csv` et portent donc les
anomalies de qualite de cette livraison. Une ligne signalee par un controle de
qualite n'est pas necessairement une ligne fabriquee.

Mise a disposition initiale : M3, brief 2.
Volume distribue : 6 000 lignes pour `control_batch.csv`, 720 lignes pour
`control_sample.csv`.

### `m4_sensor_model_evaluation`

Lots de fenêtres capteurs utilisés pour comparer la baseline M3 et les modèles
simples du M4.

| Champ | Type | Description |
|---|---|---|
| `window_id` | string | groupe indivisible de 30 mesures consécutives |
| `equipment_id` | string | équipement de la fenêtre |
| `timestamp` | datetime | horodatage de la mesure |
| `sensor_name` | string | capteur observé |
| `value` | number ou vide | valeur brute |
| `unit` | string | unité déclarée |
| `period` | string | période de livraison |
| `provenance` | enum | `réelle` ou `fabriquée`, calibration uniquement |

`sensor_calibration.csv` expose la cible. `sensor_test.csv` ne l’expose pas :
l’oracle reste côté formateur jusqu’au gel du candidat. Une partition ne sépare
jamais les lignes d’un même `window_id`. La provenance ne qualifie ni la qualité
d’une mesure, ni une anomalie métier, ni une panne future.

### `maintenance_history`

Historique des interventions et decisions de maintenance.

| Champ | Type | Description |
|---|---|---|
| `maintenance_id` | string | identifiant unique d'une intervention |
| `event_id` | string | evenement de maintenance |
| `equipment_id` | string | equipement concerne |
| `opened_at` | datetime | ouverture |
| `closed_at` | datetime | cloture, si applicable |
| `intervention_type` | string | type d'intervention |
| `outcome` | string | resultat |
| `downtime_minutes` | integer | indisponibilite estimee |
| `labor_hours` | number ou null | temps de travail consigne |
| `parts_cost_eur` | number ou null | cout des pieces en euros |
| `parts_replaced_count` | integer | nombre de pieces remplacees |
| `work_order_note` | string | note libre synthetique associee au bon de travail |
| `period` | string | periode de disponibilite |

Mise a disposition initiale : M2. Volume distribue : 1 800 lignes, anomalies
pedagogiques incluses.

### `events`

Evenements permettant de relier les rapports, capteurs, interventions et images.

| Champ | Type | Description |
|---|---|---|
| `event_id` | string | identifiant evenement |
| `equipment_id` | string | equipement concerne |
| `start_at` | datetime | debut |
| `end_at` | datetime | fin, si applicable |
| `event_type` | string | incident, intervention, observation, alerte |
| `severity` | enum | `low`, `medium`, `high`, `critical` |
| `period` | string | periode de disponibilite |

Mise a disposition initiale : M2. Volume distribue : 520 lignes, anomalies
pedagogiques incluses.

## Livraison candidate M2

Le dossier `2026-S1/m2_candidate_release/` est une livraison incrémentale à
qualifier. Les règles d'intégration ne sont pas identiques pour les trois
fichiers :

- `equipment_update.csv` peut contenir de nouveaux équipements ou des mises à
  jour d'identifiants déjà présents ;
- `events_batch_02.csv` contient des événements destinés à être ajoutés sans
  collision de `event_id` ;
- `maintenance_batch_02.csv` contient des interventions destinées à être
  ajoutées sans collision de `maintenance_id`.

Les deux premiers fichiers reprennent les colonnes de leur entité. Le fichier
de maintenance annonce en plus la colonne facultative `source_system`, de type
string, qui identifie le système ayant exporté la ligne. L'acceptation de cette
évolution et la qualification du contenu font partie du complément M2.

La livraison candidate ne doit pas être confondue avec la version publiée des
tables et ne doit pas être intégrée automatiquement.

### `feedback`

Retours des techniciens apres utilisation de DiagOps.

| Champ | Type | Description |
|---|---|---|
| `feedback_id` | string | identifiant du retour |
| `report_id` | string | rapport ou prediction concerne |
| `event_id` | string | evenement associe |
| `timestamp` | datetime | date du retour |
| `user_decision` | string | decision humaine |
| `model_helpfulness` | integer | note de 1 a 5 |
| `comment` | string | commentaire libre |

### `knowledge_documents`

Manifeste du corpus documentaire utilise par le RAG a partir de M4.

| Champ | Type | Description |
|---|---|---|
| `document_id` | string | identifiant stable du document |
| `title` | string | titre lisible |
| `revision` | string | version ou revision de la source |
| `effective_at` | date ou null | date d'effet connue |
| `source_type` | string | manuel, procedure, consigne ou retour d'experience |
| `asset_path` | string | chemin relatif sous `knowledge/documents/` |
| `license` | string | droit de reutilisation ou regime interne |
| `sensitivity` | string | public, interne ou restreint |
| `status` | string | active, superseded, draft ou quarantined |
| `supersedes_document_id` | string ou vide | document remplacé par cette révision |
| `allowed_roles` | liste `;` | rôles autorisés à recevoir le contenu |
| `checksum_sha256` | string | empreinte du fichier distribue |

Un document sans droit d'usage, niveau de sensibilite ou checksum n'est pas
admis dans l'index. Le manifeste decrit une source documentaire ; il ne contient
ni chunk, ni embedding, ni sortie de modele.

### `rag_evaluation_questions`

Jeu gele servant a comparer retrieval et generation fondee sur des preuves.

| Champ | Type | Description |
|---|---|---|
| `eval_id` | string | identifiant stable de la question |
| `question` | string | question adressee au systeme |
| `role` | string | rôle au nom duquel la question est posée |
| `expected_document_ids` | liste de strings ou null | sources attendues ; null pour un test scellé |
| `answerable` | boolean ou null | étiquette visible en calibration, scellée en test |
| `risk_tags` | liste de strings | injection, obsolescence, conflit ou autre risque |
| `split` | string | calibration ou test |
| `label_visibility` | string | visible ou sealed |

Les questions du split `test` sont visibles, mais leurs labels ne le sont pas.
Le formateur restitue les métriques après gel du pipeline. Une question non
répondable attend un refus motivé, jamais une réponse sans preuve.

### `images`

Images de defauts industriels issues d'un corpus externe documente.

| Champ | Type | Description |
|---|---|---|
| `image_id` | string | identifiant image |
| `equipment_id` | string | equipement ou famille d'equipement |
| `event_id` | string | evenement associe, si applicable |
| `image_path` | string | chemin relatif |
| `asset_source` | string | source externe documentee |
| `label` | string | etiquette disponible dans le corpus |

Mise a disposition initiale : M7.

## Contrat de provenance

A partir de M3, toute table de mesures produite par un module et transmise a un
autre declare l'origine de chaque ligne. Deux colonnes portent ce contrat.

| Champ | Type | Description |
|---|---|---|
| `provenance` | string | `réelle`, `synthétique` ou `augmentée` |
| `procedure_id` | string | procede ayant produit la ligne ; vide si `réelle` |

- `réelle` : la ligne provient d'une livraison du pack sans modification de
  `value`, `unit` ni `timestamp`. Une ligne reelle peut etre anormale : la
  provenance decrit une origine, pas une qualite.
- `augmentée` : la ligne derive d'une ligne reelle identifiable par une
  transformation deterministe — bruit, mise a l'echelle, decalage temporel.
- `synthétique` : la ligne ne derive d'aucune ligne reelle identifiable.

Un `procedure_id` renvoie a une entree d'un registre des procedes, livre avec la
table, qui indique la technique employee, ses parametres, et ce que le procede
conserve et detruit de la distribution d'origine.

Une table derivee d'une population mixte n'herite pas d'une provenance de ligne :
elle declare la composition de sa population. Un agregat calcule sur des lignes
de provenances differentes est inexploitable tant que cette composition n'est pas
publiee.

## Periodes

Les donnees sont organisees par periodes temporelles :

- `2026-S1`
- `2026-S2` — extension M5 facultative tant qu'elle n'est pas déclarée prête
  dans `MANIFEST.yaml`
- `2027-S1`

Le sens analytique de chaque periode doit etre determine par le travail realise
dans les modules.
