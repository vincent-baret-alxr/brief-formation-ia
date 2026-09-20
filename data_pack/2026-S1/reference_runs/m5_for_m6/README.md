# Référence M5 pour l'ouverture de M6

Ce dossier fournit l'état commun minimal utilisé pour démarrer M6 sans dépendre
de la production personnelle réalisée en M5. Il décrit une stack déployable et
observable, gelée après passage des gates de livraison.

## Contenu

- `release_manifest.json` : versions liées de la release M5 saine et son gate ;
- `index/index_manifest.json` : empreinte de l'index lexical reconstruisible ;
- `evaluation/` : rejeu de calibration reproductible, sans oracle de test ;
- `gates/` : seuils appliqués et rapport de gate de la release ;
- `monitoring/` : contrat de séries observables et valeurs de référence ;
- `baseline/` : retrieval lexical et agent à une décision, point de comparaison
  obligatoire du M6 ;
- `contracts/` : contrat de réponse et actions autorisées avant outillage ;
- `prompts/` : prompt de référence versionné ;
- `runtime/` : Compose, Dockerfile et scrape Prometheus de la stack M5 ;
- `operations/` : runbook d'exploitation et procédure de restauration ;
- `decision_m5.md` et `risks.md` : décision et risques transmis ;
- `veille_diagops/` : passage de relais réglementaire M5 vers M6 ;
- `checksums.sha256` : intégrité de tous les fichiers du dossier.

## Ce que la référence autorise

Elle sert de point de départ commun pour outiller l'agent, mesurer un candidat
et comparer une amélioration. Les deux comparaisons exigées en M6 partent d'ici :

- `baseline/` sans agent, réponse documentaire directe ;
- `baseline/bounded_agent.py`, tranche M4 à une seule étape.

## Limites

La référence est une baseline pédagogique extractive et déterministe. Elle ne
contient ni poids de modèle, ni secret, ni outil, ni réponse au brief M6. Les
labels du split RAG `test` restent scellés côté formateur. Aucun composant ne
possède d'effet externe : la stack lit, expose et mesure, elle ne commande rien.

Les valeurs de latence, de coût et de débit ne sont pas gelées : elles dépendent
du poste et sont mesurées pendant le M6.

## Vérification

Depuis la racine S04 :

```bash
python tools/check_m6_release.py
```

## Reconstruction

```bash
python tools/build_m6_reference.py
```

La reconstruction est déterministe : à corpus et jeu d'évaluation identiques,
les empreintes du dossier sont inchangées.
