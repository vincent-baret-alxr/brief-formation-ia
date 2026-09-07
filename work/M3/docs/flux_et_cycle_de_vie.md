# Flux de traitement et cycle de vie du jeu de données — M3

## Destinataires

- **Équipe technique DiagOps (M4)** : doit pouvoir rejouer la pipeline,
  comprendre quelles lignes ont été écartées et pourquoi, et savoir quelles
  sorties (`processed/`, `aggregates/`, `alignment/`) sont sûres à
  consommer sans revalidation.
- **Métier / maintenance** : doit pouvoir lire `output/quarantine.csv` et
  `docs/couverture_et_risques.md` pour statuer sur les lignes en
  `conserve_signale` (durées d'arrêt extrêmes, champs manquants) qui
  demandent un avis humain, et sur la faible couverture instrumentale de
  certains sites/types.
- **Conformité / protection des données** : doit pouvoir vérifier la section
  « Personnes » de `docs/couverture_et_risques.md` et le détail de
  `R-MNT-008` sans avoir à relire le code.

## Flux de traitement

```text
data_pack/2026-S1/{equipment,events,maintenance,sensors}.csv   (jamais modifiés)
        |
        v
[1] prepare_equipment            (m2_rules.py)   -> processed/equipment.csv
        |
        v
[2] prepare_events                (m2_rules.py)   -> processed/events.csv
        |  (utilise processed/equipment.csv pour R-EVT-005)
        v
[3] prepare_maintenance           (m2_rules.py)   -> processed/maintenance.csv
        |  (utilise processed/equipment.csv et processed/events.csv,
        |   cascade : une ligne exclue en [1] ou [2] peut exclure une
        |   intervention en [3] via R-MNT-002 / R-MNT-003)
        v
[4] prepare_sensors               (sensor_rules.py) -> processed/sensors.csv
        |  (utilise processed/equipment.csv pour SEN-REF-001)
        v
[5] align_measures_to_events      (contracts/schemas.py) -> alignment/measures_events.csv
        |  (utilise processed/sensors.csv et processed/events.csv)
        v
[6] agrégation par fenêtre        (cli.py)         -> aggregates/measures_by_event_window.csv
        |
        v
[7] quarantaine unifiée + registre -> quarantine.csv, registre_regles.csv/.md
        |
        v
[8] rapport de validation          -> validation_report.json
```

| Étape | Entrée | Sortie | Ligne écartée possible ? | Règle concernée |
|---|---|---|---|---|
| [1] Équipements | `equipment.csv` | `processed/equipment.csv` | Oui (doublon strict, criticité hors domaine) | `R-EQ-001`…`R-EQ-006` |
| [2] Événements | `events.csv` + [1] | `processed/events.csv` | Oui (doublon, sévérité invalide, équipement inconnu) | `R-EVT-001`…`R-EVT-005` |
| [3] Interventions | `maintenance_history.csv` + [1] + [2] | `processed/maintenance.csv` | Oui, y compris par cascade depuis [1]/[2] | `R-MNT-001`…`R-MNT-008` |
| [4] Mesures | `sensor_readings.csv` + [1] | `processed/sensors.csv` | Oui (sentinelle, hors plage, hors période, équipement inconnu, doublon de clé) | `SEN-*` |
| [5] Rapprochement | [2] + [4] | `alignment/measures_events.csv` | Non (filtre, ne détruit rien ; peut dupliquer une mesure sur deux fenêtres qui se recouvrent) | — |
| [6] Agrégats | [5] | `aggregates/measures_by_event_window.csv` | Non (résume) | — |

Une ligne écartée à n'importe quelle étape reste retrouvable dans
`output/quarantine.csv` (`source_file`, `row_identifier`, `rule_id`) : suivre
une ligne d'un bout à l'autre consiste à chercher son identifiant dans ce
fichier plutôt que dans les journaux d'exécution.

Commande qui rejoue l'ensemble (~1,7 s sur ce volume, mesuré avec `time`) :

```bash
python -m src.data_pipeline --input ../../data_pack/2026-S1 --output ./output
```

## Cycle de vie du jeu de données

| Question | Réponse |
|---|---|
| Origine : qui produit ces données ? | Équipements et système de supervision du parc industriel DiagOps (`equipment.csv`, `events.csv`, `maintenance_history.csv` : équipe maintenance ; `sensor_readings.csv` : export de supervision, cf. `data_pack/SCHEMA.md`). Le corpus utilisé ici est synthétique (`data_pack/DATA_CARD.md`) ; en production, le producteur réel de `sensor_readings.csv` reste à confirmer auprès de l'exploitation — non déterminable depuis le seul fichier reçu. |
| Fréquence de livraison | Par période semestrielle nommée (`2026-S1`), comme les trois tables M2 ; le pas d'échantillonnage nominal annoncé est de 6 h (`SCHEMA.md`), confirmé par la mesure (médiane observée 6 h, voir `output/series_overview.csv`). |
| Format et mode d'accès | CSV, une ligne par mesure, sans identifiant de ligne ; accès en lecture depuis `data_pack/2026-S1/sensors/sensor_readings.csv`, jamais modifié par la pipeline. |
| Durée et forme de conservation | Voir `docs/couverture_et_risques.md`, section « Conservation du volume » : brut + agrégats conservés pour la période courante, pas de purge automatique définie à ce stade — à fixer avec l'exploitation avant un usage en production. |
| Qui accède aux données préparées ? | L'équipe qui exécute la pipeline (accès aux fichiers du dépôt de travail) ; pas de contrôle d'accès distinct implémenté ici — hors périmètre technique de ce brief (pas de plateforme de données à construire). |
| Que se passe-t-il à l'arrivée d'une nouvelle période ? | Les nouvelles lignes portent un `period` différent ; `SEN-PERIOD-001` isole déjà les lignes hors du périmètre annoncé (30 lignes `2026-S2` trouvées dans la livraison `2026-S1` elle-même) — un signe que le mélange de périodes doit être anticipé, pas traité comme une exception rare. |
| À partir de quand ces données cessent d'être utilisables ? | Quand la couverture instrumentale ou la définition d'un capteur change sans mise à jour du registre de règles (nouvelle unité, nouveau `sensor_name`, nouveau seuil physique) : les règles `SEN-*` doivent alors être revues avant réutilisation, pas appliquées telles quelles. |

La règle de conservation retenue — brut, agrégats, ou les deux — et sa
raison : conserver **les deux** pour la période courante (voir
`docs/couverture_et_risques.md`) ; le brut reste nécessaire à toute analyse
temporelle future non prévue par les agrégats actuels (grain
équipement × capteur × événement), les agrégats sont le produit d'usage
attendu par M4.

## Description du jeu de données, mise à jour

L'ajout de `sensor_readings.csv` fait passer le jeu DiagOps d'un ensemble de
lignes indépendantes (équipements, événements, interventions) à un ensemble
comportant une **série temporelle partielle** : 36 équipements sur 416
(8,7 %), 3 sites sur 4, 11 types d'équipement sur 18. Il permet désormais de
décrire l'état mesuré d'un équipement autour d'un événement (89 événements
sur 514 rapprochables), mais ne permet toujours pas de conclure sur les
équipements non instrumentés, ni de démontrer qu'une mesure cause un
événement (hors périmètre du brief). La description du jeu doit donc
préciser, pour toute utilisation en M4, que les mesures capteurs ne
représentent qu'une fraction du parc et une fraction des événements.

## Points à revoir

- M4 doit connaître la fenêtre de rapprochement retenue (24 h avant, 6 h
  après) et la remettre en cause si l'usage prévu (ex. détection précoce)
  demande une fenêtre différente.
- Si la couverture instrumentale change (nouveaux capteurs), refaire tourner
  `docs/couverture_et_risques.md` avant de réutiliser les constats de
  couverture actuels.
- Le statut `modifiee` de `R-MNT-007` (voir `docs/registre_regles.md`) doit
  être revu si le registre de référence M2 est lui-même corrigé par le
  formateur.
