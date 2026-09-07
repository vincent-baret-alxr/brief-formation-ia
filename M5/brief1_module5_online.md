# Brief online M5 — Déployer, monitorer et intégrer l'évaluation

**Compétences : C6 niveau 3, C8 niveau 1 et C9 niveau 1**

## Mission

Déployer une solution IA existante dans une chaîne de livraison continue,
identifier les métriques utiles et intégrer son évaluation au processus MLOps.

Le brief est autonome et peut utiliser un modèle simple fourni par le formateur.

## Organisation

- 3 h en classe virtuelle : architecture de livraison, métriques et revue des
  déclencheurs ;
- 3 h en autonomie : implémentation, test et documentation.

## Travail attendu

### 1. Comprendre l'artefact

Documentez entrées, sorties, paramètres, dépendances, version et résultats de
référence du modèle fourni.

### 2. Conteneuriser

Produisez une image reproductible, une configuration externe, un health check
et une commande de test de fumée.

### 3. Versionner

Reliez versions du code, du modèle, des données et des résultats. Expliquez ce
qui déclenche une nouvelle version et ce qui peut rester inchangé.

### 4. Automatiser la validation

La CI exécute tests, évaluation minimale, construction de l'artefact et
publication vers un environnement de préproduction. La production reste soumise
à une décision explicite.

### 5. Monitorer

Définissez métriques de santé système, stabilité des données, performance du
modèle et usage. Pour chaque métrique, fixez source, fréquence, seuil,
destinataire et action attendue.

### 6. Tester et documenter

Exécutez une livraison candidate, conservez les preuves et documentez une
procédure de restauration.

## Livrables

- conteneur et configuration ;
- workflow CI/CD ;
- registre de versions ;
- tableau des métriques et déclencheurs ;
- tableau de bord ou export équivalent ;
- rapport de livraison ;
- procédure de rollback ;
- journal de bord.

## Critères de réussite

- l'artefact est reconstruisible ;
- l'évaluation est un gate de la livraison ;
- les métriques sont reliées à une décision ;
- modèle et données sont versionnés ;
- préproduction et production sont distinguées ;
- la restauration est vérifiable.
