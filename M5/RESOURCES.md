# Ressources — Module 5

## Déploiement

- [Dockerfile](https://docs.docker.com/reference/dockerfile/) et
  [Docker Compose](https://docs.docker.com/compose/) — documentation officielle ;
- [FastAPI — déploiement](https://fastapi.tiangolo.com/deployment/) et
  [lifespan](https://fastapi.tiangolo.com/advanced/events/) ;
- serveur d'inférence retenu — documentation de version exacte ;
- documentation de l'index ou de la base vectorielle choisie.

## MLOps et versionnement

- [MLflow](https://mlflow.org/docs/latest/ml/) — tracking, registry et artefacts ;
- [DVC](https://dvc.org/doc) ou mécanisme équivalent — versions des données et corpus ;
- [GitHub Actions](https://docs.github.com/actions) ou CI équivalente — environnements, artefacts et gates ;
- [OpenTelemetry](https://opentelemetry.io/docs/) — traces et métriques, si retenu.

## Observabilité

- [Prometheus](https://prometheus.io/docs/introduction/overview/) — métriques ;
- [Grafana](https://grafana.com/docs/grafana/latest/) — tableaux de bord ;
- documentation du fournisseur de logs et politique de rétention ;
- métriques M4 comme référence fonctionnelle.

## Sécurité d'exploitation

- secrets hors image et hors dépôt ;
- moindre privilège ;
- SBOM et dépendances verrouillées ;
- sauvegarde, restauration et rollback ;
- minimisation des prompts, documents et réponses dans les traces.

## Veille réglementaire

- reprendre `../M4/brief3_module4_veille_reglementaire.md` et le dossier
  `veille_diagops/` ;
- privilégier les textes officiels et les autorités compétentes sur le
  déploiement, les données personnelles, les journaux et les incidents ;
- dater la consultation et relier la conclusion au runbook, aux gates ou aux
  contrôles d'accès.

## À éviter

- tag d'image mutable comme seule version ;
- reconstruction de l'index directement en production ;
- métrique sans seuil ni responsable ;
- promotion automatique après une évaluation partielle ;
- logs contenant le corpus ou des données sensibles en clair.

## Approfondissement de 20 h

- modèles de game day et rapport post-incident ;
- outils locaux de test de charge ;
- chronologie horodatée et objectifs de reprise ;
- scénario formateur injecté sans modification d'un service externe.

## Versions du starter distribué

Les versions Python reproductibles sont verrouillées dans
`starter/requirements.lock`. L'image Prometheus est épinglée dans
`starter/deploy/compose.yaml`. Toute mise à jour de version exige le rejeu des
tests du starter et de `tools/check_m5_release.py`.
