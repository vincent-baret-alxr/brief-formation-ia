# Registre des règles — M3

## Point de départ

M3 repart de la **préparation de référence M2**
(`data_pack/2026-S1/reference_runs/m2_for_m3/`), pas d'une préparation
personnelle : c'est cette référence qui fixe les identifiants `R-EQ-*` /
`R-EVT-*` / `R-MNT-*` déjà utilisés par le starter
(`contracts.schemas.M2_RULE_IDS`) et par ses tests. Chaque règle a été
réimplémentée à partir de la condition documentée dans `regles_m2.md`, puis
vérifiée par comparaison automatique avec les effectifs de référence
(`tests/test_non_regression.py`).

## Règles héritées de M2

| Règle | Table | Statut | Contrôle | Justification |
|---|---|---|---|---|
| `R-EQ-001` | equipment | conservee | `equipment_id` unique | — |
| `R-EQ-002` | equipment | conservee | `criticality` dans le domaine fermé | — |
| `R-EQ-003` | equipment | conservee | `equipment_type` normalisé | — |
| `R-EQ-004` | equipment | conservee | `rated_power_kw` strictement positive | — |
| `R-EQ-005` | equipment | conservee | `commissioning_date` antérieure à la fin de période | — |
| `R-EQ-006` | equipment | conservee | champs descriptifs renseignés | — |
| `R-EVT-001` | events | conservee | `event_id` unique | — |
| `R-EVT-002` | events | conservee | `severity` dans le domaine fermé | — |
| `R-EVT-003` | events | conservee | `event_type` normalisé et dans le domaine | — |
| `R-EVT-004` | events | conservee | `end_at` postérieure à `start_at` | — |
| `R-EVT-005` | events | conservee | `equipment_id` présent dans la table préparée | — |
| `R-MNT-001` | maintenance | conservee | `maintenance_id` unique | — |
| `R-MNT-002` | maintenance | conservee | `event_id` présent dans la table préparée | — |
| `R-MNT-003` | maintenance | conservee | `equipment_id` présent dans la table préparée | — |
| `R-MNT-004` | maintenance | conservee | `closed_at` postérieure à `opened_at` | — |
| `R-MNT-005` | maintenance | conservee | `downtime_minutes` positive et plausible | — |
| `R-MNT-006` | maintenance | conservee | `parts_cost_eur` positive | — |
| `R-MNT-007` | maintenance | **modifiee** | `intervention_type` normalisé et dans le domaine | Le registre de référence exclut `MNT-2026S1-0912` après l'avoir normalisée (`"Correctif"` → `"corrective"`, une valeur pourtant valide une fois normalisée), alors que `R-EVT-003` traite une variante analogue (`"Incident "` → `"incident"`, ligne `EVT-2026S1-0265`) par simple normalisation, ligne conservée. Ce traitement différent d'une même famille d'anomalie (variante renvoyant sans ambiguïté vers une valeur du domaine fermé) n'est justifié nulle part dans `regles_m2.md`. M3 aligne `R-MNT-007` sur `R-EVT-003` : normalisation puis conservation, sans exclusion. Conséquence mesurée : la table `maintenance` préparée par M3 compte 1 789 lignes contre 1 788 pour la référence — la seule ligne concernée est `MNT-2026S1-0912`. |
| `R-MNT-008` | maintenance | **etendue** | absence d'information personnelle directe dans les notes | Étendue à la détection d'un nom de personne (motif capitalisé, ex. `"Nadia B."`), en plus de l'e-mail et du téléphone déjà couverts en M2 — la référence elle-même masque `"Nadia B."` dans `MNT-2026S1-1121`, ce que sa propre condition documentée (« information relative à une personne ») couvre mais que M2 n'avait pas formalisé en règle séparée. Marqueur typé par nature d'information (`[email]`, `[telephone]`, `[personne]`) plutôt qu'un jeton unique, pour que la trace dise ce qui a été retiré sans le reconstituer. |

Toutes les autres règles sont **conservées** au sens strict : même condition,
même décision, mêmes effectifs que la référence (voir non-régression
ci-dessous). Aucune règle héritée n'a été abandonnée.

## Règles ajoutées en M3

| Règle | Table | Statut | Contrôle | Justification |
|---|---|---|---|---|
| `SEN-KEY-001` | sensors | nouvelle | unicité de la clé logique `equipment_id + timestamp + sensor_name` ; arbitrage doublon strict / doublon divergent | Le fichier reçu ne déclare aucune clé primaire (SCHEMA.md) ; 10 clés dupliquées trouvées (6 strictes, 4 porteuses de deux valeurs différentes). Un doublon divergent ne peut pas être arbitré sans information supplémentaire : les deux lignes sont exclues et signalées, jamais l'une choisie arbitrairement. |
| `SEN-NAME-001` | sensors | nouvelle | `sensor_name` normalisé (casse, espace) | Trouvé par inspection : `"TEMPERATURE_C "` (40 lignes) au lieu de `temperature_c`. |
| `SEN-UNIT-001` | sensors | nouvelle | unité cohérente avec `sensor_name`, conversion vers l'unité canonique | Trouvé par inspection : 84 lignes de `temperature_c` en kelvin, 720 lignes de `pressure_bar` en kilopascal. Converties plutôt qu'exclues : la mesure reste exploitable une fois l'unité corrigée. |
| `SEN-TZ-001` | sensors | nouvelle | horodatage sans fuseau, UTC supposé | 720 horodatages reçus sans indication de fuseau. Hypothèse UTC déjà documentée par `timeseries.to_utc` ; tracée ligne par ligne plutôt qu'appliquée silencieusement (critère bloquant du brief). |
| `SEN-RANGE-001` | sensors | nouvelle | valeur dans la plage physique plausible du capteur (voir `contracts.schemas.sensor_value_ranges`), hors sentinelle | La valeur `-999` apparaît à l'identique sur les cinq capteurs (12 lignes) : signature d'une valeur sentinelle, impossible pour un courant, une pression, une vibration, une température ou une vitesse de rotation. Bornes plus larges ajoutées par ailleurs (voir `docs/diagnostic_multisource.md`) ; aucune autre valeur reçue ne les dépasse. |
| `SEN-PERIOD-001` | sensors | nouvelle | `period` dans le périmètre annoncé de la livraison (`2026-S1`) | 30 lignes portent `period = 2026-S2`, hors du périmètre de cette livraison. Ce n'est pas une erreur de mesure : la ligne est exclue de cette préparation pour être retraitée avec la livraison qui la concerne, pas mélangée à `2026-S1`. |
| `SEN-REF-001` | sensors | nouvelle | `equipment_id` présent dans la table équipements préparée | 30 lignes référencent `EQ-ORPHAN-777`, absent de `equipment.csv`, sur le même schéma que les identifiants `*-ORPHAN-*` déjà rencontrés en M2. |
| `SEN-NULL-001` | sensors | nouvelle | valeur manquante signalée, ligne conservée | 40 lignes sans `value` : une mesure non relevée n'est pas une erreur de qualité, mais doit rester visible (elle réduit la complétude d'une série). |

## Non-régression

Démontrée par `tests/test_non_regression.py`, pas seulement affirmée : le
test recharge les trois fichiers CSV reçus en M2, rejoue `prepare_equipment`,
`prepare_events`, `prepare_maintenance` (`src/data_pipeline/m2_rules.py`) et
compare, règle par règle, le nombre de lignes affectées à
`data_pack/2026-S1/reference_runs/m2_for_m3/analyses/rapport_validation_m2.json`.
Toutes les règles conservées reproduisent exactement l'effectif de
référence ; seule `R-MNT-007` diverge, de la façon décrite ci-dessus et
vérifiée explicitement par un test dédié
(`test_the_declared_divergence_is_the_only_one`).

Voir aussi `output/registre_regles.csv` / `.md`, générés par
`python -m src.data_pipeline` (table machine, identique au contenu ci-dessus).

## Décisions employées

| Décision | Sens dans la pipeline |
|---|---|
| `doublon_supprime` | Ligne strictement identique à une autre déjà retenue : la copie surnuméraire est retirée, l'originale reste. |
| `exclue` | Ligne retirée de la table préparée (référence rompue, domaine fermé violé sans normalisation possible, valeur impossible, doublon de clé non arbitrable, hors périmètre de période). |
| `champ_neutralise` | Ligne conservée, un seul champ vidé et tracé (valeur présente mais invalide : puissance négative, date future, chronologie inversée, coût négatif). |
| `valeur_normalisee` | Valeur corrigée de façon déterministe et sans ambiguïté (casse, espace, traduction, conversion d'unité, horodatage sans fuseau supposé UTC). |
| `conserve_signale` | Ligne conservée telle quelle, anomalie signalée pour information ou expertise (champ optionnel manquant, durée d'arrêt extrême mais non négative, mesure non relevée). |
| `pseudonymise` | Fragment de texte identifiant une personne remplacé par un marqueur typé (`[email]`, `[telephone]`, `[personne]`), sans reconstituer l'information. |
