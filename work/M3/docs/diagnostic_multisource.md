# Diagnostic multi-source DiagOps — M3

## Point de départ retenu

La **préparation de référence M2**
(`data_pack/2026-S1/reference_runs/m2_for_m3/`), pas une préparation
personnelle. Raison : cette référence fixe déjà les identifiants de règles
(`R-EQ-*`, `R-EVT-*`, `R-MNT-*`) repris par le starter M3
(`contracts.schemas.M2_RULE_IDS`, tests fournis) ; en repartir permet de
démontrer une non-régression vérifiable par comparaison directe à un
document déjà publié, plutôt que par comparaison à une préparation
personnelle non disponible à un tiers relisant ce dépôt. Voir
`docs/registre_regles.md` pour le détail, y compris les deux écarts
assumés (`R-MNT-007` modifiée, `R-MNT-008` étendue).

## Méthode utilisée

Pipeline Python (pandas + Pandera), `src/data_pipeline/` :
`m2_rules.py` (règles héritées), `sensor_rules.py` (règles temporelles
nouvelles), `contracts/schemas.py` (schémas de validation et
rapprochement). Environnement : Python 3.11, `requirements.lock` du
starter.

```bash
cd work/M3
python -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
python -m src.data_pipeline --input ../../data_pack/2026-S1 --output ./output
```

Temps d'exécution mesuré (`time`) : **1,7 s** pour les quatre sources
(420 + 520 + 1 800 + 50 401 lignes). À 30× ce volume sur `sensor_readings.csv`
(couverture instrumentale complète du parc, 416 équipements au lieu de 36),
le temps resterait de l'ordre de quelques dizaines de secondes avec
l'implémentation actuelle (opérations vectorisées pandas, à l'exception des
boucles d'écriture de la quarantaine qui itèrent sur les lignes en
anomalie — donc sur un sous-ensemble, pas sur la table entière). Le
rapprochement mesures ↔ événements (`align_measures_to_events`) est un
produit filtré par équipement puis par fenêtre : il resterait praticable sur
l'ensemble du parc, mais deviendrait coûteux en mémoire si le nombre
d'événements ou la densité de mesures croissait d'un ordre de grandeur
supplémentaire — à surveiller, pas encore un problème observé.

## Cadrage de la source capteurs

- **Grain** : une ligne = une mesure d'un capteur, sur un équipement, à un
  instant donné.
- **Clé logique** : `equipment_id + timestamp + sensor_name` (hypothèse du
  starter). Vérifiée, pas acquise : 10 clés apparaissent en double avant
  préparation (voir question 5).
- **Séries présentes** : 72 séries (couples équipement × capteur) sur 37
  `equipment_id` reçus (36 après exclusion de l'équipement inconnu), 5 noms
  de capteur (`current_a`, `pressure_bar`, `rpm`, `temperature_c`,
  `vibration_mm_s`).
- **Période couverte** : les horodatages bruts s'étendent du
  2025-12-28T06:00Z au 2026-07-04T12:00Z — au-delà de la période annoncée
  `2026-S1` (janvier-juin 2026) de quelques jours de part et d'autre, plus
  30 lignes explicitement étiquetées `period = 2026-S2`. Voir question 2.
- **Pas d'échantillonnage** : médiane exactement égale à 6 h sur les 72
  séries (aucune variation de médiane d'une série à l'autre), conforme au
  pas nominal annoncé par `SCHEMA.md`. 6 séries présentent un écart maximal
  supérieur à 24 h (jusqu'à 270 h, ~11 jours, pour `EQ-MIX-159` /
  `current_a`) : des interruptions d'échantillonnage existent, localisées
  série par série dans `output/series_overview_raw.csv`.
- **Volumétrie** : 50 401 lignes reçues, ~1,4 Mo — modeste, mais environ 30
  fois la plus grande table de M2 (`maintenance_history.csv`, 1 800 lignes).

## Résultats

### 1. Que représente une ligne de `sensor_readings.csv` et quelle clé identifie une mesure ?

Voir « Cadrage » ci-dessus.

### 2. Quelle période et quel pas d'échantillonnage la source couvre-t-elle réellement, par rapport à ce qui est annoncé ?

Annoncé : livraison `2026-S1`, pas nominal 6 h (`SCHEMA.md`). Observé : pas
médian effectivement 6 h sur toutes les séries — conforme. Période : les
horodatages bruts débordent la période annoncée de quelques jours avant le
1er janvier et après le 30 juin 2026 (débordement mineur, cohérent avec un
export calé sur des bornes de semaine plutôt que sur les bornes exactes du
semestre), et 30 lignes portent une étiquette `period = 2026-S2` clairement
hors périmètre. Ces 30 lignes sont exclues de cette préparation
(`SEN-PERIOD-001`, décision `exclue`) : elles ne sont pas fausses, seulement
hors du périmètre de la livraison `2026-S1` traitée ici.

### 3. Quelle part du parc est instrumentée, et quels sites, types ou criticités sont absents ou sous-représentés ?

36 équipements sur 416 (8,7 %). Voir `docs/couverture_et_risques.md` pour le
détail chiffré : `SITE-OUEST` n'a aucune couverture, 7 types d'équipement
sur 18 n'en ont aucune (dont `press`, 34 unités), et 70 % des équipements
`critical` restent non instrumentés malgré un taux d'instrumentation plus
élevé pour cette criticité que pour les autres.

### 4. L'existence, la disponibilité et l'accès de cette source sont-ils vérifiés, et que proposez-vous pour les équipements qu'elle ne couvre pas ?

Existence et lisibilité vérifiées : le fichier est présent, lisible par
pandas sans option particulière, le volume reçu (50 401 lignes) correspond à
celui annoncé par `data_pack/DATA_CARD.md`. Ce que ce diagnostic **ne peut
pas** vérifier depuis le seul fichier reçu : qui produit réellement l'export,
à quelle fréquence il est régénéré en production, ni ce qui se passe
opérationnellement si une livraison manque (pas d'historique de livraisons
disponible dans ce corpus pédagogique synthétique) — point à lever auprès de
l'exploitation avant tout usage réel (voir `docs/flux_et_cycle_de_vie.md`).

Pour les 380 équipements non instrumentés : la seule source de substitution
disponible dans le data pack est `maintenance_history.csv`
(`downtime_minutes`, `outcome`, notes libres), qui documente un état
*a posteriori* et ponctuel, pas une mesure continue — elle ne remplace pas
un capteur et ne permet pas de reconstituer une tendance entre deux
interventions. Aucune autre source de remplacement n'est disponible dans ce
data pack. Solution retenue : **aucune substitution automatique** ; les
équipements non instrumentés restent explicitement hors du périmètre de
toute analyse fondée sur `sensor_readings.csv`, et cette absence doit être
répétée dans chaque document qui en fait usage plutôt que comblée
silencieusement.

### 5. Quels défauts propres à une série temporelle avez-vous détectés, et comment les avez-vous quantifiés ?

Détectés et quantifiés par `sensor_rules.py`, exécuté sur les 50 401 lignes
reçues :

| Défaut | Quantification | Règle |
|---|---:|---|
| Doublons de clé logique | 10 clés dupliquées (6 strictes, 4 divergentes) | `SEN-KEY-001` |
| Nom de capteur mal formé | 40 lignes (`"TEMPERATURE_C "`) | `SEN-NAME-001` |
| Unité incohérente avec le capteur | 804 lignes (720 pression en kPa, 84 température en K) | `SEN-UNIT-001` |
| Horodatage sans fuseau | 720 lignes | `SEN-TZ-001` |
| Valeur sentinelle (`-999`) | 12 lignes, réparties sur les 5 capteurs | `SEN-RANGE-001` |
| Hors périmètre de période | 30 lignes | `SEN-PERIOD-001` |
| Équipement référencé inconnu | 30 lignes (`EQ-ORPHAN-777`) | `SEN-REF-001` |
| Valeur manquante | 40 lignes | `SEN-NULL-001` |
| Interruption d'échantillonnage > 24 h | 6 séries sur 72 | mesuré, non bloquant |
| Séquence de valeurs figées (≥ 6 mesures identiques consécutives) | 1 série (`EQ-PUMP-171` / `vibration_mm_s`, 84 mesures identiques sur 19 jours) | mesuré, voir question 6 |

### 6. Quelles variations atypiques sont des erreurs, lesquelles sont des mesures réelles, et sur quoi vous appuyez-vous pour trancher ?

**Cas 1 — valeur sentinelle `-999` (erreur, certaine).** Trouvée à
l'identique sur les 5 capteurs, 12 fois. Une pression, une vibration, un
courant, une vitesse de rotation ou une température ne peuvent pas être
négatifs à cette magnitude ; la répétition exacte de `-999` sur des
grandeurs physiquement sans rapport signe une valeur d'export ou de capteur
en défaut, pas une mesure. Décision : exclusion (`SEN-RANGE-001`).

**Cas 2 — séquence figée, `EQ-PUMP-171` / `vibration_mm_s` (probable
erreur, mais non certaine).** 84 mesures strictement identiques d'affilée du
12 avril au 1er mai 2026 (19 jours), alors que la vibration d'une pompe en
fonctionnement varie normalement mesure à mesure. Vérification croisée :
aucune intervention de maintenance sur cet équipement ne recouvre cette
période (les 10 interventions connues pour `EQ-PUMP-171` se concentrent
autour du 15 janvier et du 7-12 juin 2026, voir
`output/processed/maintenance.csv`), donc rien n'indique un arrêt planifié
qui expliquerait une lecture stable. Décision : **conservée mais signalée**,
pas exclue — la valeur elle-même reste dans une plage physiquement
plausible, seule sa répétition est suspecte, et l'exclure supprimerait un
signal potentiellement utile (capteur figé = maintenance à prévoir) sans
certitude suffisante pour trancher automatiquement. Table complète dans
`output/aggregates/frozen_runs.csv`, à transmettre à un expert métier.

**Cas 3 — doublon de clé divergent, `EQ-CHILL-115` / `temperature_c` à
`2026-03-13T18:00:00Z` (indécidable).** Deux lignes, même clé logique,
valeurs 55,72 °C et 66,45 °C. Rien dans `events.csv` ou
`maintenance_history.csv` ne permet de dire laquelle est la bonne mesure (2
événements et 4 interventions existent pour cet équipement, mais aucun n'est
horodaté à cet instant précis). Décision : les deux lignes sont exclues
(`SEN-KEY-001`, décision `exclue`), pas arbitrées par un choix arbitraire
(critère bloquant du brief : « doublon de clé résolu sans arbitrage
tracé »).

### 7. Quelles règles M2 avez-vous conservées, modifiées, étendues ou abandonnées, et comment démontrez-vous l'absence de régression ?

Voir `docs/registre_regles.md` : 17 règles conservées à l'identique, 1
modifiée (`R-MNT-007`), 1 étendue (`R-MNT-008`), aucune abandonnée. La
non-régression est démontrée, pas affirmée : `tests/test_non_regression.py`
recharge les fichiers CSV reçus, rejoue les règles et compare
automatiquement, règle par règle, les effectifs obtenus à ceux du rapport de
référence (`analyses/rapport_validation_m2.json`) — tout écart non prévu
fait échouer le test.

### 8. Comment avez-vous relié les mesures aux événements : quelle fenêtre, quelle cardinalité, combien de lignes non appariées ?

Fenêtre : **24 h avant** le début de l'événement, **6 h après**. Justification :
24 h avant correspond à environ 4 mesures au pas nominal de 6 h, suffisant
pour observer une tendance avant l'événement sans remonter à un état trop
ancien pour être pertinent ; 6 h après ne vise qu'à vérifier que les mesures
continuent d'arriver (signe qu'un arrêt n'a pas suivi l'événement), sans
absorber l'effet d'une intervention de maintenance qui suit généralement de
peu.

Cardinalité obtenue (`output/alignment/measures_events.csv`,
`output/validation_report.json`) :

- 514 événements préparés, **89 rapprochés** (17,3 %) à au moins une mesure ;
- **425 événements sans aucune mesure**, tous sur un équipement non
  instrumenté (aucun événement sur équipement instrumenté n'est resté sans
  mesure) ;
- 1 393 lignes de rapprochement pour 1 389 mesures distinctes appariées :
  4 mesures apparaissent dans deux fenêtres d'événements qui se recouvrent —
  duplication volontaire et contrôlée, pas une erreur de jointure ;
- 50 315 − 1 389 = 48 926 mesures hors de toute fenêtre d'événement (elles
  documentent un fonctionnement courant, sans événement à proximité).

### 9. À quel grain avez-vous agrégé les mesures, et que perd-on à ce grain ?

Grain : **équipement × capteur × événement**
(`output/aggregates/measures_by_event_window.csv`, 175 lignes), avec nombre
de mesures, complétude, minimum, maximum, moyenne et écart-type par groupe.
Ce grain perd : l'ordre temporel à l'intérieur de la fenêtre (impossible de
distinguer une tendance croissante d'une tendance décroissante à partir de
la seule moyenne), et toute mesure hors fenêtre d'événement (le
fonctionnement courant, largement majoritaire, n'est pas résumé par cette
table — voir question 8).

### 10. Comment décrivez-vous le flux de traitement et le cycle de vie du jeu de données après l'ajout de cette source, et à qui adressez-vous ces documents ?

Voir `docs/flux_et_cycle_de_vie.md`, section « Destinataires » pour le
détail par public (équipe technique M4, métier maintenance, conformité).

### 11. Quels risques cette source introduit-elle pour les personnes et pour la validité des conclusions, et quelles mesures proportionnées avez-vous prises ?

Voir `docs/couverture_et_risques.md`, sections « Personnes » et « Périmètre
de validité ».

### 12. L'ensemble multi-source peut-il être transmis à M4, sous quelles conditions, et à quel coût de rejeu ?

Oui, sous conditions — voir la décision ci-dessous. Coût de rejeu mesuré :
1,7 s pour l'ensemble des quatre sources sur ce volume, opérations
vectorisées ; praticable à échelle observée, à revalider si la couverture
instrumentale ou le nombre de périodes cumulées augmente d'un ordre de
grandeur (voir « Méthode utilisée »).

## Limites

- L'inventaire exact des anomalies injectées par le formateur n'est pas
  recherché à l'exhaustivité (hors périmètre du brief).
- La détection de nom de personne (`R-MNT-008` étendue) repose sur un motif
  étroit (mot capitalisé + initiale ou nom capitalisé) : elle peut manquer
  une formulation inhabituelle, comme le signale déjà `regles_m2.md` pour
  l'e-mail et le téléphone.
- Le seuil de « séquence figée » (6 mesures identiques consécutives) est un
  choix de diagnostic, pas une règle de rejet automatique : il n'a pas été
  validé contre un historique de pannes réelles (absent de ce corpus
  pédagogique).
- Les bornes physiques (`sensor_value_ranges`) sont volontairement larges :
  elles isolent l'impossible, pas l'inhabituel — une dérive lente dans la
  plage plausible ne serait pas détectée par ce contrôle seul.

## Décision

**Statut : `utilisable sous conditions`.**

107 lignes sur 53 141 reçues (0,2 %) ont été exclues à travers les quatre
sources (doublons, références rompues, valeurs impossibles, hors périmètre
de période) ; le détail complet reste dans `output/quarantine.csv`. Toutes
les tables préparées valident leur schéma déclaré
(`SEN-SCHEMA-VALID` et re-validation Pandera pour les tables héritées de
M2).

Conditions avant transmission à M4 :

- toute analyse fondée sur `sensor_readings.csv` doit rappeler que 8,7 % du
  parc seulement est instrumenté, avec un site (`SITE-OUEST`) et 7 types
  d'équipement totalement absents (voir `docs/couverture_et_risques.md`) ;
- les 425 événements sans mesure ne doivent pas être traités comme des
  événements « sans signal capteur » au sens métier, mais comme des
  événements sur équipement non instrumenté — la distinction doit rester
  visible dans tout usage ultérieur ;
- la séquence figée sur `EQ-PUMP-171` (cas 2, question 6) doit être
  examinée par un expert métier avant d'être utilisée comme exemple de
  fonctionnement normal ou anormal ;
- le statut `modifiee` de `R-MNT-007` doit être revu si le registre de
  référence M2 est corrigé par le formateur (voir `docs/registre_regles.md`).

Coût de rejeu : négligeable au volume actuel (1,7 s), à revalider si la
couverture instrumentale ou le nombre de périodes cumulées croît fortement.
