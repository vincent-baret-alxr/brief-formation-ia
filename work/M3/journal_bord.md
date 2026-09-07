# Journal de bord — M3

## Reprise M2

- Point de départ utilisé : **référence commune**
  (`data_pack/2026-S1/reference_runs/m2_for_m3/`), pas la production
  personnelle M2 — voir `docs/diagnostic_multisource.md`, section « Point de
  départ retenu », pour la justification.
- Règles héritées relues : les 19 règles de `regles_m2.md`
  (`R-EQ-001`…`R-EQ-006`, `R-EVT-001`…`R-EVT-005`, `R-MNT-001`…`R-MNT-008`).
- Décisions M2 remises en cause : `R-MNT-007` (traitement incohérent avec
  `R-EVT-003` dans la référence, corrigé pour M3) ; `R-MNT-008` étendue à la
  détection de nom de personne.
- Preuves conservées : `output/processed/*.csv`, `output/quarantine.csv`,
  `output/registre_regles.csv`/`.md`, `output/validation_report.json`,
  `tests/test_non_regression.py` (comparaison automatique aux effectifs de
  référence).
- Limites encore ouvertes : voir `docs/diagnostic_multisource.md`, section
  « Limites ».

## Hypothèses formulées avant analyse

| Date | Hypothèse | Mesure prévue | Résultat | Décision |
|---|---|---|---|---|
| 2026-09-01 | La clé logique `equipment_id + timestamp + sensor_name` proposée par le starter n'est pas garantie unique dans le fichier reçu | Détection des doublons de clé (`SEN-KEY-001`) | 10 clés dupliquées trouvées (6 strictes, 4 divergentes) | Doublon strict : copie retirée. Doublon divergent : les deux lignes exclues, aucun arbitrage arbitraire |
| 2026-09-01 | Les règles R-* du registre de référence sont rejouables à l'identique sur les fichiers reçus | Comparaison automatisée effectif par effectif | 17/19 règles reproduites exactement, 1 divergence identifiée et expliquée (`R-MNT-007`) | Divergence assumée et documentée plutôt que masquée |
| 2026-09-01 | La couverture instrumentale suit la criticité déclarée des équipements | Taux d'instrumentation par criticité | Confirmé en tendance (30 % en critical vs 1 % en low) mais 70 % des équipements critical restent non instrumentés | Signalé comme limite de validité, pas présenté comme une couverture suffisante |

## Activités et preuves produites

| Date | Activité | Artefact ou commit | Revue reçue |
|---|---|---|---|
| 2026-09-01 | Inspection directe des 4 fichiers reçus (nulls, doublons, unités, plages, dates, PII) | résultats repris dans `docs/diagnostic_multisource.md` et `docs/registre_regles.md` | — |
| 2026-09-01 | Reconstruction des règles héritées M2 (`src/data_pipeline/m2_rules.py`) et comparaison à la référence | `tests/test_non_regression.py` | — |
| 2026-09-01 | Écriture des règles temporelles nouvelles (`src/data_pipeline/sensor_rules.py`), du rapprochement et du schéma capteurs (`contracts/schemas.py`) | `tests/test_sensor_rules.py` | — |
| 2026-09-01 | Exécution du pipeline complet, rédaction du diagnostic multi-source | `output/`, `docs/` | — |

## Décisions

### Décision

- Options considérées : (1) reproduire `R-MNT-007` à l'identique de la
  référence, même si son traitement diffère sans justification de celui de
  `R-EVT-003` ; (2) harmoniser `R-MNT-007` sur le comportement de
  `R-EVT-003`, en le documentant comme une modification assumée.
- Preuve déterminante : les deux règles décrivent la même condition
  (« normalisé et dans le domaine ») avec la même décision annoncée dans
  `regles_m2.md`, mais produisent un résultat différent sur un cas
  analogue (normalisation réussie vers une valeur valide, suivie d'une
  exclusion pour l'une, pas pour l'autre).
- Choix retenu : option (2), avec la divergence mesurée et vérifiée par un
  test dédié plutôt qu'assertée.
- Limites et réversibilité : entièrement réversible (les fichiers reçus ne
  sont jamais modifiés, `output/` est régénéré par une seule commande) ;
  si le registre de référence est corrigé par le formateur, `R-MNT-007`
  devra être réexaminée.

## Brief online

Non traité dans cette session : le squelette de persistance (`src/db/`,
notebook `m3_base_de_donnees_atlas.ipynb`) n'a pas été complété. À reprendre
séparément si nécessaire.

## Bilan M3

- Ce que je sais démontrer : la source capteurs est cadrée avant d'être
  traitée (grain, clé, période, pas, volumétrie) ; les défauts temporels
  sont quantifiés, pas seulement cités ; la non-régression sur les tables
  M2 est vérifiée automatiquement ; le rapprochement mesures ↔ événements
  est explicite en fenêtre et en cardinalité ; la couverture instrumentale
  est chiffrée et bornée en validité.
- Ce qui reste incertain : la nature exacte (capteur figé ou mesure réelle
  stable) de la séquence figée sur `EQ-PUMP-171` ; l'origine réelle du
  doublon divergent sur `EQ-CHILL-115` ; l'existence et la fréquence de
  livraison réelles de `sensor_readings.csv` en dehors de ce corpus
  pédagogique synthétique.
- Ce que M4 doit reprendre : le brief M3 online (persistance, base de
  données) ; l'examen expert des 107 lignes en quarantaine et des cas
  signalés (`conserve_signale`) avant tout usage quantitatif ; la
  réévaluation de la couverture instrumentale si de nouveaux capteurs sont
  déployés.
