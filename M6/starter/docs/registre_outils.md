# Registre des outils — M6

Un outil absent de ce registre n'existe pas pour l'agent. Une ligne incomplète
interdit la mise en service de l'outil.

Les cinq adaptateurs distribués sont décrits ci-dessous à partir de leur contrat
`SPEC`. Les colonnes `mode dégradé`, `données sensibles` et `erreurs` sont
pré-remplies par le starter : elles doivent être vérifiées, corrigées et
complétées par l'observation réelle des exécutions.

## Outils distribués

| Outil | Finalité | Arguments | Résultat | Source de vérité | Rôles | Timeout | Limite |
|---|---|---|---|---|---|---|---|
| `search_knowledge` | fonder une réponse sur une procédure ou une politique | `query`, `top_k` | `document_id`, `title`, `revision`, `excerpt`, `score` | corpus actif du manifeste | technicien, superviseur, auditeur, public | 1500 ms | 3 |
| `get_equipment` | lire la fiche d'inventaire | `equipment_id` | type, site, criticité, mise en service, fabricant, puissance | `equipment.csv` | technicien, superviseur, auditeur | 800 ms | 1 |
| `list_events` | lister les événements récents | `equipment_id`, `severity`, `limit` | événements triés du plus récent au plus ancien | `events.csv` | technicien, superviseur, auditeur | 1000 ms | 10 |
| `get_maintenance_history` | lire les dernières interventions | `equipment_id`, `limit` | interventions, issue, durée d'arrêt | `maintenance_history.csv` | technicien, superviseur, auditeur | 1200 ms | 10 |
| `diagnose_report` | lire un rapport et en extraire le squelette DiagOps | `report_id` | équipement, symptôme, indice de sévérité, preuves, revue humaine | `reports.jsonl` | technicien, superviseur, auditeur | 1000 ms | 1 |

## Fiche par outil

Reproduire ce bloc pour chaque outil, y compris ceux du starter.

### `nom_de_l_outil`

- **finalité** :
- **arguments et contraintes** :
- **résultat et champs exposés** :
- **source de vérité et fraîcheur** :
- **autorisation** : rôles admis et motif du refus des autres ;
- **timeout et limite de résultats** : valeur, justification, effet du dépassement ;
- **données sensibles** : ce qui est lu, ce qui est rendu, ce qui est tracé ;
- **erreurs connues** : cas, signal, effet sur l'exécution ;
- **mode dégradé** : comportement attendu quand la source est absente, vide ou lente ;
- **preuve** : scénario du jeu gelé qui exerce l'outil.

## Interdits

- aucun outil n'envoie, n'écrit, ne commande, ne modifie ni ne déclenche ;
- aucune connexion arbitraire n'est exposée au modèle ;
- aucun outil n'est ajouté sans scénario de test associé ;
- aucun argument brut n'apparaît dans les traces.

## Journal des modifications

| Date | Outil | Modification | Motif | Décidée par |
|---|---|---|---|---|
| | | | | |
