# Contributing to EUROPA Eval

The highest-value v0.1 contribution is a careful native review of one language pack.

## Review a language pack

1. Choose a JSON file in `src/europa_eval/resources/language-packs/` whose `review_status` is `machine_translated`.
2. Check all strings against `pack-source-en.json` for semantic equivalence, naturalness, difficulty and exact response instructions.
3. Confirm option B is correct on both multiple-choice templates.
4. Preserve protected literals, JSON keys, dates, times, numbers and the English `translation_source`.
5. Confirm `strict_answer` is exactly `ORION-7|420000|OK`.
6. Recompute the surface metric under the written Unicode-letter/whitespace-token protocol.
7. Set `review_status` to `native_reviewed` and add `native_review` with reviewer name or handle, date, variant/script reviewed and short notes.
8. Run the suite builder, validator and tests.

```bash
python3 scripts/build_core_suite.py
python3 -m europa_eval validate
python3 -m unittest discover -s tests -v
python3 -m europa_eval build-site --docs docs --results results/runs
```

Do not mark a pack reviewed if you cannot evaluate its naturalness and implied difficulty as a fluent speaker.

## Add a template

A parallel template must be language-portable, unambiguous, short enough for local evaluation, openly licensed and accompanied by deterministic gold or a precise judge rubric. Add the English source fields, update the pack generator, provide all 36 translations, add the template ID to the suite builder and tests, and explain the capability gap it fills.

Culture-specific tasks are welcome as a separately labeled native layer. Do not force nominally parallel translations when cultural adaptation changes the construct.

## Submit a run

A public result must:

- cover the complete current suite;
- pin the target model revision or Ollama digest;
- configure a named, pinned judge for rubric items;
- contain no generation errors or unjudged items;
- preserve raw responses and protocol metadata;
- disclose model-specific limitations;
- avoid editing the generated score summary manually.

Diagnostic language-filtered and oracle runs are useful for tests but are intentionally excluded from the project page.

## Pull request checklist

- `europa validate` passes.
- The unit test suite passes.
- `docs/data` was regenerated and has no unexplained diff.
- New text and data have an explicit license and source.
- The change does not turn missing evidence into zero.
- The change does not merge reasoning-on and reasoning-off evidence.
- Native-review claims identify the reviewed language variant and script.
