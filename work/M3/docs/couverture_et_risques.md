# Couverture et risques — M3

## Couverture instrumentale

Calculée sur `output/processed/equipment.csv` (416 lignes) croisé avec les
`equipment_id` présents dans `output/processed/sensors.csv` (36 équipements
instrumentés, sur 37 `equipment_id` reçus — le 37e, `EQ-ORPHAN-777`, est
exclu par `SEN-REF-001`).

| Dimension | Parc complet | Parc instrumenté | Écart |
|---|---:|---:|---|
| Équipements | 416 | 36 | 8,7 % du parc |
| Sites (couverts / total) | 4 | 3 | `SITE-OUEST` (16 équipements) n'a **aucun** équipement instrumenté |
| Types d'équipement (couverts / total) | 18 | 11 | 7 types sans aucune couverture : `dryer`, `gearbox`, `lift`, `motor`, `packaging_machine`, `press` (34 unités !), `valve` |
| Criticités (taux d'instrumentation) | — | — | `critical` 14/46 (30 %), `high` 14/122 (11 %), `medium` 7/173 (4 %), `low` 1/75 (1 %) |
| Événements rapprochables | 514 | 89 (17,3 %) | 425 événements n'ont aucune mesure disponible, faute d'équipement instrumenté ou de mesure dans la fenêtre |

Point positif : le taux d'instrumentation croît avec la criticité déclarée
(30 % en `critical` contre 1 % en `low`), ce qui suggère un choix
d'instrumentation au moins partiellement guidé par le risque métier. Point
d'alerte : 32 des 46 équipements `critical` (70 %) restent malgré tout sans
aucune mesure, et un site entier (`SITE-OUEST`) est aveugle.

## Périmètre de validité

Tout constat tiré de `sensor_readings.csv` (agrégats, seuils physiques,
comportements de capteur) ne s'applique qu'aux 36 équipements instrumentés,
sur les sites `SITE-NORD`, `SITE-SUD` et `SITE-EST`, et seulement pour les
cinq grandeurs mesurées (courant, vibration, température, pression,
vitesse de rotation). Il ne doit pas être étendu à `SITE-OUEST`, aux 7 types
d'équipement non couverts, ni généralisé à « l'équipement critique » comme
catégorie (70 % des équipements `critical` ne sont pas concernés).

## Personnes

Recherché : noms de personnes, adresses e-mail et numéros de téléphone dans
`work_order_note` (règle `R-MNT-008`, étendue en M3, voir
`docs/registre_regles.md`). Détecté : 3 occurrences sur 1 800 notes (2
retrouvées en M2, 1 nom de personne supplémentaire détecté par l'extension
M3). Décidé : pseudonymisation par marqueur typé, note conservée sinon
inchangée.

Risque propre à `sensor_readings.csv` : une mesure horodatée toutes les 6 h
ne contient aucune information nominative directe, mais son croisement avec
un site, un horodatage et un bon de travail de maintenance (qui, lui,
contient un `work_order_note` parfois nominatif) peut permettre de
reconstituer une présence humaine à un moment et un lieu donnés. Ce n'est pas
une donnée identifiante en soi, mais **la conjonction** peut le devenir.
Position retenue : ne pas croiser `sensor_readings.csv` avec des données RH
ou de badgeage en dehors de ce périmètre pédagogique, et traiter tout futur
croisement site + horodatage + identité comme un traitement à documenter
séparément, pas comme une extension anodine de la pipeline actuelle. Cette
position est proportionnée au constat : elle n'interdit pas l'usage
technique (maintenance prédictive) mais borne l'usage RH.

## Conservation du volume

- **Brut** (`output/processed/sensors.csv`, 50 315 lignes) : conservé tel
  quel après préparation (valeurs impossibles exclues, unités et noms
  normalisés) — nécessaire pour toute nouvelle analyse temporelle non prévue
  aujourd'hui (dérive lente, détection de saut) qu'un agrégat détruirait.
- **Agrégats** (`output/aggregates/measures_by_event_window.csv`, 175 lignes,
  grain équipement × capteur × événement) : conservés comme produit
  d'usage pour M4, où le volume brut par événement est inutilement lourd.
- **Écarté** : les 107 lignes en quarantaine (doublons, valeurs
  impossibles, références rompues, hors périmètre de période) ne sont pas
  conservées dans les tables préparées ; elles restent traçables dans
  `output/quarantine.csv`, pas perdues.

Le brut représente ~1,4 Mo pour un semestre sur 36 équipements ; le coût de
conservation du brut est donc négligeable ici. Il cesserait de l'être sur
l'ensemble du parc (416 équipements, soit un facteur ~12) ou sur plusieurs
périodes cumulées — voir `docs/diagnostic_multisource.md`, question 12, pour
le coût de rejeu.

## Suivi proposé

- Réévaluer la couverture instrumentale (site, type, criticité) à chaque
  nouvelle période : un déploiement de capteurs sur `SITE-OUEST` ou sur les
  types actuellement non couverts changerait le périmètre de validité
  ci-dessus et devrait être mesuré avant toute nouvelle conclusion.
- Recompter les occurrences d'information personnelle détectées à chaque
  nouvelle période de `maintenance_history.csv` : le motif de détection de
  nom (`NAME_RE`) est étroit et peut manquer une formulation inhabituelle
  (limite déjà documentée dans `regles_m2.md`).
- Revérifier la stabilité des plages physiques (`sensor_value_ranges`) si un
  nouveau type d'équipement est instrumenté : les bornes actuelles sont
  calées sur le parc généraliste observé, pas sur un équipement spécialisé.
