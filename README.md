# DiagOps — cursus Atlas/CISIA — session S04

Ce dépôt est la **source pédagogique commune** de la session S04. Le formateur
publie progressivement les briefs, starters, données et références de
continuité sur `main`. Les apprenants le configurent comme remote `upstream`
et conservent leurs productions dans un dépôt privé indépendant (`origin`).

## État du cursus

| Module | État | Supports |
|---|---|---|
| M0 | passé | briefs, synthèse, acquis et modèles |
| M1 | passé | briefs, synthèse, acquis et starter |
| M2 | passé | présentiel 14 h, online 6 h, starter et référence de continuité |
| M3 | ouvert | présentiel 14 h, online 6 h, starter, données capteurs et référence de continuité |
| M4 | prêt à distribuer — 40 h | conception et évaluation : modèle simple, RAG minimal, agent borné et réplication |
| M5 | prêt à distribuer — 40 h | déploiement, CI d'évaluation, monitoring et exercice d'incident |
| M6 | prêt à distribuer — 40 h | amélioration continue, outils en lecture seule, feedback et campagne adversariale |
| M7 | prévu — 40 h | revue d'architecture, sécurité, souveraineté, réversibilité et migration exercée |
| M8 | prévu — 40 h | nouveau projet RAG-agentique, audit indépendant, correction et soutenance |

Les données distribuées sont centralisées dans [`data_pack/`](data_pack/).
Un module peut les utiliser, mais ne doit pas en conserver de copie.

La modernisation RAG et agentique progresse de M4 a M8. Les briefs online
restent consacres au programme CampusAtlas certifiant ; les briefs presentiels
portent la mise a jour 2026. A partir de M4, un brief d'approfondissement de
20 h ajoute une realisation individuelle, une contradiction independante puis
une remediation et une defense. Les contrats d'actifs futurs marques `planned`
dans le manifeste ne signifient pas que ces actifs sont deja distribues.

La veille technologique et reglementaire ouverte en M0 est consolidee en M4,
puis prolongee jusqu'en M8 par un checkpoint inclus dans chaque brief
presentiel. Elle ne majore pas les quotas de 40 h : ses decisions sont integrees
aux risques, gates, politiques, ADR et dossiers deja produits dans le module.

## Démarrer M6

Le M6 part de la référence `diagops-m5-reference-r1` et ouvre la période
`2027-S1`. Avant l'ouverture, le formateur conserve la clé de qualification du
feedback hors du dépôt apprenant et vérifie les checksums du data pack.

```bash
python tools/init_module.py M6
cd work/M6
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
python eval/run_agent_eval.py
python feedback/qualify_feedback.py --batch b1
```

Le lot de feedback `b2` et les cas adverses supplémentaires n'entrent qu'au
brief 2. Le starter fournit la machinerie bornée, pas la solution : l'agent
distribué reste à une seule étape et échoue volontairement sur trois scénarios
du jeu gelé.

Contrôle avant publication :

```bash
python tools/check_m6_release.py
python tools/check_m6_release.py --trainer
```

## Organisation du dépôt

```text
S04/
├── M0/ ... M8/          # supports publiés progressivement
├── data_pack/           # source unique des données apprenant
├── tools/               # initialisation et contrôle de publication
├── work/                # productions propres à l'apprenant
├── GIT_WORKFLOW.md      # configuration origin/upstream
└── _conception/         # local et ignoré, jamais publié
```

Le dépôt pédagogique ne publie aucun travail dans `work/MN/`. Chaque apprenant
peut donc y versionner sa production sans conflit avec les mises à jour de
`upstream/main`.

## Démarrer M3

Après avoir configuré les remotes comme indiqué dans
[`GIT_WORKFLOW.md`](GIT_WORKFLOW.md) :

```bash
python tools/init_module.py M3
cd work/M3
python -m venv .venv
```

Le script refuse d'écraser un dossier existant. Les notebooks et utilitaires
retrouvent automatiquement les données sous `data_pack/2026-S1/`.

## Démarrer M4

Le M4 utilise la révision `diagops-2026-S1-m4-v1`. Avant l’ouverture, le
formateur conserve les oracles et le lot de contradiction hors du dépôt
apprenant, puis vérifie les checksums du data pack.

```bash
python tools/init_module.py M4
cd work/M4
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
```

Le test capteur et les labels RAG de test ne sont restitués qu’après gel du
candidat. Le lot du brief 2 est remis séparément après la première décision M4.

## Démarrer M5

M5 utilise la révision `diagops-2026-S1-m5-v1` du data pack et la référence
saine `diagops-m4-reference-r1`. Les scénarios du game day restent dans
l'espace formateur et sont injectés seulement après le gel du candidat.

```bash
python tools/check_m5_release.py
python tools/init_module.py M5
cd work/M5
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
```

La période `2026-S2` est une extension facultative tant qu'elle n'est pas
explicitement déclarée `ready_for_distribution` dans le manifeste.

## Règles de publication

- dans le dépôt pédagogique, `upstream/main` contient uniquement le matériel
  distribué aux apprenants ; dans chaque dépôt privé, `origin/main` contient
  aussi les productions placées sous `work/` ;
- `_conception/`, les environnements, checkpoints et runs locaux sont exclus ;
- les données d'un module futur ne sont ajoutées qu'au moment de son ouverture ;
- avant toute publication, exécuter :

```bash
python tools/check_publication.py
python tools/check_m4_release.py --trainer
python tools/check_m5_release.py --trainer
```

Ce contrôle inspecte les fichiers suivis ou candidats au commit et bloque les
contenus privés, les copies de données par module et les fichiers trop lourds.
Le second contrôle vérifie les lots, labels scellés, checksums, baseline M3 et
actifs formateur nécessaires à l’ouverture du M4.
