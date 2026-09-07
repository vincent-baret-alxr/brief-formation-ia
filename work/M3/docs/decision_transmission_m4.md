# Décision de transmission à M4 — M3

**Décision : utilisable sous conditions.**

Le détail des résultats et le raisonnement complet sont dans
[`diagnostic_multisource.md`](diagnostic_multisource.md), section
« Décision ». Ce document résume la décision pour une lecture rapide.

## Preuves principales

- Non-régression démontrée sur les trois tables héritées de M2
  (`tests/test_non_regression.py`), un seul écart assumé et justifié
  (`R-MNT-007`, voir `registre_regles.md`).
- 107 lignes exclues sur 53 141 reçues (0,2 %) à travers les quatre sources,
  toutes tracées dans `output/quarantine.csv`.
- Tables préparées valides au regard de leur schéma déclaré
  (`output/validation_report.json`).
- Rapprochement mesures ↔ événements contrôlé en cardinalité : 89/514
  événements rapprochés, 425 sans mesure disponible faute d'instrumentation
  (pas d'erreur de jointure silencieuse).

## Conditions

1. Rappeler la couverture instrumentale partielle (8,7 % du parc, un site et
   7 types d'équipement totalement absents) dans toute analyse qui utilise
   `sensor_readings.csv`.
2. Ne pas confondre un événement « sans mesure » (équipement non
   instrumenté) avec un événement « sans anomalie capteur ».
3. Faire trancher par un expert métier la séquence de valeurs figées
   détectée sur `EQ-PUMP-171` avant de l'utiliser comme exemple de
   comportement normal ou anormal.
4. Revoir `R-MNT-007` (modifiée par M3) si le registre de référence M2 est
   corrigé par le formateur.

## Coût de rejeu

1,7 s pour l'ensemble des quatre sources au volume actuel (mesuré avec
`time`). À revalider si la couverture instrumentale ou le nombre de
périodes cumulées augmente d'un ordre de grandeur.

## Risques

Voir [`couverture_et_risques.md`](couverture_et_risques.md) : risque de
réidentification indirecte par croisement site + horodatage + bon de
travail (mesure retenue : ne pas croiser avec des données RH/badgeage),
biais de conclusion dû à la couverture partielle du parc.
