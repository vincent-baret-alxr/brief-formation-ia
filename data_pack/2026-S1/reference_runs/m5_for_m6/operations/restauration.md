# Procédure de restauration de la référence

## Condition de déclenchement

- un gate régresse après promotion ;
- l'index actif ne correspond plus au corpus déclaré ;
- une réponse cite une source inadmissible ou une révision remplacée ;
- un comportement d'agent dépasse son budget ou sa liste d'outils.

## Étapes

1. arrêter la promotion en cours et consigner l'horodatage ;
2. restaurer la release `diagops-m5-reference-r1` ;
3. rejouer la calibration et comparer aux valeurs de
   `evaluation/metrics_calibration.json` ;
4. vérifier les séries de `monitoring/baseline_metrics.json` ;
5. consigner la durée de restauration et la cause dans le journal de bord.

## Objectif

La restauration est mesurée. En M6, un échec d'invariant sous campagne
adversariale déclenche cette procédure avant toute correction.
