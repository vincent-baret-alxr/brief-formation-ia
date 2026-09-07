# Protocole M1

> Note de reconstruction : ce dossier a ete reconstitue apres la perte du
> depot de travail local (`M1/starter/work/` etait ignore par erreur par le
> `.gitignore` racine, corrige depuis). Seuls les elements dont les valeurs
> exactes ont ete conservees figurent ci-dessous ; les champs sans donnee
> retrouvee restent vides plutot que d'etre reconstitues de memoire.

## Question

Le fine-tuning LoRA de `Qwen/Qwen3-0.6B` apporte-t-il un gain mesurable par
rapport au modele brut pour transformer un rapport technicien en diagnostic
JSON DiagOps, et quel reglage (nombre d'epoques, learning rate) maximise ce
gain sur la configuration commune (r=16, alpha=32) ?

## Hypothese

- Si : le modele est adapte par LoRA sur les modules d'attention avec la
  configuration commune,
- Alors : la conformite au schema JSON et l'exactitude `equipment_id`
  augmentent nettement par rapport au modele brut, tandis que la
  classification `severity` reste sensible au nombre d'epoques,
- Parce que : 3 epoques sur 320 exemples peuvent laisser le modele
  sous-entraine sur la partie la plus fine de la tache (classification),
  la structure JSON elle-meme etant plus rapide a apprendre.

## Systeme controle

- modele et revision : `Qwen/Qwen3-0.6B`,
  `c1899de289a04d12100db370d81485cdf75e47ca`, dtype `bfloat16` ;
- prompt et chat template : template de chat standard, `enable_thinking: false` ;
- parametres de generation (baseline et candidats) : `max_new_tokens: 256`,
  `do_sample: false`, `temperature: 0.0` ;
- split et seed : seed `42`, 320 exemples d'entrainement / 80 de validation
  issus de `diagops_train.jsonl` ;
- metriques : JSON parseable, schema valide, exactitude `equipment_id`,
  macro-F1 `severity`, exactitude `requires_human_review`, score lexical
  textuel, latence mediane/p95, debit, score composite ;
- environnement : non conserve (fiche `environment.json` perdue).

## Runs

| Run | Variable modifiee | Valeur | Prediction formulee avant execution |
|---|---|---|---|
| Baseline | aucune | sans LoRA | non disponible (run non conserve) |
| Reference | aucune | r=16, alpha=32, dropout=0.05, epochs=3, lr=2e-4 | La structure JSON et `equipment_id` devraient etre fiables, mais `severity` restera imparfaite apres seulement 3 epoques. |
| Variation 1 | `training.epochs` | 3 -> 5 | Plus d'epoques ameliore la conformite au schema et le macro-F1 `severity`, sans changer le format de sortie. |
| Variation 2 | `training.learning_rate`, compare a Variation 1 (epochs=5 fixe) | 2e-4 -> 1e-4 | Un learning rate plus faible peut stabiliser l'apprentissage mais aussi ralentir la convergence sur seulement 5 epoques, avec un effet incertain sur le score composite. |

Variation 2 modifie une seule variable par rapport a Variation 1 (et non par
rapport a Reference) afin de respecter la regle d'une seule variable changee
a la fois : Variation 1 sert de base locale pour isoler l'effet du learning
rate independamment de celui du nombre d'epoques.

## Resultats obtenus

| Run | Schema valide | `equipment_id` | Severity macro-F1 | Score textuel | Latence p95 (s) | Score composite |
|---|---:|---:|---:|---:|---:|---:|
| Baseline | — | — | — | — | — | — |
| Reference (3 ep., lr 2e-4) | 0.9875 | 1.0 | 0.7489 | 0.6577 | 6.264 | 89.693 |
| Variation 1 (5 ep., lr 2e-4) | 1.0 | 1.0 | 0.9547 | 0.9431 | 6.304 | 98.088 |
| Variation 2 (5 ep., lr 1e-4) | — | — | — | — | — | 95.146 |

Pour Variation 2, seul le score composite a ete conserve ; le detail par
metrique n'a pas ete retrouve.

## Regle de decision

Non retrouvee : les criteres de retenue/rejet/reexperimentation fixes avant
resultats n'ont pas ete conserves dans les notes disponibles.

## Gel

- commit :
- date :
- auteurs :
