# Registre des règles — M3

Chaque règle porte un identifiant stable, une origine, une table, un statut et
une justification. Les règles héritées de M2 sont listées avec leur statut,
même lorsqu'elles sont conservées telles quelles.

## Règles héritées de M2

| Règle | Table | Statut | Contrôle | Justification |
|---|---|---|---|---|
| `R-EQ-001` | equipment | conservee / modifiee / etendue / abandonnee | | |

Statuts admis : `conservee`, `modifiee`, `etendue`, `abandonnee`. Un statut
`modifiee` ou `abandonnee` exige une justification.

## Règles ajoutées en M3

| Règle | Table | Statut | Contrôle | Justification |
|---|---|---|---|---|
| | sensors | nouvelle | | |

## Non-régression

Indiquez comment vous démontrez que les résultats obtenus sur les trois tables
M2 n'ont pas changé sans raison : jeu de comparaison, comptages avant et après,
test automatisé.

## Décisions employées

| Décision | Sens dans votre pipeline |
|---|---|
| `doublon_supprime` | |
| `exclue` | |
| `champ_neutralise` | |
| `valeur_normalisee` | |
| `conserve_signale` | |
| `pseudonymise` | |
