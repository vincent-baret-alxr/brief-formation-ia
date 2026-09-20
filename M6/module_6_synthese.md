# Module 6 — Améliorer DiagOps avec feedback et outils

**Durée S04 : 40 h — 14 h présentiel + 6 h online + 20 h approfondissement**

**Fil rouge moderne : passer du RAG déployé à un agent outillé en lecture seule**

## Positionnement

M6 ajoute deux boucles contrôlées à la stack M5 :

- une boucle de feedback humain qui propose des améliorations sans les déployer
  automatiquement ;
- une boucle agentique bornée qui choisit entre retrieval documentaire et outils
  structurés en lecture seule.

Le RAG devient un outil parmi d'autres. Les capteurs, équipements, événements et
historiques sont interrogés par contrats typés, jamais transformés en documents
pour contourner leur structure.

Le brief online couvre C5, C8 et C9 : analyser les mesures, intégrer de nouvelles
données et du feedback, entraîner un candidat, le comparer puis décider.

## Compétences travaillées

| Compétence | Résultat attendu | Niveau visé | Preuve principale |
|---|---|---:|---|
| **C5** | Entraîner ou adapter un candidat à partir de données et feedback qualifiés | **N2** | protocole, candidat et comparaison |
| **C8** | Mesurer performance, impacts et usage du système complet | **N2** | tableau de bord et analyse par scénario |
| **C9** | Conduire une boucle d'amélioration avec promotion contrôlée | **N2** | feedback qualifié, gate et décision |

## Entrées

- `data_pack/2026-S1/reference_runs/m5_for_m6/` ;
- `2027-S1/reports/reports.jsonl` et `feedback/feedback.csv` lorsqu'ils sont
  déclarés prêts ;
- stack M5, jeux d'évaluation, traces minimisées et runbook ;
- contrats de données structurées M2-M3 ;
- dossier `veille_diagops/` et passage de relais réglementaire M5.

## Brief présentiel — pratique moderne

### Mission

Construire un agent qui répond à un scénario DiagOps en choisissant des outils
de lecture autorisés, puis utiliser le feedback humain pour proposer une
amélioration mesurée sans créer de déploiement autonome.

### Outils autorisés

- `search_knowledge` ;
- `get_equipment` ;
- `list_events` ;
- `get_maintenance_history` ;
- `diagnose_report`.

Chaque outil possède un schéma, une autorisation, un timeout, une limite de
résultats et une trace. Aucun outil ne modifie une donnée ou ne déclenche une
intervention.

### Sorties attendues

- registre et contrats d'outils ;
- politique d'autorisation et budget d'exécution ;
- agent mono-agent borné en étapes ;
- jeu de scénarios avec outils et preuves attendus ;
- mesures du choix d'outil, des arguments, citations et réponses ;
- qualification des feedbacks et proposition d'amélioration ;
- candidat comparé à la version de référence ;
- décision humaine de promotion, rejet ou prolongation.

## Brief online — couverture Atlas

Le brief online exploite de nouvelles données et du feedback pour entraîner ou
adapter un modèle, reprendre les métriques, analyser la dérive et intégrer la
validation à la chaîne MLOps. Les données synthétiques et augmentées déjà
traitées en M3 sont auditées par provenance ; elles ne sont pas recréées pour
remplir artificiellement le module.

## Brief 2 — approfondissement et campagne adversariale

Le brief 2 étend les scénarios d'outils et le lot de feedback. Après 12 h de
réalisation individuelle, 4 h de campagne adversariale vérifient permissions,
arguments, budgets et modes d'échec ; les 4 h finales corrigent la politique et
défendent la promotion ou le rejet du candidat.

## Checkpoint de veille réglementaire M6

Environ 1 h des 14 h du présentiel vérifie si les outils, l'autonomie bornée,
les feedbacks et les décisions de promotion modifient les rôles, la supervision
ou la traçabilité attendue. L'entrée M6 doit modifier une politique, une trace
ou un gate, ou justifier de façon sourcée l'absence d'impact, puis être transmise
à M7.

## Matrice de couverture

| Attendu | Programme Atlas | Mise à jour 2026 | Compétence |
|---|---|---|---|
| Nouvelles données | qualité, biais, feature engineering | feedback qualifié et provenance | C5, C9 |
| Optimisation | candidat et comparaison | modification minimale liée à une hypothèse | C5 |
| Mesure | précision, F1, erreurs, impacts | choix d'outil, groundedness, refus et coût | C8 |
| Boucle de feedback | intégration continue | proposition, review, gate et rollback | C9 |
| Contrôle humain | limites d'utilisation | aucune promotion ni action automatique | C8, C9 |
| Veille réglementaire | réévaluation continue | impact daté sur outils, feedback et supervision | C8, C9 |

## Évaluation

- brief 1 présentiel : **35 %** ;
- brief 1 online : **30 %** ;
- brief 2 d'approfondissement : **35 %**.

| Dimension | Poids |
|---|---:|
| C5 — candidat et protocole | 20 % |
| C8 — mesure multi-composant | 25 % |
| C9 — feedback et promotion contrôlée | 20 % |
| Agent borné et contrats d'outils | 25 % |
| Documentation | 10 % |

## Gate de sortie

L'agent respecte son budget, choisit les outils attendus sur le jeu gelé, ne
possède aucun effet externe et produit des traces auditables. La campagne
adversariale ne révèle aucun dépassement non traité, et une amélioration issue
du feedback n'est promue qu'après comparaison et décision humaine. Le
checkpoint réglementaire M6 et son passage de relais à M7 sont présents.

## Résultat de fin de module

DiagOps dispose d'un agent mono-agent, outillé et en lecture seule, ainsi que
d'une boucle d'amélioration contrôlée. M7 reçoit cette preuve pour challenger
l'architecture, les permissions, la souveraineté et les risques d'agence, avec
les décisions réglementaires actualisées.
