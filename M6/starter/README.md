# Starter — Module 6

Ce starter fournit la machinerie d'exécution bornée : contrats d'outils en
lecture seule, registre gelable, politique d'exécution, agent à une étape,
harness d'évaluation agentique, qualification du feedback et tests
d'invariants. Il ne constitue pas la solution du brief : l'agent fourni est la
tranche M4 à une seule étape, transposée aux cinq outils.

Tous les adaptateurs M6 sont en lecture seule. Un test explicite échoue si un
outil tente de modifier un système ou d'exécuter une commande arbitraire.

## Installation

Depuis la racine du dépôt pédagogique :

```bash
python tools/init_module.py M6
cd work/M6
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
```

Sous PowerShell, l'activation est `.venv\Scripts\Activate.ps1`.

## Données

Les chemins sont relatifs à `work/M6/` :

```text
../../data_pack/2026-S1/reference_runs/m5_for_m6/   # référence de continuité
../../data_pack/2026-S1/knowledge/                  # corpus documentaire actif
../../data_pack/2026-S1/equipment/equipment.csv
../../data_pack/2026-S1/events/events.csv
../../data_pack/2026-S1/maintenance/maintenance_history.csv
../../data_pack/2027-S1/reports/reports.jsonl       # période dérivée
../../data_pack/2027-S1/feedback/feedback.csv       # lots b1 et b2
```

La variable `DIAGOPS_DATA_PACK` permet de désigner un autre data pack. Ne
copiez jamais le data pack dans le module.

## Structure

```text
work/M6/
├── agent/            # politique, registre gelable, agent borné
├── tools/            # cinq adaptateurs de lecture et accès au data pack
├── eval/             # jeu de scénarios gelé et harness de mesure
├── feedback/         # qualification des retours avant tout usage
├── tests/            # contrats, bornes de politique, absence d'effet
├── docs/             # registre des outils et qualification du feedback
├── adversarial/      # campagne, invariants, rapport et remédiation
├── results/          # sorties locales, jamais versionnées dans upstream
└── journal_bord.md
```

## Premières vérifications

```bash
python -m pytest -q
python eval/run_agent_eval.py
python feedback/qualify_feedback.py --batch b1
python eval/run_agent_eval.py --scenarios adversarial/campaign.jsonl \
  --output results/campagne_baseline.json --traces results/campagne_traces.jsonl
```

## Point de départ mesuré

Sur le jeu gelé de 18 scénarios, l'agent fourni obtient :

| Mesure | Valeur de départ |
|---|---|
| réussite des scénarios | 0,833 |
| choix d'outil exact | 0,889 |
| exactitude des arguments | 0,933 |
| taux d'appels inutiles | 0,062 |
| appels d'outils interdits | 1 |
| refus corrects | 7 |
| baseline sans agent | 0,111 |

Les trois scénarios en échec désignent le travail à faire : `SCN-006`
enchaînement borné de plusieurs étapes, `SCN-013` refus avant appel lorsque la
question porte une instruction, `SCN-014` filtrage du rôle avant la lecture.
Sur la campagne fournie, `ADV-001` et `ADV-006` échouent pour les mêmes raisons.

Ces valeurs sont la référence à battre. Les reproduire n'est pas un livrable.

## Ce que vous produisez

- le registre d'outils complété et justifié, y compris modes dégradés ;
- la politique d'exécution défendue valeur par valeur ;
- l'extension du jeu de scénarios, puis son gel avant mesure ;
- un agent borné dépassant la tranche à une étape, sans dépasser le budget ;
- les métriques séparant choix d'outil, arguments, exécution et qualité finale ;
- la qualification du feedback et ses seuils justifiés ;
- un candidat modifiant un seul axe, comparé à la référence M5 ;
- la campagne adversariale, la remédiation et la décision de promotion ;
- l'entrée de veille réglementaire M6 et son passage de relais à M7.

## Règles

- aucun outil n'écrit, ne commande, ne déclenche ni ne sort du data pack ;
- le registre est gelé : aucun outil ne s'ajoute en cours d'exécution ;
- un résultat d'outil est une donnée, jamais une instruction ;
- les traces ne contiennent ni argument en clair, ni document, ni donnée
  personnelle, ni raisonnement privé ;
- le jeu de scénarios se gèle avant toute comparaison ;
- aucune promotion sans gate rejoué et sans décision humaine ;
- une correction qui élargit une permission n'est pas une correction.
