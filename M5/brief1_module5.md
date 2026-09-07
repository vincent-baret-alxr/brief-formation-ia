# Brief présentiel M5 — Mettre le RAG sous contrôle opérationnel

**Compétences : C6 niveau 3, C8 niveau 1 et C9 niveau 1**

## Situation

M4 a livré des baselines et une décision. L'équipe veut maintenant exploiter le
système dans un environnement reproductible. Le risque principal n'est plus
seulement une mauvaise réponse : c'est un changement de modèle, corpus, index ou
prompt impossible à relier au comportement observé.

## Mission

Construire la chaîne de livraison et d'observation de DiagOps, puis prouver
qu'une version dégradée peut être détectée et restaurée.

## Point de départ commun

- `data_pack/2026-S1/reference_runs/m4_for_m5/` ;
- jeux d'évaluation M4 ;
- période `2026-S2` seulement lorsqu'elle est publiée et qualifiée ;
- contrats de citation, refus et agent à une étape.

La référence distribuée porte l'identifiant `diagops-m4-reference-r1`. Son
intégrité est vérifiée avant le démarrage avec `python tools/check_m5_release.py`.

## Travail attendu

### 1. Identifier les unités versionnées

Attribuez une version et un checksum à : code, configuration, modèle, corpus,
manifest, stratégie de chunking, modèle d'embeddings, index, prompts et jeu
d'évaluation. Un run de production doit permettre de retrouver chaque unité.

### 2. Conteneuriser les composants

Séparez au minimum API, retrieval/index et observabilité, même si plusieurs
composants s'exécutent sur une seule machine. Ajoutez health checks, timeouts,
limites de ressources et configuration hors code.

### 3. Rendre l'ingestion idempotente

- valider manifeste, droits, sensibilité et checksum ;
- détecter ajout, modification, retrait et conflit de révision ;
- produire un nouvel index sans écraser l'index sain ;
- publier l'index seulement après évaluation ;
- conserver une procédure de retour arrière.

### 4. Construire les gates de CI

La chaîne vérifie au minimum :

- tests unitaires et contrats API ;
- intégrité du manifeste ;
- évaluation retrieval réduite ;
- citations résolubles et refus attendus ;
- régressions de latence et mémoire ;
- cas de prompt injection indirecte ;
- absence de secret et d'actif restreint dans les artefacts.

### 5. Observer trois plans

**Service** : disponibilité, erreurs, débit, latence et ressources.

**Retrieval** : documents sans résultat, top-k, versions, index et filtres.

**Réponse** : refus, citations, validation de schéma, revue humaine et coût.

Ne journalisez ni document sensible complet, ni prompt contenant une donnée
personnelle. Définissez rétention et accès aux traces.

### 6. Tester une livraison et un rollback

Déployez un candidat en préproduction, exécutez les gates, injectez une
régression contrôlée puis démontrez : détection, alerte, décision, restauration
et vérification après rollback.

### 7. Documenter l'exploitation

Le runbook décrit démarrage, arrêt, réindexation, incident, rollback, rotation
des secrets, sauvegarde et responsable de chaque décision.

### 8. Exécuter le checkpoint réglementaire M5

À partir du dossier `veille_diagops/` transmis par M4 :

- vérifiez sur des sources officielles datées les exigences susceptibles de
  concerner le déploiement, les fournisseurs, les traces, la rétention, la
  supervision humaine et le traitement des incidents ;
- consignez les changements, incertitudes ou l'absence de changement dans une
  entrée M5 du journal de veille ;
- traduisez la décision dans le runbook, les gates CI, les accès aux traces ou
  les alertes ;
- transmettez à M6 les questions ouvertes avec responsable et échéance.

Ce checkpoint représente environ 1 h incluse dans les 14 h du présentiel et ne
s'ajoute pas au quota du module.

## Livrables

- configuration de conteneurisation ;
- pipeline d'ingestion et publication d'index ;
- CI d'évaluation ;
- configuration de métriques et tableaux de bord ;
- `docs/contrat_versions.md` ;
- `docs/runbook.md` ;
- `docs/rapport_rollback.md` ;
- entrée M5 et passage de relais dans `veille_diagops/` ;
- journal de bord.

## Critères de réussite

- toute réponse est attribuable à des versions identifiées ;
- la réindexation est idempotente et atomique du point de vue du service ;
- une régression bloque la promotion ;
- les métriques distinguent service, retrieval et réponse ;
- le rollback est exécuté, pas seulement décrit ;
- la décision réglementaire M5 est reliée à au moins un contrôle
  d'exploitation, ou son absence d'impact est justifiée ;
- l'autonomie de l'agent n'augmente pas en M5.

## Hors périmètre

- nouvel outil agentique, traité en M6 ;
- réentraînement automatique sans décision humaine ;
- outil à effet ;
- orchestration multi-agent.
