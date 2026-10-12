# EUROPA Eval and EuroEval: external comparison

_Snapshot checked 12 October 2026. This is an overlap audit, not a validation claim._

## What each benchmark measures

EUROPA Eval v0.1 is a lightweight, public **post-training capability probe**. It gives each of the 36 OpenEuroLLM target languages the same 12 task templates: reading, arithmetic, grounded answering, abstention, structured output, instruction following, tool recovery, a defined text calculation, summarization, translation, refusal, and revision tracking. It runs models zero-shot and reports item scores from 0 to 1, along with language, domain, format, and judge evidence. The 35 translated packs still need native review. See [our methodology](METHODOLOGY.md).

[EuroEval](https://euroeval.com/) is a broader, independent European-language benchmark using multiple datasets and tasks. Its [generative leaderboard](https://github.com/EuroEval/EuroEval/blob/main/src/frontend/md/leaderboards-README.md) is ordinarily few-shot; its chat leaderboard is zero-shot. Its **rank score is lower-is-better**, based on standardized distances from the best model within each dataset and averaged through tasks and languages. Rank scores from different leaderboard categories are not interchangeable. The number is neither an accuracy percentage nor a conversion of EUROPA's 0–100% item score. See [EuroEval's scoring method](https://github.com/EuroEval/EuroEval/blob/main/src/frontend/md/methodology.md).

The benchmarks are complementary: EuroEval provides breadth and native task datasets; EUROPA makes a small set of post-training behaviors and their final answers inspectable under one parallel protocol. Agreement between them remains an empirical question.

## Overlap audit

We checked all eight published full-suite EUROPA runs against EuroEval's [European all-models leaderboard](https://euroeval.com/leaderboards/european) on the date above. The [deployed CSV snapshot](https://euroeval.com/assets/european_all_models-DttHrEgc.js) is the source for the EuroEval entries and figures below. We used **exact model IDs** as the initial matching rule; family resemblance was not counted. EuroEval's public table does not pin the same weight SHA or inference settings as a EUROPA artifact, so even a same-ID row is not a revision-confirmed replication.

| EUROPA model (pinned in its run artifact) | EUROPA overall | EuroEval overlap | Eligible for checkpoint-level correlation? |
| --- | ---: | --- | --- |
| `swiss-ai/Apertus-8B-Instruct-2509` | 57.3% | Same model ID; language-level rank scores in 13 languages in the European all-models table, but no European aggregate for this incomplete row. Weight revision unconfirmed. | No |
| `gemma4:31b` | 77.3% | Related `google/gemma-4-31B-it` validation row has rank score **1.65 ± 0.12**. Ollama digest, quantization and prompt protocol are not verified as equivalent. | No |
| `gemma4:e2b` | 64.6% | Related `google/gemma-4-E2B-it` validation row has rank score **2.91 ± 0.14**. Not an exact checkpoint match. | No |
| `qwen3.6:35b-a3b` | 88.1% | No same-ID row in the European table. | No |
| `birgermoell/oellm-9b-threeway-dpo-full-v1` | 84.0% | No same-ID row. | No |
| `Neonkraft/oellm-9b-256k-theta64m-prelude-anneal300b-instruct-sft` | 76.2% | No same-ID row. | No |
| `nicher92/long-ctx-checkpoint-4000` | 57.3% | No same-ID row. | No |
| `openeurollm/oellm-9b-256k-sft` | 46.6% | No same-ID row. | No |

EUROPA values are rounded from the committed [run artifacts](../results/runs/), each with 432/432 scored items. EuroEval's two Gemma numbers are **validation-split rank scores**, not EUROPA-style percentages. Apertus's language-level rank scores must not be averaged with the 36-language EUROPA percentage: the language coverage, task set and scale differ.

**Conclusion:** one of eight runs has the same public model ID, and zero are confirmed to use the same pinned weight revision and protocol in both benchmarks. A checkpoint-level Pearson or Spearman correlation is **not estimable**. Reporting one would imply evidence that does not exist.

## A defensible next comparison

1. Choose several EuroEval-listed, open-weight instruction checkpoints with identifiable revisions, preferably at least ten covering a range of model strengths; run those exact revisions through EUROPA under one target and judge protocol.
2. Record EuroEval category, split, prompting mode, version, task coverage, failure counts and model revision where available. Keep validation-only results separate from test results. Do not silently substitute an Ollama quantization for a Hugging Face checkpoint.
3. Restrict analysis to languages with evidence in **both** benchmarks and state the coverage matrix. Compare conceptually related task slices as well as overall model order; do not treat their raw score scales as equal.
4. Predeclare Spearman rank correlation as an exploratory ordering check, report confidence intervals and sensitivity to each model and language, and inspect disagreements item by item. Human review of EUROPA's translated packs and judge calibration should precede any stronger validity claim.

No coefficient is published until this matching and review work is done.
