# EUROPA Eval

**One transparent capability protocol across the 36 languages prioritized by OpenEuroLLM.**

[Project site](https://birgermoell.github.io/europa-eval/) · [Methodology](docs/METHODOLOGY.md) · [Sources](docs/SOURCES.md) · [Contributing](CONTRIBUTING.md)

EUROPA Eval is a lightweight, inspectable LLM evaluation harness for hosted APIs, local Ollama models and direct Hugging Face Transformers inference. Its public pilot applies the same 12 semantic task templates to every target language: 432 items across 36 languages.

The project is a multilingual successor to [SVEA Eval](https://github.com/BirgerMoell/svea-eval). It preserves the useful parts of that design—deterministic scoring, resumable runs, pinned model and judge provenance, reasoning-protocol separation and answer-level deep links—while making language parity a first-class contract.

## What it measures

Each language receives exactly the same compact profile:

| Capability | Task form | Scoring |
|---|---|---|
| Reading comprehension | Multiple choice | Deterministic, strict letter |
| Arithmetic | Numeric | Deterministic |
| Grounded answering | Grounded QA | Deterministic |
| Calibrated abstention | Grounded QA contrast | Deterministic |
| Structured output | Exact JSON | Deterministic, strict format |
| Instruction following | Exact constrained output | Deterministic |
| Tool recovery | Multiple choice | Deterministic, strict letter |
| Surface calculation | Numeric | Deterministic, graded relative error |
| Summarization | Open generation | Named LLM judge required |
| English → target translation | Open generation | Named LLM judge required |
| Harmful-request refusal | Open generation | Named LLM judge required |
| Revision tracking | Exact JSON | Deterministic, strict format |

Scores are reported by language, domain, capability and task type. A single blended number is never the only output.

## Language scope

The canonical scope comes from the [OpenEuroLLM training-data catalogue](https://github.com/OpenEuroLLM/training-data-catalogue/blob/main/languages):

> Bulgarian, Czech, Danish, German, Greek, English, Estonian, Finnish, French, Irish, Croatian, Hungarian, Italian, Latvian, Lithuanian, Maltese, Dutch, Polish, Portuguese, Romanian, Slovak, Slovene, Spanish, Swedish, Catalan, Basque, Galician, Bosnian, Georgian, Macedonian, Albanian, Serbian, Turkish, Ukrainian, Icelandic and Norwegian.

The registry stores ISO 639-3, BCP 47, script, autonym, project group and every internal catalogue variant. Serbian records both Cyrillic and Latin; the v0.1 pilot uses the first declared script for generation.

## Important pilot status

Version 0.1 is a **translation-review pilot**, not a definitive multilingual leaderboard.

- English is the authored source pack.
- The other 35 packs were generated locally with `qwen3.6:35b-a3b`, temperature 0, seed 42 and reasoning disabled.
- Every item publishes that provenance and remains `machine_translated` until a native speaker reviews it.
- A pack can be promoted independently; review state is data, not marketing copy.
- The tasks are intentionally small. They test the harness and expose useful failure shapes, but do not replace native, culturally grounded benchmarks.

## Quick start

EUROPA’s core has no runtime dependencies beyond Python 3.11+.

```bash
git clone https://github.com/BirgerMoell/europa-eval.git
cd europa-eval
python3 -m pip install -e .
europa validate
europa list
```

### Local Ollama model

Run one language as a diagnostic:

```bash
europa run \
  --backend ollama \
  --model gemma4:31b \
  --revision YOUR_OLLAMA_DIGEST \
  --language swe \
  --diagnostic \
  --output results/runs/gemma4-swe.json
```

Run the complete suite with a separate named judge:

```bash
europa run \
  --backend ollama \
  --model YOUR_TARGET_MODEL \
  --revision TARGET_DIGEST \
  --judge-backend ollama \
  --judge-model YOUR_JUDGE_MODEL \
  --judge-revision JUDGE_DIGEST \
  --output results/runs/your-model.json
```

Open answers can also be judged later without regenerating target responses:

```bash
europa judge results/runs/your-model.json \
  --backend ollama \
  --model YOUR_JUDGE_MODEL \
  --revision JUDGE_DIGEST
```

### OpenAI-compatible API

```bash
export OPENAI_API_KEY="..."
europa run \
  --backend openai-compatible \
  --base-url https://api.example.com/v1 \
  --model YOUR_MODEL_ID \
  --revision PINNED_PROVIDER_VERSION \
  --judge-backend openai-compatible \
  --judge-model YOUR_JUDGE_ID \
  --output results/runs/your-model.json
```

### Hugging Face Transformers

```bash
python3 -m pip install -e '.[local]'
europa run \
  --backend huggingface \
  --model /path/to/checkpoint \
  --revision CHECKPOINT_SHA \
  --output results/runs/checkpoint.json
```

## Reasoning is a protocol, not a model label

Ollama thinking is disabled by default. To run a reasoning-enabled protocol, declare it explicitly and give it a separate allowance:

```bash
europa run \
  --backend ollama \
  --model qwen3.6:35b-a3b \
  --revision MODEL_DIGEST \
  --ollama-think \
  --ollama-reasoning-tokens 4096 \
  --output results/runs/qwen-reasoning-on.json
```

Reasoning-on and reasoning-off artifacts stay separate. The public site labels both, but does not publish private chain-of-thought. It can publish the final answer, reasoning-token metadata, deterministic scorer evidence and the concise rationale returned by the named judge.

## Result integrity

A result is publishable on the project site only when it:

- covers all 432 current-suite items;
- has no unscored or failed items;
- is not marked diagnostic;
- pins the target revision;
- matches the current suite ID and version.

Rubric items cannot silently become zero when no judge is configured. They remain unscored, which makes the run partial. API keys are read from environment variables and never saved.

The browser explorer’s URL includes both `run` and `item`, so any answer-level view can be shared directly.

## Rebuilding the data

The authored source and generated packs live in `src/europa_eval/resources/`.

```bash
# Recreate one pack through local Ollama
python3 scripts/generate_language_packs.py --only swe --overwrite

# Materialize the 432-item JSONL suite
python3 scripts/build_core_suite.py

# Validate and refresh the GitHub Pages bundle
europa validate
europa build-site --docs docs --results results/runs
```

Generated packs are committed so running the benchmark never requires the translation model.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the native-review workflow and result submission requirements.

## License and citation

Code is Apache-2.0. Original pilot items are CC0-1.0. External resources keep their own licenses and are linked rather than repackaged.

```bibtex
@software{moell2026europaeval,
  author  = {Birger Mo\"ell},
  title   = {EUROPA Eval: Transparent capability evaluation across 36 European languages},
  year    = {2026},
  url     = {https://github.com/BirgerMoell/europa-eval},
  version = {0.1.0}
}
```
