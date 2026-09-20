# État du projet DiagOps — fin du module 6

## Résumé

DiagOps dispose d'un agent mono-agent borné, capable d'utiliser le RAG et des
outils structurés en lecture seule. Une boucle de feedback qualifie les retours,
produit des candidats et les soumet aux gates M5.

## Acquis techniques

- registre d'outils et schémas versionnés ;
- politique d'autorisation et budget d'exécution ;
- jeu de scénarios agentiques gelé ;
- métriques de choix d'outil et qualité finale ;
- traces auditables et minimisées ;
- feedback qualifié ;
- candidat comparé et décision humaine.
- campagne agentique adversariale indépendante ;
- invariants vérifiés avant et après remédiation ;
- politique corrigée sans élargissement de permissions.
- entrée de veille M6 reliée à la politique d'outils, au feedback, aux traces ou
  au gate de promotion ;
- passage de relais réglementaire M7.

## Compétences acquises

- **C5 — niveau 2** : entraîner ou adapter un candidat selon une hypothèse et
  un protocole reproductible ;
- **C8 — niveau 2** : mesurer les performances et impacts du système complet ;
- **C9 — niveau 2** : conduire une amélioration de la collecte du feedback à la
  décision de promotion.

## Limites conservées

- outils strictement en lecture seule ;
- aucun ajout dynamique d'outil ;
- aucune mémoire autonome longue durée ;
- aucun multi-agent requis ;
- aucune promotion ou action métier sans décision humaine.

## Entrées pour M7

- stack M5 et agent M6 de référence ;
- registre des outils et permissions ;
- scénarios, traces et métriques ;
- décisions de feedback ;
- incidents, modes dégradés et risques résiduels ;
- coûts et dépendances observés ;
- dossier `veille_diagops/`, décisions actualisées et validations encore
  ouvertes.
