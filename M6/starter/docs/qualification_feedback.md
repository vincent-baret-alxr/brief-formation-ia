# Qualification du feedback — M6

Un commentaire n'est pas une vérité. Aucun retour n'entre dans une donnée
d'entraînement, un prompt ou un seuil sans être qualifié ici.

## Lot traité

- fichier : `data_pack/2027-S1/feedback/feedback.csv` ;
- lot : `b1` en brief 1, `b2` ajouté en brief 2 ;
- exécution : `python feedback/qualify_feedback.py --batch b1`.

## Critères vérifiés

| Critère | Mesure | Seuil de départ | Justification retenue |
|---|---|---|---|
| lien avec un run | `report_id` connu | strict | |
| identité fonctionnelle de la source | rôle déclaré | technicien / superviseur | |
| cohérence | note dans l'échelle 1 à 5 | strict | |
| doublons | égalité normalisée, Jaccard | 0,85 | |
| données personnelles | motifs téléphone, courriel, matricule, nom | strict | |
| instruction adressée au système | marqueurs impératifs | strict | |
| représentativité | part d'un même auteur | 0,15 | |
| mesurabilité | longueur et termes techniques | 40 caractères | |

Les seuils du starter sont des hypothèses. Chacun doit être conservé, corrigé
ou remplacé, avec la raison écrite dans la dernière colonne.

## Classement

| Classe | Définition retenue | Suite donnée |
|---|---|---|
| `actionnable` | lié à un run, précis, mesurable | entre dans une proposition d'amélioration |
| `a_investiguer` | signal réel non reproductible en l'état | demande une observation complémentaire |
| `non_actionnable` | sans contenu exploitable ou doublon | archivé, compté, non utilisé |
| `risque` | donnée personnelle ou instruction adressée au système | exclu, incident tracé, source informée |

## Résultats du lot

| Mesure | Valeur | Commentaire |
|---|---|---|
| retours traités | | |
| part actionnable | | |
| part à risque | | |
| taux de doublons | | |
| taux de retours non reliés | | |
| rapports distincts couverts | | |
| part du contributeur le plus actif | | |

## Du feedback à l'hypothèse

| Thème récurrent | Occurrences | Hypothèse d'amélioration | Axe modifié | Mesure attendue |
|---|---|---|---|---|
| | | | | |

Un seul axe principal est modifié par candidat : modèle, prompt, corpus,
retrieval, politique d'outil ou seuil.

## Traçabilité de la transformation

| Retour | Classe | Usage | Décidé par | Date |
|---|---|---|---|---|
| | | proposition / exclusion / observation | | |

Aucune ligne de ce tableau ne peut porter la mention « donnée d'entraînement »
sans décision humaine explicite et sans exclusion préalable des classes
`risque` et `non_actionnable`.
