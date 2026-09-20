# Ressources — Module 6

## Contrats d'outils

- JSON Schema et Pydantic — validation des arguments et résultats ;
- documentation officielle du mécanisme de tool calling retenu ;
- OpenAPI — contrats des outils HTTP ;
- SQLAlchemy — requêtes structurées bornées.

## Évaluation agentique

- jeux de scénarios avec trajectoire attendue ;
- métriques séparant sélection, arguments, exécution et réponse ;
- traces structurées sans chaîne de pensée privée ;
- comparaison à une baseline sans agent.

## Feedback et amélioration

- MLflow — comparaison de runs et registry ;
- outils de data validation ;
- procédures de revue et promotion M5 ;
- méthodes de mesure de dérive par segment.

## Sécurité

- moindre privilège et liste blanche ;
- validation stricte des arguments ;
- budget d'étapes, tokens et durée ;
- timeouts et circuit breakers ;
- OWASP — excessive agency et prompt injection ;
- protection contre l'exfiltration par les paramètres d'outils.

## Veille réglementaire

- reprendre `../M4/brief3_module4_veille_reglementaire.md` et la dernière entrée
  de `veille_diagops/` ;
- vérifier sur des sources officielles les points liés à l'autonomie, aux
  outils, au feedback, à la supervision humaine et à la traçabilité ;
- relier la conclusion à une politique, une trace ou un gate de promotion.

## À éviter

- exposer une connexion SQL arbitraire au modèle ;
- exécuter une chaîne de commandes produite par le modèle ;
- ajouter un outil sans scénario de test ;
- mesurer uniquement la qualité de la réponse finale ;
- transformer tout feedback en exemple d'entraînement.

## Approfondissement de 20 h

- harness de simulation des timeouts et résultats d'outils ;
- catalogue d'invariants agentiques ;
- campagne indépendante versionnée ;
- comparaison avant/après sur scénarios historiques et adversariaux.
