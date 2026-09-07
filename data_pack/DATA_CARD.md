# DiagOps Data Pack — data card

Statut : support apprenant.

## Description

Le DiagOps Data Pack est un corpus synthetique fourni pour un parcours de
formation a la conception et l'implementation de solutions d'intelligence
artificielle appliquees a la maintenance industrielle.

Il contient des rapports techniciens, des donnees d'equipements, des mesures
capteurs, des historiques d'interventions, des evenements de maintenance, des
retours utilisateurs et un corpus image externe pour le travail multimodal.

## Origine

Les donnees textuelles, tabulaires et temporelles sont synthetiques.
Elles ont ete creees pour exercer des competences de cadrage, preparation,
entrainement, evaluation, integration, deploiement et amelioration continue.

Le corpus image M7 provient d'une source externe qui doit etre documentee dans
le manifeste avant distribution.

## Usages autorises

- Travaux de formation.
- Prototypage pedagogique.
- Evaluation de livrables dans le cadre du parcours.
- Demonstration de pipelines d'IA sur donnees controlees.

## Usages exclus

- Analyse metier reelle de maintenance industrielle.
- Entrainement d'un systeme de production.
- Comparaison scientifique entre modeles.
- Decision operationnelle ou de securite.

## Limites

Ce corpus ne constitue pas une source de connaissance metier. Les distributions,
formulations, incidents et relations entre sources sont construits pour le
parcours de formation.

Les resultats obtenus sur ce corpus ne doivent pas etre generalises a un site
industriel reel sans donnees reelles, expertise metier et validation dediee.

## Donnees annotees M1

Le pack inclut un sous-ensemble annote pour M1 :

- environ 400 exemples d'entrainement ;
- environ 100 exemples de test ;
- tache : transformer un rapport technicien en JSON DiagOps conforme.

Ces annotations servent d'intrants pedagogiques pour entrainer et evaluer le
modele M1.

## Tables ouvertes en M2

La revision `diagops-2026-S1-m2-v1` ajoute :

- 420 lignes d'inventaire d'equipements ;
- 520 lignes d'evenements ;
- 1 800 lignes d'historique de maintenance.

Ces tables couvrent les identifiants d'equipement et d'evenement references
par le corpus M1 et ajoutent des equipements sans annotation afin de travailler
la couverture.

Elles contiennent des anomalies pedagogiques controlees : doublons, valeurs
manquantes, categories heterogenes, incoherences temporelles, ruptures de
jointure, valeurs extremes et informations personnelles synthetiques dans
quelques notes libres. L'inventaire exact des anomalies n'est pas distribue aux
apprenants.

Les donnees capteurs ne sont pas ouvertes en M2. Elles restent reservees au
travail temporel et multi-source de M3.

## Table ouverte en M3

La révision `diagops-2026-S1-m3-v1` ajoute `2026-S1/sensors/sensor_readings.csv` :
50 401 mesures issues de 36 équipements instrumentés, au pas nominal de six
heures, du 2 janvier au 30 juin 2026.

Cette table est la première source temporelle du corpus. Elle n'a pas
d'identifiant de ligne : la clé logique est le triplet
`equipment_id + timestamp + sensor_name`.

Elle contient des anomalies pédagogiques contrôlées : doublons stricts,
doublons de clé à valeur divergente, horodatages hétérogènes, série décalée
dans le temps, changements d'unité, capteur figé, dérive lente, trou
d'échantillonnage, valeurs sentinelles, mesures hors période et mesures
rattachées à un équipement inconnu. Certaines variations sont réelles et ne
doivent pas être supprimées. L'inventaire exact des anomalies n'est pas
distribué aux apprenants.

Le parc instrumenté est volontairement partiel : 36 équipements sur 416, avec
une couverture inégale selon le site, le type d'équipement et la criticité.
Toute statistique calculée sur les capteurs porte donc sur une partie du parc.
La composition exacte du parc instrumenté n'est pas décrite ici : elle se
mesure à partir des données.

## Lot de contrôle M3

La révision `diagops-2026-S1-m3-v2` ajoute `2026-S1/sensors_control/`, ouvert au
brief 2 de M3. Le lot mélange des mesures authentiques, reprises de
`sensor_readings.csv`, et des mesures fabriquées. Il sert à éprouver des
contrôles, jamais à alimenter une analyse.

`control_batch.csv` ne porte pas de colonne de provenance : c'est le lot à
qualifier. `control_sample.csv` est un échantillon **disjoint**, produit par la
même procédure et dans les mêmes proportions, dont la provenance de chaque ligne
est déclarée ; il sert à régler des contrôles, pas à conclure.

La proportion de lignes fabriquées et les procédés employés ne sont pas
distribués. Les fabrications ne sont pas toutes de même difficulté : certaines
violent les contrôles de qualité de M2 et M3, d'autres respectent les
distributions marginales, d'autres encore préservent la structure temporelle et
ne se trahissent que par leur incohérence avec `events.csv`.

Les lignes authentiques du lot portent les anomalies de qualité de la livraison
M3. **Une ligne signalée par un contrôle de qualité n'est donc pas
nécessairement une ligne fabriquée**, et le lot contient délibérément des cas où
cette confusion est coûteuse.

L'outil `tools/verify_synthetic.py` applique les contrôles de référence de M2 et
M3 à un fichier de mesures et retourne des comptages par famille de règle, sans
jamais désigner les lignes concernées. Son périmètre exclut la structure
temporelle des séries et leur cohérence avec les autres sources : il le rappelle
à chaque exécution.

## Actifs ouverts en M4

La révision `diagops-2026-S1-m4-v1` ajoute trois ensembles.

`2026-S1/model_eval/` fournit 30 fenêtres de calibration étiquetées et 60
fenêtres de test sans étiquette. Chaque fenêtre contient 30 mesures et porte un
`window_id` indivisible. Les lots sont disjoints des lots de contrôle M3. La
cible pédagogique est la provenance `réelle` ou `fabriquée`, jamais une panne
future. Les oracles de test restent côté formateur.

`2026-S1/knowledge/` contient huit documents synthétiques de maintenance et de
gouvernance accompagnés d’un manifeste versionné. Droits, sensibilité, statut de
révision, rôles autorisés et checksums conditionnent l’admission dans un index.
Une révision remplacée et un document restreint sont conservés pour éprouver les
contrôles ; leur présence ne les rend pas admissibles pour tous les rôles.

`2026-S1/rag_eval/questions.jsonl` contient douze questions de calibration dont
les labels sont visibles et douze questions de test dont les labels sont
scellés. Les questions couvrent citations, abstention, révisions, unités,
permissions et limites de l’agent. Le lot de contradiction du brief 2 n’est
révélé qu’après gel du premier candidat.

Le dossier `2026-S1/reference_runs/m3_for_m4/` fige enfin une baseline à règles
et ses métriques sur la calibration. Cette baseline est volontairement limitée :
elle signale des violations de contrat et ne constitue pas une vérité de
provenance.

## Référence de continuité M4 vers M5

La révision `diagops-2026-S1-m5-v1` ajoute le dossier
`2026-S1/reference_runs/m4_for_m5/`, qui fournit la release pédagogique
saine `diagops-m4-reference-r1` : baseline lexicale, agent à une décision,
contrats de réponse, index reconstruisible, métriques de calibration, décision,
risques et passage de relais réglementaire. Ses checksums permettent de relier
les versions du corpus, de l'index, du prompt et de l'évaluation.

Cette référence n'emploie jamais le split RAG `test` et ne contient aucun poids
de modèle. Elle autorise une préproduction pédagogique et les exercices de
rollback, pas un déploiement industriel. La période `2026-S2` reste une
extension M5 facultative tant que son statut demeure `planned` dans le
manifeste.

## Contrat de provenance

À partir de M3, une table de mesures transmise d'un module à l'autre déclare
l'origine de chaque ligne — `réelle`, `synthétique` ou `augmentée` — et le
procédé qui l'a produite. Le contrat est décrit dans `SCHEMA.md`. Il ne porte
pas sur la qualité d'une ligne : une mesure réelle peut être aberrante, une
mesure fabriquée peut être irréprochable.

## Référence de continuité M2 vers M3

Le dossier `2026-S1/reference_runs/m2_for_m3/` fournit un état préparé commun
des trois tables ouvertes en M2 : tables préparées, quarantaine, registre des
règles appliquées, rapport de validation et décision de référence. Il permet de
démarrer M3 sans dépendre de l'achèvement des productions personnelles de M2.

Ce dossier n'est pas une correction du brief M2. Le registre est partiel,
plusieurs décisions restent discutables et aucune règle temporelle n'y figure.

## Livraison candidate facultative M2

La révision `diagops-2026-S1-m2-v2` ajoute le dossier
`2026-S1/m2_candidate_release/` pour le complément « Pour aller plus loin ».
Il contient un lot incrémental d'équipements, d'événements et d'interventions à
qualifier avant toute intégration.

Ce lot est volontairement distinct des tables publiées : il peut contenir des
erreurs, des évolutions de schéma, des catégories nouvelles et des changements
de qualité globale. Sa présence dans le data pack ne signifie pas qu'il est
accepté. Les notes de livraison décrivent uniquement les évolutions annoncées ;
l'inventaire formateur des écarts n'est pas distribué.

Ce complément ne contient aucune donnée capteur et n'anticipe pas le périmètre
temporel de M3.

## Référence de continuité M1 vers M2

Le dossier `2026-S1/reference_runs/m1_for_m2/` fournit un run M1 commun :
prédictions, métriques, matrice d'erreurs, limites et décision de référence.
Il permet de démarrer M2 sans dépendre de l'achèvement des productions
personnelles de M1. Il ne contient ni poids, ni checkpoint, ni correction de
M2.

## Precautions d'interpretation

Les effectifs et correlations sont construits a des fins pedagogiques. Ils ne
representent pas un parc industriel reel. Une relation observee ne doit pas
etre interpretee comme une causalite ni generalisee hors de ce corpus.
