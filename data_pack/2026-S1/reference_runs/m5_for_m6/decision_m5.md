# Décision de sortie M5

## Décision

La release `diagops-m5-reference-r1` est admise comme **référence saine de
préproduction pour M6**. Cette admission autorise son exploitation observée, sa
restauration et son usage comme point de comparaison ; elle n'autorise ni usage
industriel réel, ni promotion automatique d'un successeur.

## Conditions

- conserver le corpus, le prompt et le jeu d'évaluation gelés ;
- conserver les contrôles de rôle, de citation et d'abstention ;
- reconstruire l'index hors du chemin actif, puis promouvoir atomiquement ;
- bloquer toute promotion lorsqu'un gate régresse ;
- conserver une version saine restaurable et chronométrer la restauration ;
- n'ajouter aucune capacité d'action externe sans décision documentée.

## Ce que M6 peut modifier

Un seul axe principal par candidat : modèle, prompt, corpus, retrieval,
politique d'outil ou seuil. Toute modification est comparée à cette référence
avant décision humaine.

## Ce que M6 ne peut pas modifier

- le caractère lecture seule des accès ;
- l'obligation de citer une source admissible ;
- la séparation des splits de calibration et de test ;
- la conservation d'une version restaurable.

## Limites

Les données et procédures sont synthétiques. Le passage des gates de calibration
ne démontre ni robustesse industrielle, ni conformité réglementaire, ni qualité
d'une génération libre.
