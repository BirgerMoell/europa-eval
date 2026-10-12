# EUROPA Eval and EuroEval: external comparison

_Snapshot checked 12 October 2026. This is a descriptive comparison of existing runs, not a validation claim._

## What each benchmark measures

EUROPA Eval v0.1 is a lightweight, public **post-training capability probe**. It gives each of the 36 OpenEuroLLM target languages the same 12 task templates: reading, arithmetic, grounded answering, abstention, structured output, instruction following, tool recovery, a defined text calculation, summarization, translation, refusal, and revision tracking. It runs models zero-shot and reports item scores from 0 to 1, along with language, domain, format, and judge evidence. The 35 translated packs still need native review. See [our methodology](METHODOLOGY.md).

[EuroEval](https://euroeval.com/) is a broader, independent European-language benchmark using multiple datasets and tasks. Its [generative leaderboard](https://github.com/EuroEval/EuroEval/blob/main/src/frontend/md/leaderboards-README.md) is ordinarily few-shot; its chat leaderboard is zero-shot. Its **rank score is lower-is-better**, based on standardized distances from the best model within each dataset and averaged through tasks and languages. Rank scores from different leaderboard categories are not interchangeable. The number is neither an accuracy percentage nor a conversion of EUROPA's 0–100% item score. See [EuroEval's scoring method](https://github.com/EuroEval/EuroEval/blob/main/src/frontend/md/methodology.md).

The benchmarks are complementary: EuroEval provides breadth and native task datasets; EUROPA makes a small set of post-training behaviors and their final answers inspectable under one parallel protocol. We can inspect whether their *model orderings* agree where the published results overlap, without equating their score scales.

## Overlap audit

We checked all eight published full-suite EUROPA runs against EuroEval's [European all-models leaderboard](https://euroeval.com/leaderboards/european) on the date above. The [deployed CSV snapshot](https://euroeval.com/assets/european_all_models-DttHrEgc.js) is the source for the EuroEval entries and figures below. We used **exact model IDs** as the initial matching rule; family resemblance was not counted. EuroEval's public table does not pin the same weight SHA or inference settings as a EUROPA artifact, so even a same-ID row is not a revision-confirmed replication.

| EUROPA model (pinned in its run artifact) | EUROPA overall | EuroEval overlap | Eligible for checkpoint-level correlation? |
| --- | ---: | --- | --- |
| `swiss-ai/Apertus-8B-Instruct-2509` | 57.3% | Same model ID; language-level rank scores in 13 languages in the European all-models table, but no European aggregate for this incomplete row. Weight revision unconfirmed. | No |
| `gemma4:31b` | 77.3% | Related `google/gemma-4-31B-it` validation row has rank score **1.65 ± 0.12**. Ollama digest, quantization and prompt protocol are not verified as equivalent. | No |
| `gemma4:e2b` | 64.6% | Related `google/gemma-4-E2B-it` validation row has rank score **2.91 ± 0.14**. Not an exact checkpoint match. | No |
| `qwen3.6:35b-a3b` | 88.1% | No same-ID row. A **different-generation** `Qwen/Qwen3.5-35B-A3B-FP8` validation entry has rank score **1.63 ± 0.12**; context only, not included in the ordering check. | No |
| `birgermoell/oellm-9b-threeway-dpo-full-v1` | 84.0% | No same-ID row. | No |
| `Neonkraft/oellm-9b-256k-theta64m-prelude-anneal300b-instruct-sft` | 76.2% | No same-ID row. | No |
| `nicher92/long-ctx-checkpoint-4000` | 57.3% | No same-ID row. | No |
| `openeurollm/oellm-9b-256k-sft` | 46.6% | No same-ID row. | No |

EUROPA values are rounded from the committed [run artifacts](../results/runs/), each with 432/432 scored items. EuroEval's two Gemma numbers are **validation-split rank scores**, not EUROPA-style percentages. Apertus's language-level rank scores must not be averaged with the 36-language EUROPA percentage: the language coverage, task set and scale differ.

**Conclusion:** one of eight runs has the same public model ID, and zero are confirmed to use the same pinned weight revision and protocol in both benchmarks. A checkpoint-level Pearson or Spearman correlation is **not estimable**. Reporting one would imply evidence that does not exist.

## What the existing language scores show

Three model families have useful overlapping **language-level** results: Apertus 8B, Gemma 4 31B and Gemma 4 E2B. Apertus has one exact public model ID in both sources, but no confirmed common weight revision; the two Gemma rows are related Hugging Face and Ollama variants, not verified checkpoint matches. We therefore treat this as a *family-level directional check*, not a matched-checkpoint analysis. We excluded EuroEval's Faroese Apertus result because EUROPA has no Faroese pack, and restricted the comparison to the 12 languages present for all three entries.

Each cell below gives **EUROPA item score % / EuroEval validation rank score**. Higher is better in the first number; **lower** is better in the second. The figures come from the committed [EUROPA run artifacts](../results/runs/) and the [EuroEval European all-models CSV snapshot](https://euroeval.com/assets/european_all_models-DttHrEgc.js). They are shown side by side to make the ordering check auditable, not to suggest that the values have the same units.

| Language | Apertus 8B | Gemma 4 31B | Gemma 4 E2B |
| --- | ---: | ---: | ---: |
| Bosnian | 60.1 / 1.94 | 78.0 / 1.16 | 65.3 / 1.83 |
| Bulgarian | 50.7 / 3.31 | 69.5 / 1.65 | 66.6 / 2.95 |
| Catalan | 64.2 / 3.53 | 78.8 / 2.11 | 66.1 / 3.35 |
| Czech | 64.2 / 2.95 | 78.9 / 1.73 | 67.0 / 3.01 |
| English | 53.3 / 2.13 | 78.6 / 1.26 | 67.2 / 2.21 |
| Estonian | 54.7 / 3.19 | 75.7 / 2.20 | 56.8 / 3.79 |
| Latvian | 62.3 / 2.46 | 77.5 / 1.62 | 59.4 / 2.87 |
| Norwegian | 51.7 / 2.63 | 79.6 / 1.48 | 68.3 / 2.82 |
| Polish | 67.2 / 2.96 | 78.0 / 1.58 | 76.1 / 2.94 |
| Romanian | 64.2 / 3.27 | 77.8 / 1.57 | 67.1 / 2.92 |
| Slovak | 63.0 / 3.07 | 76.7 / 1.72 | 63.8 / 3.15 |
| Slovene | 68.4 / 3.14 | 77.7 / 1.64 | 61.3 / 3.22 |

For each language, there are three model-pair orderings. **31 of the 36 orderings agree** between benchmarks. Gemma 31B is ahead of both others in both sources for all 12 languages (24 of the agreements). Apertus versus Gemma E2B agrees in seven languages and reverses in five: **Czech, English, Estonian, Norwegian and Slovak**. For instance, EUROPA favors E2B over Apertus in Estonian (56.8% versus 54.7%), while EuroEval favors Apertus (rank score 3.19 versus 3.79).

This is a useful descriptive signal, but **31/36 is not a correlation coefficient or a validation rate**. The 36 checks reuse the same three model families and are not independent; two of those families are not checkpoint-matched. EuroEval's generative validation results and EUROPA's zero-shot pilot also differ in task mix, prompting and language coverage. EUROPA's 35 translated language packs still need native review. The Qwen3.6 run is not part of this calculation: EuroEval's Qwen3.5 reference is a different model generation, even though both are strong in their respective leaderboards.

## A defensible next comparison

1. Choose several EuroEval-listed, open-weight instruction checkpoints with identifiable revisions, preferably at least ten covering a range of model strengths; run those exact revisions through EUROPA under one target and judge protocol.
2. Record EuroEval category, split, prompting mode, version, task coverage, failure counts and model revision where available. Keep validation-only results separate from test results. Do not silently substitute an Ollama quantization for a Hugging Face checkpoint.
3. Restrict analysis to languages with evidence in **both** benchmarks and state the coverage matrix. Compare conceptually related task slices as well as overall model order; do not treat their raw score scales as equal.
4. Predeclare Spearman rank correlation as an exploratory ordering check, report confidence intervals and sensitivity to each model and language, and inspect disagreements item by item. Human review of EUROPA's translated packs and judge calibration should precede any stronger validity claim.

No coefficient is published until this matching and review work is done.
