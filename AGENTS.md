# EUROPA Eval agent guide

EUROPA Eval is a 36-language LLM capability benchmark. Keep these contracts intact:

- Treat `src/europa_eval/resources/suites/` as the canonical bundled suite data.
- Keep exactly the declared template coverage for every declared language.
- Every item needs language, script, template, provenance, license, scoring, domain, capability, task type and review state.
- Preserve raw model output and exact run protocol in result artifacts.
- Never turn missing or unjudged evidence into zero.
- Never present diagnostic, oracle, partial, machine-translation-only or protocol-mismatched runs as definitive leaderboard evidence.
- Keep the dependency-free core working on Python 3.11+.
- API keys are read only from named environment variables and are never saved.
- Use `python3 -m europa_eval validate`, `python3 -m unittest discover -s tests -v`, and `python3 -m europa_eval build-site` before publishing.

The public pilot is a development and translation-review instrument, not a hidden test set. Promote a language pack only after native review is recorded in its committed metadata.
