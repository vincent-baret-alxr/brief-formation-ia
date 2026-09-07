# Module 5 — Déployer et observer DiagOps

**Durée S04 : 40 h — 14 h présentiel + 6 h online + 20 h approfondissement**

**Fil rouge moderne : rendre le RAG M4 reproductible, observable et restaurable**

## Positionnement

M5 ne cherche pas de nouvelles capacités agentiques. Il transforme l'état M4
en service opérable : artefacts versionnés, conteneurs, chaîne de validation,
monitoring et rollback. L'évaluation du modèle, du retrieval et des réponses
citées devient un gate de livraison, pas une analyse exécutée une seule fois.

Le brief online couvre le programme CampusAtlas de déploiement, CI/CD, MLOps,
versionnement et monitoring.

## Compétences travaillées

| Compétence | Résultat attendu | Niveau visé | Preuve principale |
|---|---|---:|---|
| **C6** | Intégrer modèle, retrieval et reporting dans l'environnement choisi | **N3** | stack conteneurisée et contrat d'exploitation |
| **C8** | Définir, suivre et interpréter les indicateurs opérationnels | **N1** | métriques, seuils, alertes et rapport d'incident |
| **C9** | Installer une chaîne d'amélioration contrôlée | **N1** | CI d'évaluation, alertes et rollback |

C8 est introduite par la mesure opérationnelle ; M6 l'approfondit au niveau N2
sur le système complet et ses scénarios d'usage.

## Entrées

- `data_pack/2026-S1/reference_runs/m4_for_m5/` ;
- corpus, index et jeux d'évaluation M4 gelés ;
- nouvelles périodes `2026-S2` lorsqu'elles sont déclarées prêtes ;
- décisions et risques M4 ;
- dossier `veille_diagops/` et passage de relais réglementaire M4.

## Brief présentiel — pratique moderne

### Mission

Déployer l'état M4 sans perdre sa reproductibilité, surveiller les trois plans
du système — service, retrieval et qualité de réponse — puis démontrer une
restauration vers la dernière version saine.

### Sorties attendues

- images ou environnements reproductibles ;
- versions liées du modèle, corpus, index, prompts et code ;
- pipeline d'ingestion idempotent et réindexation contrôlée ;
- CI exécutant tests, évaluation réduite et contrôles de sécurité ;
- tableaux de bord de santé, qualité, latence et coût ;
- seuils d'alerte et responsables nommés ;
- déploiement candidat, test de fumée et rollback démontré ;
- runbook d'exploitation.

## Brief online — couverture Atlas

Le brief online traite conteneurisation, versionnement du modèle et des données,
CI/CD, métriques, tableaux de bord et documentation du cycle de vie. Il peut
s'appuyer sur un service simple et reste autonome du RAG présentiel.

## Brief 2 — approfondissement et exercice d'incident

Le brief 2 ajoute une nouvelle version du corpus, un test de charge et un
incident contrôlé. Après 12 h de préparation individuelle, 4 h de game day
contradictoire exposent le service à une régression ou une panne ; les 4 h
finales servent à restaurer, corriger et défendre le rapport post-incident.

## Checkpoint de veille réglementaire M5

Environ 1 h des 14 h du présentiel est consacrée à une entrée datée sur le
déploiement, les fournisseurs, les traces, la rétention, la supervision et les
incidents. La décision est traduite dans un gate, une alerte, un accès aux
traces ou le runbook, puis transmise à M6.

## Matrice de couverture

| Attendu | Programme Atlas | Mise à jour 2026 | Compétence |
|---|---|---|---|
| Packaging | Docker et environnement | composants séparés et health checks | C6 |
| Versionnement | modèle et données | corpus, index, prompts et évaluations liés | C6, C9 |
| CI/CD | tests et livraison | gates retrieval, citations, refus et sécurité | C9 |
| Monitoring | système et performance | métriques retrieval, génération, coût et refus | C6, C8, C9 |
| Amélioration | déclencheurs | alerte, rollback et décision humaine | C8, C9 |
| Veille réglementaire | suivi des exigences | décision datée intégrée à l'exploitation | C6, C9 |

## Évaluation

- brief 1 présentiel : **35 %** ;
- brief 1 online : **30 %** ;
- brief 2 d'approfondissement : **35 %**.

| Dimension | Poids |
|---|---:|
| C6 — intégration et exploitation | 30 % |
| C9 — chaîne contrôlée et rollback | 25 % |
| C8 — observabilité multi-plan | 20 % |
| Reproductibilité et sécurité de livraison | 15 % |
| Documentation | 10 % |

## Gate de sortie

Une version saine peut être reconstruite, déployée, évaluée, observée et
restaurée. Aucun changement de corpus ou d'index ne contourne les gates, et un
incident contrôlé est détecté puis résolu dans les objectifs annoncés. L'entrée
de veille M5 doit être reliée à un contrôle d'exploitation, ou documenter de
façon sourcée pourquoi aucun changement n'est nécessaire.

## Résultat de fin de module

DiagOps possède une stack RAG opérable et une trajectoire de preuves. M6 reçoit
un service stable auquel ajouter des outils en lecture seule et une boucle de
feedback, sans réinventer le déploiement, ainsi que les décisions et points
réglementaires encore ouverts.
