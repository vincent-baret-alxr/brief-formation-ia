# Journal de bord — M2

## Reprise M0–M1

- Référence commune M1 consultée : `data_pack/2026-S1/reference_runs/m1_for_m2/`
  (métriques, prédictions et matrice d'erreurs de continuité, 80 exemples de
  validation déjà consultés).
- Comparaison éventuelle avec ma production M1 : la matrice d'erreurs
  commune a été jointe à `equipment.csv` préparé pour répondre à la question
  9 du diagnostic (voir `docs/diagnostic_donnees.md`) ; ma propre production
  M1 (runs LoRA à 3 et 5 époques) n'a pas été recomparée ici, M2 ne
  statuant pas sur la promotion du modèle.
- Décisions structurantes : traitement par pipeline Python (pandas +
  Pandera) plutôt que par notebook, pour disposer de contrôles rejouables et
  testés (`pytest`) — voir `docs/README.md`.
- Preuves conservées : `output/processed/*.csv`, `output/quarantine.csv`,
  `output/corrections.csv`, `output/validation_report.json`,
  `tests/test_rules.py` (22 tests).
- Limites encore ouvertes : détection PII par expression régulière
  uniquement, effectifs faibles sur certaines catégories (`SITE-OUEST`,
  `lift`, `steam_unit`), croisement M1 sur un historique déjà consulté.

## Hypothèses formulées avant analyse

| Date | Hypothèse | Mesure prévue | Résultat | Décision |
|---|---|---|---|---|
| 2026-09-01 | Les fichiers reçus contiennent des doublons, ruptures de référence et valeurs impossibles injectés à des fins pédagogiques (`data_pack/DATA_CARD.md`) | Contrôles Pandera + règles référentielles sur les 3 tables | 24 lignes anormales détectées sur 2 740 (0,9 %), 5 valeurs corrigeables | Isoler en quarantaine, corriger seulement les cas non ambigus |
| 2026-09-01 | Le taux d'erreur `severity` de M1 peut varier selon la catégorie d'équipement, mais sur de petits effectifs | Comptage croisé matrice M1 × `equipment.csv` | Écarts observés (ex. `fan` 57 %, n=7) mais effectifs trop faibles pour conclure | Signaler sans affirmer de causalité |

## Activités et preuves produites

| Date | Activité | Artefact ou commit | Revue reçue |
|---|---|---|---|
| 2026-09-01 | Inspection directe des 3 fichiers reçus (nulls, doublons, domaines, dates, valeurs impossibles, PII) | exploration ponctuelle, résultats repris dans `docs/diagnostic_donnees.md` | — |
| 2026-09-01 | Écriture des schémas Pandera (`contracts/schemas.py`) | commit à faire | — |
| 2026-09-01 | Écriture des règles de doublons, référence, correction et PII (`src/data_pipeline/rules.py`) et du pipeline (`src/data_pipeline/cli.py`) | commit à faire | — |
| 2026-09-01 | Tests unitaires valides/invalides (`tests/test_rules.py`, 22 tests) | commit à faire | — |
| 2026-09-01 | Exécution du pipeline sur les données reçues, rédaction du diagnostic | `output/`, `docs/diagnostic_donnees.md` | — |

## Décisions

### Décision

- Options considérées : (1) corriger silencieusement toutes les anomalies
  pour maximiser le volume utilisable ; (2) tout exclure au moindre doute ;
  (3) ne corriger que les cas sans ambiguïté et isoler le reste en
  quarantaine documentée.
- Preuve déterminante : les anomalies non ambiguës (variantes de casse,
  PII détectable) représentent 5 valeurs sur 2 740 lignes, contre 24 lignes
  dont la correction supposerait de deviner une valeur (signe, catégorie).
- Choix retenu : option (3) — corriger uniquement ce qui est certain, isoler
  le reste avec règle, valeur observée et raison tracées.
- Limites et réversibilité : entièrement réversible (les fichiers reçus ne
  sont jamais modifiés, `output/` est régénéré par une seule commande) ;
  limité par la couverture des règles écrites, pas garantie exhaustive.

## Bilan M2

- Ce que je sais démontrer : les trois tables et leurs relations sont
  comprises, les anomalies principales sont quantifiées et tracées, les
  contrôles sont rejouables et testés, la décision (« utilisable sous
  conditions ») s'appuie sur des résultats précis et cite ses limites.
- Ce qui reste incertain : l'inventaire exact des anomalies injectées par le
  formateur (non recherché à l'exhaustivité, conformément au brief), la
  cause des écarts de taux d'erreur M1 par catégorie (effectifs trop
  faibles).
- Ce que M3 doit reprendre : les 24 lignes de `output/quarantine.csv`
  restent à trancher par un expert métier avant intégration ; les
  catégories sous-représentées (`SITE-OUEST`, `lift`, `steam_unit`, etc.)
  doivent être signalées dans toute analyse capteurs qui les utiliserait
  isolément.
