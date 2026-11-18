# EUROPA Eval technical report

`europa-eval.tex` is the report; `analysis.py` regenerates every number, table and figure from the committed run artifacts in `results/runs/` (and, for the cross-benchmark section, the EUROPA Alignment runs if `../europa-alignment` is checked out next to this repository).

```bash
PYTHONPATH=src uv run --no-project --python 3.12 --with numpy --with matplotlib python paper/analysis.py
cd paper && tectonic -X compile europa-eval.tex
cp europa-eval.pdf ../docs/paper/europa-eval.pdf
```

Outputs: `generated/` (LaTeX macros and tables) and `figures/` (PDF figures). References are in `references.bib`.
