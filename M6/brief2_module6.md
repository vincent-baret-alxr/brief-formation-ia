# Brief 2 M6 — Résister à une campagne agentique adversariale

**Durée : 20 h — 12 h de réalisation, 4 h de campagne indépendante, 4 h de remédiation et défense**

## Situation

Le brief 1 a produit un agent outillé en lecture seule et une boucle de feedback.
Les scénarios nominaux ne suffisent pas à établir que permissions, budgets et
contrats tiennent lorsque les entrées ou les outils se comportent mal.

## Mission

Étendre le jeu agentique, qualifier un nouveau lot de feedback, soumettre
l'agent à une campagne indépendante puis corriger la politique et décider du
candidat d'amélioration.

## Entrées

- agent, registre d'outils et politique du brief 1 ;
- jeu de scénarios gelé ;
- nouveau lot de feedback qualifié par le formateur ;
- harness permettant de simuler erreurs, délais et résultats d'outils ;
- version M5 restaurable.

## Phase 1 — Réalisation individuelle, 12 h

### 1. Étendre les scénarios

Ajoutez des cas multi-étapes mais bornés : outil inutile, arguments invalides,
résultat vide, identifiant ambigu, timeout, données contradictoires, preuve
insuffisante et refus attendu.

### 2. Instrumenter la politique

Rendez observables budget restant, choix d'outil, validation des arguments,
résultat, arrêt, fallback et raison finale. Les traces ne contiennent ni chaîne
de pensée privée ni donnée sensible complète.

### 3. Qualifier le feedback

Mesurez doublons, couverture, cohérence, provenance et risques. Transformez
seulement les retours actionnables en proposition versionnée.

### 4. Construire un candidat

Modifiez un seul axe principal : modèle, prompt, retrieval, politique, outil ou
seuil. Rejouez anciens et nouveaux scénarios avant toute recommandation.

### 5. Préparer les invariants adversariaux

Ils incluent : aucun effet externe, aucun outil hors liste, arguments conformes,
budget enforceable, arrêt sur erreur critique, filtres d'accès avant données et
promotion humaine uniquement.

## Phase 2 — Campagne indépendante, 4 h

Un pair construit ou sélectionne des attaques sans modifier le runtime :

- injection demandant un outil interdit ;
- résultat d'outil contenant une instruction ;
- argument visant une autre ressource ;
- répétition coûteuse ;
- conflit entre outil structuré et document ;
- timeout en cascade ;
- feedback malveillant ou non représentatif.

Chaque cas produit verdict, trace, impact et invariant concerné.

## Phase 3 — Remédiation et défense, 4 h

- classer les échecs par politique, contrat, outil, modèle ou test ;
- corriger sans élargir les permissions ;
- rejouer campagne et non-régression ;
- comparer version de référence et candidat ;
- décider promotion, rejet ou prolongation ;
- défendre le meilleur argument opposé.

## Livrables

- scénarios étendus ;
- instrumentation et tableau des métriques ;
- qualification du feedback ;
- candidat versionné ;
- campagne indépendante et traces ;
- rapport d'invariants ;
- correction et résultats avant/après ;
- décision de promotion ;
- support de défense.

## Critères de réussite

- les attaques restent dans le laboratoire ;
- aucun outil ne possède d'effet ;
- l'agent ne peut élargir sa liste blanche ;
- les résultats d'outils sont traités comme données ;
- budgets et timeouts sont vérifiables ;
- le candidat est comparé aux scénarios historiques ;
- un échec non corrigé bloque la promotion.

## Gate renforcé M6

L'agent respecte ses invariants sous campagne indépendante et toute amélioration
reste réversible, mesurée et soumise à une décision humaine.
