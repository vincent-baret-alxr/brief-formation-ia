# État du projet DiagOps — fin du module 5

## Résumé

DiagOps dispose d'une stack RAG déployable, d'une chaîne d'évaluation et d'une
observabilité couvrant le service, le retrieval et la réponse.

## Acquis techniques

- versions liées du code, modèle, corpus, index, prompts et évaluations ;
- ingestion documentaire idempotente ;
- conteneurs et health checks ;
- CI avec gates de qualité et sécurité ;
- tableaux de bord et alertes ;
- procédure de promotion et rollback démontrée ;
- runbook d'exploitation.
- rapport de capacité sur un profil annoncé ;
- game day, chronologie et rapport post-incident ;
- remédiation rejouée après restauration.
- entrée de veille M5 traduite dans le runbook, les gates, les traces ou les
  alertes ;
- passage de relais réglementaire M6 avec responsable et échéance des points
  ouverts.

## Compétences acquises

- **C6 — niveau 3** : intégrer les briques de la solution dans un environnement
  exploitable et documenté ;
- **C8 — niveau 1** : définir, suivre et interpréter des indicateurs avec seuil,
  responsable et action attendue ;
- **C9 — niveau 1** : installer une chaîne d'amélioration avec mesures,
  déclencheurs et retour arrière.

## Limites conservées

- l'agent reste limité à l'action unique définie en M4 ;
- aucune trace ne constitue automatiquement une donnée de réentraînement ;
- un déploiement sain ne prouve pas la pertinence métier ;
- les outils métier et feedback humain sont introduits en M6.

## Entrées pour M6

- stack de référence déployable ;
- versions saines et procédure de rollback ;
- métriques et traces minimisées ;
- jeux d'évaluation ;
- registre des incidents et décisions ;
- contrats de sécurité M4-M5 ;
- dossier `veille_diagops/` et dernière entrée réglementaire datée.
