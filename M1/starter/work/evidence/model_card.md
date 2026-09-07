# Model card — DiagOps M1

> Reconstruction partielle : seules les valeurs listees ci-dessous ont ete
> retrouvees. Les sections sans donnee restent vides (voir
> `protocol_m1.md` pour le detail de la reconstruction).

## Identification

- modele de base : `Qwen/Qwen3-0.6B`
- revision : `c1899de289a04d12100db370d81485cdf75e47ca`
- adaptateur : LoRA (r=16, alpha=32, dropout=0.05, cibles `q_proj`, `k_proj`,
  `v_proj`, `o_proj`) — trois runs compares (reference, variation 1,
  variation 2)
- commit du depot :
- date :

## Usage prevu

Transformer un rapport technicien en diagnostic JSON structure (DiagOps),
avec revue humaine obligatoire sur les cas signales par
`requires_human_review`. Le modele n'automatise aucune decision
d'intervention.

## Donnees

- origine : `data_pack/2026-S1/annotations/diagops_train.jsonl`
- volumes train / validation / test : 320 / 80 / (test non consulte au stade
  Brief 1)
- limites connues :

## Entrainement

- configuration : LoRA r=16, alpha=32, dropout=0.05, `max_length=512`,
  batch 4, accumulation 4, warmup 0.1, weight decay 0.01, seed 42
- environnement : non conserve
- duree : non conservee
- variations comparees :
  - Reference : `epochs=3`, `learning_rate=2e-4`
  - Variation 1 : `epochs=5`, `learning_rate=2e-4`
  - Variation 2 : `epochs=5`, `learning_rate=1e-4` (comparee a Variation 1)

## Evaluation

Table etendue a trois candidats LoRA (baseline non disponible).

| Metrique | Baseline | Reference (3 ep.) | Variation 1 (5 ep., lr 2e-4) | Variation 2 (5 ep., lr 1e-4) |
|---|---:|---:|---:|---:|
| JSON parseable | | 1.0 | 1.0 | |
| Schema valide | | 0.9875 | 1.0 | |
| Equipment ID | | 1.0 | 1.0 | |
| Severity macro-F1 | | 0.7489 | 0.9547 | |
| Revue humaine (exactitude) | | 0.9875 | 0.9875 | |
| Score textuel | | 0.6577 | 0.9431 | |
| Latence p95 (s) | | 6.264 | 6.304 | |
| Score composite | | 89.693 | 98.088 | 95.146 |

## Robustesse

Non evalue a ce stade (Brief 2).

## Decision

- promouvoir / ne pas promouvoir / prolonger :
- preuves principales :
- risques :
- conditions de reexamen :

## Limites

Ce modele ne remplace pas la decision d'un technicien et ne commande aucun
equipement.
