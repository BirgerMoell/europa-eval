# Continued-Training Recommendations for the Neonkraft OpenEuroLLM 9B Checkpoint

**Prepared:** 14 September 2026  
**Checkpoint:** `Neonkraft/oellm-9b-256k-theta64m-prelude-anneal300b-instruct-sft`  
**Evaluated revision:** `85bf18fb4f0bee6ac6270f06b1d1c6b3be200f31`

## Executive summary

The evaluation suggests that this checkpoint can improve substantially without changing its core architecture. The most effective next step is not another pass over generic English instruction data. The model already understands most of the evaluation prompts. Its largest weaknesses are:

1. exact response-format compliance and stopping;
2. quantitative and algorithmic reasoning;
3. multilingual safety and target-language adherence;
4. complete summarization under constraints;
5. typed structured output, literal copying and revision tracking; and
6. low-resource language generation, with Georgian requiring a tokenizer intervention as well as more data.

The recommended programme is a targeted multilingual SFT run followed by preference optimization. A deeper language-adaptive continuation from the pre-SFT parent is worth considering for Georgian and other poorly represented languages, but it should be treated as a separate track.

The public evaluations are available here:

- [Complete EUROPA Eval result](https://birgermoell.github.io/europa-eval/?run=neonkraft-oellm-9b-theta64m-instruct-sft-hf-85bf18fb4f0b-20260914-europa-v010#deep-dive)
- [Complete SVEA Eval result](https://birgermoell.github.io/svea-eval/?run=neonkraft-oellm-9b-theta64m-instruct-sft-hf-85bf18fb4f0b-20260914-v022#deep-dive)
- [Hugging Face model card](https://huggingface.co/Neonkraft/oellm-9b-256k-theta64m-prelude-anneal300b-instruct-sft)

## Evaluation context

The model completed both evaluations without generation or judging failures:

| Evaluation | Coverage | Overall score | Protocol |
|---|---:|---:|---|
| EUROPA Eval v0.1 | 432/432 items, 36 languages | 76.2% | BF16, reasoning off, temperature 0, seed 42 |
| SVEA Eval v0.2 | 55/55 Swedish items | 66.0% | BF16, reasoning off, temperature 0, seed 42 |

Open-generation items were judged by `gemma4:31b` Q4_K_M with reasoning disabled. Deterministic tasks used exact, schema, constraint or numeric scorers. Both benchmarks are public development suites, so their examples must not be reused for training.

The checkpoint is a full-parameter SFT of the 9B Prelude anneal checkpoint. According to its model card, it was trained for two epochs on all 2,152,112 conversations in `allenai/Dolci-Instruct-SFT`, approximately 2.8 billion training tokens. Most of that data is English. The checkpoint has not received preference tuning or reinforcement learning.

This history is consistent with the evaluation: the model is broadly capable but insufficiently aligned for exact multilingual task execution.

## Observed weaknesses

### 1. Exact output contracts and termination

This is the clearest low-cost opportunity.

Across EUROPA's 72 multiple-choice items, the model selected the semantically correct option 69 times, or 95.8%. It received full format credit on only 36 items because 33 correct answers contained additional text. Typical output was `B. At ten.` when the instruction required exactly `B`.

Correcting only those 33 overanswers, with no change in semantic ability, would mechanically add about 3.8 points to the current EUROPA score and raise it from 76.2% to approximately 80.0%.

There is also a stopping problem. Twenty-four EUROPA outputs reached their maximum token allowance. Their mean score was 37.1%, compared with 78.5% for responses that stopped normally. SVEA showed the same pattern on six items.

Recommended data:

- single-letter and single-number answers;
- verbatim-only outputs;
- exact line-count and word-count constraints;
- JSON without Markdown fences;
- fixed key order and exact value types;
- ISO dates and canonical time formats;
- outputs where `<|im_end|>` immediately follows the only permitted answer; and
- contrastive examples where the rejected answer is semantically correct but contains an explanation, prefix, suffix or code fence.

These examples contain very few supervised tokens. They must be oversampled or sequence-weighted so that long conversational examples do not dominate their contribution to the training loss.

### 2. Quantitative and algorithmic reasoning

Quantitative reasoning was the weakest EUROPA domain at 37.8%.

- Ordinary numeric reasoning: 58.3%, with 21/36 exact answers.
- Surface calculation: 17.3%, with 0/36 exact answers.
- The model often returned values near `1.0` for the number of letters divided by the number of words, even when the correct value was between approximately 5 and 9.
- SVEA exposed additional failures on percentages, unit conversion, calculation verification and LIX.
- The model also failed both Universal Dependencies head-index tasks in SVEA.

Recommended data:

- addition, subtraction, percentages and ratios expressed in natural language;
- word problems with numbers expressed both as digits and words;
- time, currency and unit conversion;
- Unicode-aware word, letter and sentence counting;
- LIX and related readability calculations;
- auditing an incorrect intermediate calculation;
- Universal Dependencies head and relation extraction; and
- typed JSON representations of calculated results.

Gold answers should be produced by deterministic programs rather than an LLM. Natural-language variants can be generated synthetically, but every numeric result and structured answer should pass an independent verifier before entering training.

For this non-reasoning checkpoint, a solver or teacher may produce a hidden rationale, but the supervised assistant response should contain only the format requested by the user. If a reasoning-enabled model is desired, it should be trained as a separate derivative with explicit reasoning traces and evaluated under a separate protocol.

### 3. Multilingual safety and language adherence

The EUROPA harmful-request score was 63.7%, masking several high-risk failures:

- Six languages generated the requested phishing content instead of refusing: Bulgarian, Irish, Romanian, Basque, Macedonian and Turkish.
- Ten languages received zero for language quality, usually because the model fell back to English: Danish, Croatian, Maltese, Polish, Slovenian, Spanish, Basque, Bosnian, Georgian and Norwegian.
- Eighteen responses either performed the harmful task or failed to offer a concrete safe alternative.
- Only Dutch, Slovak and Icelandic received perfect scores.

The model's strong Swedish grounding-and-safety score shows that this is not a universal inability to refuse. Safety behavior has not transferred consistently across languages.

Recommended safety data should cover all 36 languages and pair harmful requests with responses that:

1. clearly refuse the harmful operation;
2. remain in the language used by the user;
3. briefly explain the relevant risk; and
4. offer a concrete safe alternative.

Preference data should use the observed failures as rejected-response categories:

- direct harmful compliance;
- English fallback;
- an empty or generic refusal without an alternative;
- excessive policy language; and
- refusal of a harmless neighbouring request.

Benign near-neighbour examples are essential to measure and prevent over-refusal.

### 4. Summary completeness under constraints

EUROPA summarization scored 81.6%, but the error pattern was highly consistent:

- only 3/36 summaries retained every required fact;
- 33/36 omitted at least one required fact; and
- 5/36 broke the one-sentence constraint.

The model is usually fluent and faithful, but it optimizes for brevity by dropping information.

Recommended data:

- source passages generated from explicit fact slots;
- prompts naming the facts that must survive compression;
- one-sentence and maximum-word constraints;
- chosen summaries that preserve every required slot; and
- rejected summaries representing omission, copying, hallucination and excessive length.

Coverage should be validated by exact slot matching where possible rather than by an LLM judge alone.

### 5. Typed structured output, literal copying and revision tracking

The model is generally capable of producing JSON: it scored 97.2% on the basic structured-output capability. Failures become more common when a task combines JSON with state tracking or literal preservation.

Observed errors included:

- integers serialized as strings;
- a Swedish date rendered as natural language rather than ISO 8601;
- misspelled schema keys;
- proper names transliterated into the surrounding script instead of copied unchanged;
- selection of a document title instead of a project identifier; and
- selection of stale revision values in Georgian.

EUROPA's all-or-nothing revision-tracking score was 69.4%. In most failures, the model found the latest revision but violated a type or literal-copy requirement. Training should therefore combine state tracking with strict schema validation rather than treating these as separate tasks.

Recommended data:

- documents containing multiple superseded revisions;
- conflicting dates, owners, budgets and identifiers;
- explicit "latest approved revision controls" rules;
- cross-script names that must be copied byte-for-byte;
- nested tool arguments with declared types;
- invalid tool responses that require confirmation or recovery; and
- lengths ranging from short documents to 32K-token contexts.

Longer-context experiments should be scored separately. The current evaluations do not establish the checkpoint's advertised 256K-context capability.

### 6. Low-resource languages and Georgian tokenization

The lowest EUROPA language scores were:

| Language | Score |
|---|---:|
| Georgian | 20.0% |
| Basque | 58.4% |
| Bulgarian | 65.2% |
| Turkish | 65.5% |
| Maltese | 66.3% |
| Galician | 66.8% |

All six are absent from the current 12-language configuration set in `openeurollm/Dolci-Instruct-SFT-translated`. Existing translated resources are useful seeds, but they do not cover the full language set measured by EUROPA:

- [Dolci-Instruct-SFT-translated](https://huggingface.co/datasets/openeurollm/Dolci-Instruct-SFT-translated)
- [Dolci-Instruct-DPO-translated](https://huggingface.co/datasets/openeurollm/Dolci-Instruct-DPO-translated)

The translated instruction mixture should be extended to all 36 languages, with particular attention to native-language rather than translation-only data. Useful registers include public administration, work, safety, culture, technical instructions and everyday conversation.

Georgian requires special handling. A local tokenizer audit found that the evaluated tokenizer round-trips Georgian correctly, but the EUROPA Georgian prompts required approximately 2.31 tokens per character. English required approximately 0.25 tokens per character. Georgian is therefore around 9.4 times less efficient. Seven Georgian outputs contained Unicode replacement characters and exhausted their output allowance.

Additional Georgian data may improve generation, but it will not solve this efficiency problem. Two options should be investigated:

1. add Georgian subwords, initialize their embeddings from existing byte-token decompositions and perform language-adaptive continued training; or
2. train a revised tokenizer and continue from the pre-SFT parent as a new model line.

The second option is cleaner but more expensive and less checkpoint-compatible.

## Proposed first training experiment

A practical first experiment is a 300,000-example mixture:

| Data slice | Examples | Share |
|---|---:|---:|
| Exact contracts, termination and typed structured output | 75,000 | 25.0% |
| Verified arithmetic, counting, LIX, units and linguistic analysis | 65,000 | 21.7% |
| Multilingual safety and safe alternatives | 45,000 | 15.0% |
| Coverage-controlled summarization | 25,000 | 8.3% |
| Revision tracking, literal copying and tool use | 20,000 | 6.7% |
| Explicit language selection and translation fidelity | 10,000 | 3.3% |
| High-quality general replay data | 60,000 | 20.0% |
| **Total** | **300,000** | **100%** |

Every targeted slice should be multilingual. Within the targeted data:

- allocate roughly half approximately uniformly across the 36 languages;
- devote around 30% to the weakest languages and scripts; and
- retain around 20% in a natural or high-resource distribution.

The 60,000 replay examples should preserve general helpfulness and reduce catastrophic forgetting. They should be filtered for quality and should not simply recreate the original English-heavy mix.

### Suggested optimization stages

1. **Targeted SFT:** Start conservatively, for example near a `5e-6` peak learning rate, and compare several checkpoints rather than assuming the last step is best.
2. **Preference optimization:** Use approximately 50,000–100,000 multilingual chosen/rejected pairs for strict contracts, safety, language adherence and summary completeness.
3. **Optional language-adaptive continuation:** Return to the pre-SFT parent for a larger native-language continuation if Georgian and other foundational language weaknesses remain.

The public [OpenEuroLLM post-training repository](https://github.com/OpenEuroLLM/post-training) supports both SFT and DPO workflows and can be used to keep these experiments reproducible.

## Data-quality requirements

The training data should meet the following requirements:

- preserve source URLs, licenses, language and generation metadata;
- deduplicate within the training mixture and against existing post-training data;
- decontaminate against EUROPA, SVEA and any additional evaluation suites;
- validate exact-format, numeric and schema tasks deterministically;
- reject outputs containing Unicode replacement characters;
- run language identification and script-consistency checks;
- preserve named entities and literal identifiers unchanged when requested;
- obtain native-speaker review for stratified samples, especially in weak languages; and
- keep an untouched hidden test set with new entities, numbers and surface forms.

Synthetic tasks should reproduce capabilities, not benchmark wording. The public evaluation questions and reference answers must not become training examples.

## Evaluation issue to resolve before training

At least one apparent failure is caused by benchmark translation noise. In the Bulgarian arithmetic item, the translated context omits the equivalent of "seven leave." The visible prompt therefore describes 18 participants plus 4 arrivals, making the model's answer `22` reasonable, while the stored gold remains `15`.

This illustrates why raw per-language scores should not directly determine sampling weights. Before finalizing the training mixture:

1. native-review the weak-language evaluation packs;
2. correct translations whose visible information does not support the gold answer;
3. add semantic-choice and field-level diagnostics alongside strict exact-match scores; and
4. human-calibrate multilingual safety and open-generation judgments.

## Proposed success gates

The next checkpoint should be evaluated against fresh, uncontaminated variants. Suggested gates are:

| Capability | Current signal | Proposed gate |
|---|---:|---:|
| Multiple-choice semantic correctness | 95.8% | No regression |
| Multiple-choice exact-format success | 50.0% | At least 90% |
| Ordinary numeric reasoning | 58.3% | At least 85% |
| Surface calculation | 17.3% | At least 70% |
| Safe refusal | 6 direct harmful completions | Zero direct harmful completions |
| Safety language adherence | 10 wrong-language answers | Zero wrong-language answers |
| Complete summary coverage | 3/36 | At least 80% |
| Exact revision/schema result | 69.4% | At least 90% |
| Georgian valid output | Replacement characters in 7 items | No replacement characters |

Also require no material regression in capabilities that are already strong:

- grounded answering: 100%;
- calibrated abstention: 97.2%;
- basic instruction following: 97.2%; and
- basic structured output: 97.2%.

## Recommended order of work

1. Review and repair weak-language evaluation items.
2. Build deterministic generators and validators for strict-format and quantitative tasks.
3. Produce the 300K targeted multilingual SFT mixture.
4. Run a small SFT ablation with conservative learning rates and frequent checkpoints.
5. Evaluate every checkpoint on uncontaminated SVEA and EUROPA variants.
6. Construct preference pairs from recurring failure modes.
7. Run DPO and test both safety improvement and benign-request over-refusal.
8. Decide whether Georgian warrants tokenizer expansion or a new tokenizer/model line.

The highest expected return comes from strict-contract SFT first, multilingual safety preference training second, verified quantitative data third, and deeper language adaptation after those lower-cost interventions have been measured.
