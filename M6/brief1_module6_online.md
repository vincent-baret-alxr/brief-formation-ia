# Brief online M6 — Améliorer un modèle avec de nouvelles données et du feedback

## Mission

Analyser une version en service, qualifier de nouvelles données et des retours
humains, entraîner un candidat, mesurer ses effets puis décider de sa promotion
dans une chaîne d'amélioration continue.

Le brief est autonome et n'exige pas d'agent.

## Organisation

- 3 h en classe virtuelle : dérive, hypothèse d'amélioration et protocole ;
- 3 h en autonomie : candidat, évaluation et décision.

## Travail attendu

### 1. Reprendre la référence

Identifiez version, données, métriques, limites, seuils et environnement de la
version active. Aucun progrès ne peut être affirmé sans référence comparable.

### 2. Qualifier les nouvelles données

Mesurez qualité, distribution, couverture, biais, doublons et lien avec la
cible. Distinguez données réelles, synthétiques et augmentées selon leur
provenance. Qualifiez séparément les feedbacks humains.

### 3. Formuler une hypothèse

Choisissez une modification à la fois : données, feature engineering,
hyperparamètre, modèle ou seuil. Expliquez le mécanisme attendu et les segments
susceptibles de régresser.

### 4. Entraîner le candidat

Versionnez la référence, exécutez l'entraînement de façon reproductible et
conservez configurations, métriques, artefacts et journal.

### 5. Évaluer

Comparez précision, rappel, F1, erreurs, stabilité par segment, ressources et
impacts. Utilisez validation et test sans réutiliser le test pour régler le
candidat.

### 6. Décider et intégrer

Décidez promotion, rejet ou prolongation. Une promotion passe par la chaîne M5,
avec préproduction, gate et rollback disponible.

## Livrables

- rapport de dérive ;
- qualification des nouvelles données et feedbacks ;
- hypothèse et protocole ;
- configuration et résultats du candidat ;
- comparaison segmentée ;
- tableau de bord mis à jour ;
- décision et plan de déploiement ;
- journal de bord.

## Critères de réussite

- la référence est explicite ;
- les feedbacks ne sont pas assimilés automatiquement à des labels ;
- une seule hypothèse principale est testée ;
- les jeux restent séparés ;
- les régressions par segment sont recherchées ;
- la décision est reliée aux exigences initiales ;
- la promotion reste contrôlée.
