# Sources and provenance

## Canonical language scope

EUROPA Eval uses the 36 prioritized macro-languages listed by the OpenEuroLLM training-data catalogue:

- **Source:** [OpenEuroLLM training-data catalogue — languages](https://github.com/OpenEuroLLM/training-data-catalogue/blob/main/languages)
- **Repository:** [OpenEuroLLM/training-data-catalogue](https://github.com/OpenEuroLLM/training-data-catalogue)
- **Accessed:** 2026-09-03
- **License:** Apache-2.0

The local registry preserves ISO 639-3 macro-language codes, BCP 47 tags, autonyms, primary scripts and all internal catalogue variants. EUROPA evaluates 36 macro-languages, while the catalogue contains more language/script variant codes.

## Original pilot items

All 12 English semantic templates were authored for EUROPA Eval and released under CC0-1.0. They were adapted from the transparent capability patterns developed in [SVEA Eval](https://github.com/BirgerMoell/svea-eval), not copied from third-party benchmark questions.

The generated packs preserve their translation metadata in each committed JSON file. The source template is `src/europa_eval/resources/pack-source-en.json`; generated packs are under `src/europa_eval/resources/language-packs/`. Any quality correction after generation is also recorded in the affected pack rather than folded invisibly into the model provenance.

## Translation generator

The v0.1 machine-translated packs were produced locally with the Ollama checkpoint label `qwen3.6:35b-a3b`, revision `07d35212591f`, temperature 0, seed 42 and thinking disabled. This is generation provenance, not an endorsement or a native-quality claim.

## Complementary evaluation resources

- [OpenEuroLLM](https://github.com/OpenEuroLLM)
- [OpenEuroLLM oellm-eval](https://github.com/OpenEuroLLM/oellm-eval)
- [EuroEval](https://euroeval.com/)
- [SVEA Eval](https://birgermoell.github.io/svea-eval/)

EUROPA links to these projects and does not redistribute their datasets. Their licenses and task-specific terms remain authoritative.

## What must be cited in a result

A reproducible result should identify the EUROPA suite version, target model ID and immutable revision, backend, decoding settings, reasoning mode, judge model and revision for rubric items, and any added model-specific limitations. The result artifact records these fields directly.
