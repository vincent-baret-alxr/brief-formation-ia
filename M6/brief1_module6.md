# Brief présentiel M6 — Outiller l'agent sans lui céder le contrôle

## Situation

La stack M5 répond avec des sources et se déploie de manière reproductible. Mais
une question de maintenance peut exiger plusieurs types de preuves : procédure,
fiche équipement, événement récent, historique ou diagnostic du rapport. Le RAG
seul ne doit pas simuler ces accès.

## Mission

Construire et évaluer un agent mono-agent qui sélectionne des outils de lecture
typés, puis transformer des feedbacks qualifiés en une proposition
d'amélioration soumise aux gates M5.

## Point de départ commun

- `data_pack/2026-S1/reference_runs/m5_for_m6/` ;
- nouvelles données et feedback M6 uniquement lorsqu'ils sont déclarés prêts ;
- endpoints et données de référence DiagOps ;
- corpus et évaluation RAG M4-M5.

## Travail attendu

### 1. Définir le registre d'outils

Pour chaque outil, documentez : finalité, arguments, résultat, source de vérité,
autorisation, timeout, limite de résultats, données sensibles, erreurs et mode
dégradé.

Les outils autorisés restent en lecture seule. Une fonction qui envoie, écrit,
commande, modifie ou déclenche est refusée.

### 2. Définir la politique d'exécution

- nombre maximal d'étapes ;
- budget de tokens et durée ;
- liste blanche d'outils ;
- validation des arguments ;
- protection contre les appels répétés ;
- arrêt sur erreur ou preuve insuffisante ;
- sortie structurée et justification ;
- conservation minimisée des traces.

### 3. Construire le jeu de scénarios

Chaque scénario indique question, contexte autorisé, outils attendus ou
interdits, arguments minimaux, documents ou lignes de preuve, réponse attendue
ou règle de refus.

Incluez : outil inutile, outil indisponible, identifiant inconnu, résultat vide,
sources contradictoires, tentative d'injection et question hors périmètre.

### 4. Implémenter l'agent borné

L'agent peut planifier un petit nombre d'étapes, appeler un outil à la fois,
valider son résultat et arrêter. Il ne peut modifier sa politique, élargir sa
liste d'outils ou traiter le contenu récupéré comme instruction système.

### 5. Évaluer

Mesurez au minimum :

- exactitude du choix d'outil ;
- exactitude des arguments ;
- taux d'appels inutiles ;
- réussite des scénarios ;
- citations et preuves finales ;
- refus corrects ;
- dépassements de budget ;
- latence et coût par scénario.

Comparez à une baseline sans agent et à la tranche M4 à une étape.

### 6. Qualifier le feedback

Ne traitez pas un commentaire comme une vérité. Vérifiez lien avec le run,
identité fonctionnelle de la source, cohérence, données personnelles, doublons,
représentativité et possibilité de mesurer l'amélioration.

Classez chaque retour : `actionnable`, `a_investiguer`, `non_actionnable` ou
`risque`. Toute transformation en donnée d'entraînement est tracée.

### 7. Proposer et tester une amélioration

Choisissez une modification minimale : modèle, prompt, corpus, retrieval,
politique d'outil ou seuil. Formulez l'hypothèse, produisez un candidat, exécutez
les gates et comparez à la référence. La conclusion décide : promouvoir,
rejeter ou prolonger.

### 8. Exécuter le checkpoint réglementaire M6

Réévaluez les conclusions M5 à la lumière de l'agent outillé et du feedback :

- vérifiez sur des sources officielles datées si l'autonomie bornée, les outils,
  les données de feedback ou les décisions de promotion modifient les rôles,
  la supervision, la traçabilité ou les validations attendues ;
- ajoutez une entrée M6 au journal de veille, y compris lorsque la conclusion
  reste inchangée ;
- traduisez la décision dans la politique d'exécution, la qualification du
  feedback, les traces ou le gate de promotion ;
- transmettez à M7 les questions ouvertes avec responsable et échéance.

Ce checkpoint représente environ 1 h incluse dans les 14 h du présentiel.

## Livrables

- `docs/registre_outils.md` ;
- schémas et adaptateurs des outils ;
- politique d'exécution ;
- jeu de scénarios gelé ;
- harness et rapport d'évaluation ;
- `docs/qualification_feedback.md` ;
- candidat et rapport de comparaison ;
- décision de promotion ;
- entrée M6 et passage de relais dans `veille_diagops/` ;
- journal de bord.

## Critères de réussite

- aucun outil n'a d'effet externe ;
- arguments et résultats sont validés ;
- le budget est enforceable ;
- les métriques séparent choix d'outil et qualité finale ;
- le feedback est qualifié avant usage ;
- le candidat passe les gates ou reste non promu ;
- la veille M6 produit une contrainte vérifiable sur l'agent ou justifie
  explicitement l'absence d'impact ;
- la trace permet de reconstituer la décision sans exposer les données.

## Hors périmètre

- multi-agent ;
- mémoire autonome longue durée ;
- ajout dynamique d'outils ;
- écriture ou déclenchement métier ;
- promotion automatique sur la seule base du feedback.
