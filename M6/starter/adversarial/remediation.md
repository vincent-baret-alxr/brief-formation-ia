# Remédiation et défense — M6

## Classement des échecs

| Échec | Cause retenue | Catégorie | Correction proposée | Coût |
|---|---|---|---|---|
| | | politique / contrat / outil / modèle / test | | |

La catégorie détermine où corriger. Une correction dans le modèle ne répare pas
un défaut de politique.

## Règle de correction

Une correction ne peut pas élargir une permission. Si la seule correction
envisageable consiste à autoriser un outil, un argument ou un budget plus large,
la décision remonte à l'humain et le candidat n'est pas promu.

## Avant et après

| Mesure | Référence | Candidat avant correction | Candidat après correction |
|---|---|---|---|
| réussite des scénarios historiques | | | |
| réussite de la campagne | | | |
| exactitude du choix d'outil | | | |
| exactitude des arguments | | | |
| appels inutiles | | | |
| refus corrects | | | |
| dépassements de budget | | | |
| latence moyenne par scénario | | | |

Les scénarios historiques sont rejoués intégralement : une correction qui
répare un cas adverse en cassant un cas nominal est un échec.

## Décision

- décision : `promouvoir` / `rejeter` / `prolonger` ;
- responsable de la décision : _à nommer_ ;
- gate M5 rejoué : oui / non, résultat ;
- version restaurable disponible : oui / non ;
- meilleur argument opposé, et pourquoi il ne renverse pas la décision.
