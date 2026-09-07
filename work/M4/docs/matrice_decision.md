# Matrice de décision M4

| Option | Qualité | Robustesse | Latence | Mémoire | Coût par réponse | Exploitation | Réversibilité |
|---|---:|---:|---:|---:|---:|---:|---:|
| Maintenir la baseline M3 (règles) | F1 fenêtre 0,375 ; comportement entièrement prévisible et explicable | Aucune variance d'entraînement ; comportement identique à chaque exécution | Négligeable (règles simples, pas d'inférence) | Négligeable | ~0 (pas de calcul modèle) | Déjà en place, aucun changement | Totale (rien à défaire) |
| Adopter le modèle simple (forêt aléatoire) | F1 fenêtre 0,381, marginalement supérieur ; rappel instable (0,00–0,67 selon le pli) | Faible à ce volume : 30 échantillons, 22 groupes, forte variance inter-plis | 62 ms entraînement, 3 ms prédiction (négligeable en pratique) | Quelques centaines de Ko | Faible, mais nécessite un pipeline de features à maintenir | Ajoute une dépendance scikit-learn et un ré-entraînement périodique à planifier | Élevée (modèle remplaçable par la baseline sans changement de contrat de sortie) |
| Adopter le RAG hybride (retrieval + citations + abstention) | Hit rate 1,00, précision contexte 0,517, 0 erreur de contrat sur 12 réponses de calibration | Dépend d'un corpus documentaire tenu à jour (statuts, checksums) ; comportement déterministe hors ré-indexation | 4,2 ms retrieval hybride + 8,9 s de construction d'index (une fois par démarrage) | 12 288 octets d'index pour 8 documents ; croît linéairement avec le corpus | Faible au volume actuel ; à revoir si le corpus documentaire grossit significativement | Nécessite de maintenir `manifest.csv` (droits, statut, checksum) à chaque publication de document | Élevée (aucun contenu généré librement ; citations vérifiables) |

## Décision

**`évaluer davantage`** pour le modèle capteur simple ; **`adopter`** pour le
RAG (retrieval hybride + réponses citées + agent borné à une étape), sous
les conditions ci-dessous.

Justification du modèle capteur : l'écart de F1 entre la forêt aléatoire
(0,381) et la baseline M3 ramenée au grain fenêtre (0,375) est de 0,006 sur
30 échantillons — à l'intérieur du bruit d'estimation (le rappel varie de
0,00 à 0,67 selon le pli de validation croisée). Rien ne justifie de
remplacer une baseline entièrement explicable par un modèle dont la
supériorité n'est pas démontrée. La baseline M3 reste en production ; le
modèle simple est conservé comme piste à réévaluer si le volume de fenêtres
étiquetées augmente (le brief indique explicitement que l'oracle de test
scellé sera noté par le formateur après ce gel — cette note future est la
prochaine occasion de trancher avec plus de données).

Justification du RAG : le retrieval hybride atteint un hit rate parfait
(1,00) sur les questions répondables de calibration, avec 0 erreur de
contrat de citation et une abstention correcte à 100 % (y compris le cas
sensible RAG-CAL-008). L'admissibilité filtre correctement les documents
obsolètes et restreints même quand ils sont bien classés. L'agent reste
strictement borné à trois actions, structurellement impossible à détourner
vers une écriture.

## Conditions de non-déploiement

- Le modèle capteur simple **ne doit pas** remplacer la baseline M3 en
  l'état : aucune preuve de gain fiable à 30 échantillons.
- Le RAG **ne doit pas** être ouvert à un rôle non couvert par
  `DOC-DATA-ACCESS-001`, ni connecté à un modèle génératif sans revalider le
  threat model (les réponses actuelles sont composées et validées par
  contrat, pas produites par un LLM — voir `docs/threat_model.md`, section
  « Limites »).
- Le champ `topic` nécessaire à la détection automatique de conflit de
  révisions (`src/conflict_check.py`) n'existe pas dans `manifest.csv` :
  ne pas présenter cette détection comme opérationnelle sur le corpus réel
  avant son ajout.

## Meilleur argument contraire

On pourrait adopter la forêt aléatoire malgré l'absence de gain démontré,
au motif qu'elle apprend des interactions entre indices (unité incohérente
et hors grille temporelle simultanément, par exemple) qu'une baseline par
règles indépendantes ne peut pas capturer par construction, et que ce
potentiel se révélera avec plus de données. Cet argument est réel mais ne
suffit pas à trancher aujourd'hui : rien dans les 30 fenêtres de calibration
ne démontre que cette capacité s'exprime déjà, et le rappel du modèle chute
à 0 sur au moins un pli de validation — un signal contraire au moins aussi
fort. D'où la décision « évaluer davantage » plutôt qu'« adopter » ou
« écarter ».
