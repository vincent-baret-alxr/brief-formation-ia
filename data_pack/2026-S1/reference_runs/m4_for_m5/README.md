# Référence M4 pour l'ouverture de M5

Ce dossier fournit l'état commun minimal utilisé pour démarrer M5 sans dépendre
de la production personnelle réalisée en M4.

## Contenu

- `release_manifest.json` : versions liées de la référence saine ;
- `index/index_manifest.json` : empreinte de l'index lexical reconstruisible ;
- `evaluation/` : résultats de calibration reproductibles, sans oracle de test ;
- `baseline/` : retrieval lexical et agent à une décision ;
- `contracts/` : contrat de réponse et actions autorisées ;
- `prompts/` : prompt de référence versionné ;
- `decision_m4.md` et `risks.md` : décision et risques transmis ;
- `veille_diagops/` : passage de relais réglementaire ;
- `checksums.sha256` : intégrité de tous les fichiers du dossier.

## Limites

La référence est une baseline pédagogique extractive et déterministe. Elle ne
contient ni poids de modèle, ni secret, ni réponse au brief M5. Les labels du
split RAG `test` restent scellés côté formateur. M5 doit conserver cette version
saine, reconstruire son index et démontrer ses propres gates et procédures de
rollback.

## Vérification

Depuis la racine S04 :

```bash
python tools/check_m5_release.py
```
