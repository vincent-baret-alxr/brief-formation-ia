# Risques transmis à M5

| Risque | Contrôle existant | Preuve attendue en M5 |
|---|---|---|
| Mauvaise attribution de version | Manifeste de release | Versions exposées par l'API et liées aux traces |
| Index incohérent avec le corpus | Checksums et manifeste | Construction atomique et gate avant promotion |
| Citation absente ou inaccessible | Contrat de réponse | Métrique et test bloquant |
| Réponse sans preuve | Abstention obligatoire | Taux de refus mesuré |
| Injection indirecte | Contenu traité comme donnée | Test de sécurité en CI |
| Donnée sensible dans les traces | Minimisation exigée | Revue des champs, accès et rétention |
| Régression non détectée | Baseline de calibration | Alerte, décision et rollback chronométré |
