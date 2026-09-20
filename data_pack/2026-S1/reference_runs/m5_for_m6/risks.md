# Risques transmis à M6

| Risque | Contrôle existant en M5 | Preuve attendue en M6 |
|---|---|---|
| Agence excessive | Une seule action, aucun outil | Politique d'exécution bornée et budget vérifiable |
| Outil à effet externe | Aucun outil déclaré | Registre d'outils en lecture seule et test d'absence d'effet |
| Injection indirecte par un document | Contenu traité comme donnée | Résultat d'outil traité comme donnée, campagne adversariale |
| Argument d'outil détourné | Sans objet avant M6 | Validation stricte des arguments et filtrage d'accès avant lecture |
| Coût non maîtrisé | Requête unique | Budget d'étapes, de durée et mesure du coût par scénario |
| Feedback pris pour une vérité | Sans objet avant M6 | Qualification documentée avant tout usage |
| Donnée personnelle dans un retour | Minimisation des traces | Détection, exclusion et traçabilité de la décision |
| Régression non détectée | Baseline de calibration | Comparaison candidat contre référence sur scénarios historiques |
| Promotion non contrôlée | Gate de release | Décision humaine explicite, rollback disponible |

## Risques résiduels connus

- la baseline lexicale privilégie les documents longs : un outil structuré peut
  paraître meilleur sans que la réponse finale s'améliore ;
- le corpus contient une révision remplacée (`DOC-LOTO-001`) : toute citation de
  cette révision est une régression, pas une variante acceptable ;
- le lot de feedback `2027-S1` n'est pas représentatif du parc : sa composition
  doit être mesurée avant tout usage.
