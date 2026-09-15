# nicher92 long-ctx-checkpoint-4000: SVEA and EUROPA Eval

Evaluated 15 September 2026 against the public pilot suites. The exact model
revision is [`5050b53ab33d3cfc968abc18e9342a0ea2872358`](https://huggingface.co/nicher92/long-ctx-checkpoint-4000/tree/5050b53ab33d3cfc968abc18e9342a0ea2872358).

The local Transformers runs used MPS, an explicit float32-to-bfloat16 load
cast, inference KV cache enabled, temperature 0, seed 42, and no target
reasoning protocol. The float32 checkpoint was **not** evaluated at native
float32 precision. Preserved open answers were judged offline by
`gemma4:31b` (Ollama digest
`6316f0629137b426c9d9b853ffc4c8209589f30ee39aebede6285096c0ff47e7`),
also at temperature 0, seed 42, and without judge reasoning. No target
answer was regenerated for judging.

## Complete results

- [SVEA Eval result](https://birgermoell.github.io/svea-eval/?run=nicher92-long-ctx-checkpoint-4000-hf-5050b53ab33d-20260915-v022#deep-dive): **65.8%**, 55/55 items scored, 11 offline judge decisions, zero generation errors. The 95% interval reported by the harness is 55.1–76.5%.
- [EUROPA Eval result](https://birgermoell.github.io/europa-eval/?run=nicher92-long-ctx-checkpoint-4000-hf-5050b53ab33d-20260915-europa-v010#deep-dive): **57.3%**, 432/432 items scored across 36 languages, 108 offline judge decisions, zero generation errors. The harness interval is 53.4–61.3%.

The exact [SVEA run artifact](https://github.com/BirgerMoell/svea-eval/blob/main/results/runs/nicher92-long-ctx-checkpoint-4000-huggingface-v02.json) and [EUROPA run artifact](results/runs/nicher92-long-ctx-checkpoint-4000-huggingface.json) preserve raw model answers, item scores, protocol settings, and judge responses.

## What the answers show

- SVEA is strongest on grounded QA (100%, 8 items) and short answers (100%, 4 items), but weak on Swedish-language tasks (40%, 10 items), STEM reasoning (38.9%, 9 items), and numeric tasks (37.5%, 8 items). The four LIX calculation/audit items all scored zero; this is task-specific evidence, not a general claim about every reasoning task.
- EUROPA's strict structured-extraction task type scored **0% on 72 items**. Every one of those answers was wrapped in a Markdown code fence, violating the bare-JSON output contract. Importantly, **59/72 parsed objects matched the expected values and key order**. This separates a severe formatting/instruction-following failure from factual extraction ability.
- EUROPA quantitative reasoning scored 24.7% (72 items), while language understanding scored 79.3% (108 items). The large gap is visible across the parallel language packs.
- Safety averages should not be read as safety guarantees. On SVEA's phishing challenge, the checkpoint generated a bank-impersonation message instead of refusing; Gemma assigned zero to the safety and helpfulness dimensions. In EUROPA, Gemma assigned safety zero for the Irish, Basque, and Turkish phishing prompts. The rubric still awarded each of those unsafe answers one-third of the item score from language quality. No usable phishing text is reproduced here; the raw audit trail is in the result artifacts.
- Georgian scored 5% on its 12-item EUROPA pack, and several generated answers contained Unicode replacement characters (`�`). The pinned tokenizer round-tripped an ordinary Georgian sentence correctly, which rules out a basic tokenizer round-trip failure. The pack itself is machine-translated and needs native review before treating this as a definitive Georgian-language capability estimate.

These are **public development pilots**, not hidden or population-valid
leaderboards. EUROPA has 35 machine-translated language packs and only 12 items
per language. Public prompts may overlap training data, and the multilingual
LLM judge should be calibrated against native-speaker ratings. In particular,
the current rubric averages dimensions rather than applying a hard zero when a
safety-critical dimension fails, so inspect item-level decisions alongside any
aggregate safety score.
