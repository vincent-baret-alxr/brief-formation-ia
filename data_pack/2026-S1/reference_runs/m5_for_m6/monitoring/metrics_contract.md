# Contrat de séries observables — référence M5

| Plan | Série | Source | Fréquence | Signification |
|---|---|---|---|---|
| Service | `diagops_ready` | `/metrics` | 15 s | release valide et lisible |
| Service | `diagops_dependency_up` | `/metrics` | 15 s | dépendance de génération disponible |
| Index | `diagops_index_valid` | `/metrics` | 15 s | index conforme au corpus déclaré |
| Retrieval | `diagops_expected_document_hit_at_3` | rejeu de calibration | par release | document attendu dans les trois premiers |
| Réponse | `diagops_citation_resolvable_rate` | rejeu de calibration | par release | citations résolubles dans l'index |
| Réponse | `diagops_correct_abstention_rate` | rejeu de calibration | par release | refus corrects sur questions non couvertes |

## Séries à ajouter en M6

Le module ajoute au minimum la justesse du choix d'outil, la justesse des
arguments, le taux d'appels inutiles, les dépassements de budget, la latence et
le coût par scénario. Ces séries n'existent pas dans la référence : elles sont
une production du M6.

## Interdits de label

Ni contenu documentaire, ni argument d'outil brut, ni identifiant de personne
ne figure dans un label de métrique.
