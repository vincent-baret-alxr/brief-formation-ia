# Brief 2 M5 — Conduire un game day de la stack RAG

**Durée : 20 h — 12 h de préparation, 4 h d'incident contradictoire, 4 h de remédiation et défense**

**Compétences consolidées : C6 niveau 3, C8 niveau 1 et C9 niveau 1**

## Situation

Le brief 1 a produit une stack déployable, observable et restaurable sur un
parcours nominal. Il faut maintenant vérifier son comportement lorsqu'une
nouvelle version et une panne réelle du laboratoire se combinent.

## Mission

Préparer une livraison candidate, mesurer sa capacité, subir un incident
contrôlé puis restaurer le service et corriger le dispositif opérationnel.

## Entrées

- état M5 du brief 1 ou référence formateur ;
- version saine identifiée ;
- nouvelle révision de corpus ou configuration candidate ;
- scénarios d'incident formateur ;
- objectifs de service et de reprise.

Les objectifs formateur communs fixent notamment une détection en moins de
2 minutes, une décision en moins de 5 minutes, une restauration en moins de
10 minutes et aucune perte de données. L'équipe peut annoncer des objectifs
plus exigeants avant l'injection.

## Phase 1 — Préparation individuelle, 12 h

### 1. Construire la livraison candidate

Versionnez code, modèle, corpus, index, prompts et évaluation. Produisez l'index
hors du chemin actif, exécutez les gates puis préparez une promotion réversible.

### 2. Tester la capacité

Définissez un profil réaliste et mesurez débit, latence p50/p95, erreurs,
mémoire, stockage et coût. Identifiez le premier point de saturation sans tester
un service externe ou de production.

### 3. Vérifier l'observabilité

Chaque panne envisagée doit produire un signal attribuable. Vérifiez alertes,
seuils, liens vers les versions, rétention et absence de données sensibles dans
les traces.

### 4. Préparer le game day

Écrivez rôles, canal de décision, conditions d'arrêt, procédure de sauvegarde,
rollback, reconstruction et vérification après reprise.

## Phase 2 — Incident contradictoire, 4 h

Le formateur ou un pair injecte un scénario parmi :

- index partiellement corrompu ;
- corpus candidat dégradant les citations ;
- serveur de génération indisponible ;
- latence du retrieval multipliée ;
- configuration incompatible ;
- alerte manquante ou trop bruyante.

L'équipe observe, qualifie, décide, restaure et chronomètre. Elle n'efface ni
traces ni état initial avant la fin de l'exercice.

## Phase 3 — Remédiation et défense, 4 h

- construire la chronologie ;
- distinguer cause, facteurs aggravants et symptômes ;
- corriger test, alerte, runbook ou architecture ;
- rejouer le scénario ou un test équivalent ;
- vérifier la version saine après restauration ;
- défendre les arbitrages de coût, disponibilité et qualité.

## Livrables

- manifeste de livraison candidate ;
- rapport de capacité ;
- plan et rôles du game day ;
- chronologie et preuves de l'incident ;
- preuve de rollback ou reconstruction ;
- rapport post-incident ;
- correctif et test de non-régression ;
- runbook révisé ;
- support de défense.

## Critères de réussite

- le candidat ne remplace pas la version saine avant les gates ;
- la capacité est mesurée sur un profil annoncé ;
- l'incident est détecté par le système, pas seulement signalé par l'animateur ;
- le rollback est exécuté ;
- le rapport évite la recherche de faute individuelle ;
- une remédiation est vérifiée ;
- les objectifs non atteints restent visibles.

## Gate renforcé M5

La stack détecte un incident contrôlé, restaure une version saine et démontre
la correction dans les objectifs de reprise annoncés ou documente leur échec.
