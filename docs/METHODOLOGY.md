# EUROPA Eval methodology

## Purpose

EUROPA Eval is a lightweight capability probe across the 36 macro-languages prioritized by OpenEuroLLM. It is designed to answer a more useful question than “does the model speak this language?”: **which practical capabilities hold in which languages, under an explicitly recorded protocol?**

The v0.1 suite is a public development and translation-review pilot. It tests the evaluation machinery and creates a concrete native-review target. It is not a statistically comprehensive leaderboard.

## Parallel design

Every language has exactly 12 items derived from the same authored English templates. IDs are stable:

```text
europa-v01-{iso639-3}-{template-id}
```

Validation fails if a language is missing a template or if its language, script, scorer, source or review state is undeclared. This makes accidental coverage differences visible before a run starts.

The template set covers:

1. reading comprehension;
2. arithmetic;
3. grounded answering;
4. calibrated abstention;
5. strict structured output;
6. exact instruction following;
7. tool-error recovery;
8. an explicitly defined surface-text calculation;
9. summarization;
10. English-to-target translation;
11. harmful-request refusal;
12. revision tracking.

These tasks intentionally use names, IDs, dates and operational situations that can be carried across languages without requiring culture-specific background knowledge. Native expansions should add culturally grounded evidence without pretending it is parallel when it is not.

## Translation and review

English is the authored source pack. In v0.1, the remaining packs were generated locally by `qwen3.6:35b-a3b` with temperature 0, seed 42 and reasoning disabled. The generator preserves JSON keys, option letters, exact literals, dates, times, numbers and the English source sentence used by the translation task.

Machine translation is not treated as invisible preprocessing. Each item records:

- language, BCP 47 tag and script;
- source template;
- translation model and decoding protocol;
- any post-generation quality correction and the fields it changed;
- review state: `source_native`, `machine_translated`, or `native_reviewed`.

A native reviewer should check semantic equivalence, naturalness, task difficulty, option correctness, exact-output feasibility, script choice, metric derivation and all reference answers. Review is promoted per language pack and captured in version control.

## Scoring

Deterministic scorers handle multiple choice, exact text, numeric answers and JSON. Strict formats are part of the capability: code fences around a response that requested bare JSON are malformed and fail. A correct answer that begins with an unambiguous choice letter but violates a single-letter contract receives 0.5 and does not pass; a later incidental letter receives no credit.

Numeric surface calculations may declare relative-error partial credit:

```text
score = max(0, 1 - |prediction - gold| / |gold|)
```

The item’s precomputed tokens, character count, word count, unrounded value and rounded gold remain in scorer details. The metric is a protocol-following test—not a claim that raw average word length is a comparable readability measure across scripts or languages.

Open generation uses a 0–4 rubric per named dimension. An item score is the dimension mean divided by four. The default pass threshold is 0.75. A missing judge means missing evidence, not zero.

The judge prompt identifies the target language and requests concise evidence-based JSON. Target model and judge identities, revisions, backends and decoding settings are published separately.

## Aggregation

For every run EUROPA reports:

- micro item score;
- macro language score and weakest-language score;
- macro domain score and weakest-domain score;
- language, domain, capability and task-type slices;
- 95% normal-approximation intervals for descriptive orientation;
- malformed output, prompt-echo and repeated-span diagnostics;
- latency and token summaries;
- paired supported-versus-insufficient evidence retention.

Small-sample intervals are descriptive, not a claim of population representativeness. Scores from different suite versions, judges, reasoning modes or decoding protocols should not be compared as if only the checkpoint changed.

## Reasoning protocol

Reasoning is controlled run metadata. Ollama thinking is off unless explicitly enabled. A reasoning allowance is added separately from the item’s answer budget. Reasoning-on and reasoning-off runs are separate artifacts.

EUROPA does not publish private chain-of-thought. It publishes the final answer, reasoning-enabled flag and count metadata exposed by the backend, plus the named judge’s concise score rationale where applicable.

## Publication gate

The site includes only a run that is complete, non-diagnostic, fully scored, pinned to a model revision and matched to the current suite. Per-language filters are useful diagnostics but are deliberately not full-suite leaderboard evidence.

## Known limitations

- Thirty-five v0.1 packs need native review.
- Twelve items per language are far too small for definitive language rankings.
- Translationese may make generated tasks easier or less natural than native tasks.
- Judge scores require multilingual human calibration.
- The pilot is public and may become contaminated.
- Dialects, regional varieties, speech, multimodality and interactive agents are not yet measured.
- Norwegian, Latvian, Estonian, Albanian and Serbian have multiple internal catalogue variants; v0.1 does not exhaustively test every variant/script.

These constraints are displayed on the site and embedded in run artifacts.
