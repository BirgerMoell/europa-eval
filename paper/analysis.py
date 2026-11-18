#!/usr/bin/env python3
"""Reproduce every number, table and figure in the EUROPA Eval paper.

Reads only the committed run artifacts in ``results/runs/``, the bundled suite
and (for the cross-benchmark section) the EUROPA Alignment run artifacts if a
sibling checkout exists. Writes LaTeX macros/tables to ``paper/generated/`` and
figures to ``paper/figures/``. Dependencies: numpy and matplotlib, plus the
dependency-free ``europa_eval`` package from this repository (for the scorer).

    PYTHONPATH=src python3 paper/analysis.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from europa_eval import scoring  # noqa: E402
from europa_eval.data import load_suite  # noqa: E402

RUNS = ROOT / "results" / "runs"
OUT = ROOT / "paper" / "generated"
FIG = ROOT / "paper" / "figures"
ALIGN_RUNS = ROOT.parent / "europa-alignment" / "results" / "runs"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20261118)
B = 10_000

# key, file, label, group. OELLM runs share one 9B base and tokenizer.
RUN_SPECS = [
    ("oesft", "oellm-9b-256k-sft-huggingface.json", "OELLM SFT (T\\\"ulu/EuroBlocks)", "oellm"),
    ("nicher", "nicher92-long-ctx-checkpoint-4000-huggingface.json", "Third-party ckpt-4000", "oellm"),
    ("stage1", "birgermoell-oellm-9b-256k-stage1-instruct-v1-huggingface.json", "Stage-1 SFT$^\\dagger$", "oellm"),
    ("dolci", "neonkraft-oellm-9b-theta64m-instruct-sft-huggingface.json", "Dolci SFT", "oellm"),
    ("dpo", "oellm-9b-threeway-dpo-full-v1-huggingface.json", "Dolci SFT + DPO", "oellm"),
    ("apertus", "apertus-8b-instruct-2509-huggingface.json", "Apertus-8B-Instruct", "ref"),
    ("ge2b", "gemma4-e2b-ollama.json", "Gemma 4 E2B", "ref"),
    ("g31", "gemma4-31b-ollama.json", "Gemma 4 31B$^\\ddagger$", "ref"),
    ("qwen", "qwen3-6-35b-a3b-ollama.json", "Qwen3.6-35B-A3B", "ref"),
]
PLAIN = {
    "oesft": "OELLM SFT (Tülu/EuroBlocks)", "nicher": "Third-party ckpt-4000",
    "stage1": "Stage-1 SFT†", "dolci": "Dolci SFT", "dpo": "Dolci SFT + DPO",
    "apertus": "Apertus-8B", "ge2b": "Gemma 4 E2B", "g31": "Gemma 4 31B‡",
    "qwen": "Qwen3.6-35B-A3B",
}
KEYS = [k for k, *_ in RUN_SPECS]
LABEL = {k: l for k, _, l, _ in RUN_SPECS}
GROUP = {k: g for k, _, _, g in RUN_SPECS}
MACRO_NAME = {"oesft": "Oesft", "nicher": "Nicher", "stage1": "Stageone", "dolci": "Dolci",
              "dpo": "Dpo", "apertus": "Apertus", "ge2b": "Gemmasmall", "g31": "Gemmalarge",
              "qwen": "Qwen"}
DPO_LANGS = {"ces", "deu", "ell", "eng", "spa", "fin", "fra", "ita", "pol", "ron", "swe", "ukr"}
TEMPLATES = [
    ("reading", "Reading comprehension"), ("numeric", "Arithmetic"),
    ("ground-supported", "Grounded answer"), ("ground-insufficient", "Calibrated abstention"),
    ("structured", "Structured JSON"), ("strict-format", "Exact instruction"),
    ("tool-recovery", "Tool recovery"), ("surface-metric", "Surface calculation"),
    ("summarization", "Summarization"), ("translation", "EN$\\to$X translation"),
    ("safety", "Harmful-request refusal"), ("revision-tracking", "Revision tracking"),
]
TPL = [t for t, _ in TEMPLATES]
TPL_LABEL = dict(TEMPLATES)
DOMAINS = [
    ("language_understanding", "Language understanding"),
    ("quantitative_reasoning", "Quantitative reasoning"),
    ("grounding_safety", "Grounding \\& safety"),
    ("digital_agency", "Digital agency"),
    ("practical_communication", "Practical communication"),
]

meta, suite_items = load_suite(ROOT / "src/europa_eval/resources/suites/europa-core-v0.1")
items = {it.id: it for it in suite_items}
ids = [it.id for it in suite_items]
LANGS = sorted({it.language for it in suite_items})
lang_reg = json.loads((ROOT / "src/europa_eval/resources/languages.json").read_text())["languages"]
LNAME = {e["code"]: e["name"] for e in lang_reg}
LGROUP = {e["code"]: e["group"] for e in lang_reg}
tpl_of = {i: items[i].template_id for i in ids}
lang_of = {i: items[i].language for i in ids}
L_IDX = {l: [n for n, i in enumerate(ids) if lang_of[i] == l] for l in LANGS}
T_IDX = {t: [n for n, i in enumerate(ids) if tpl_of[i] == t] for t in TPL}

runs, by = {}, {}
for k, f, *_ in RUN_SPECS:
    d = json.loads((RUNS / f).read_text())
    runs[k] = d
    by[k] = {s["item_id"]: s for s in d["samples"]}


def S(k, field="score"):
    """Item vector in suite order; NaN where the run has no score."""
    out = []
    for i in ids:
        s = by[k][i]
        v = s.get(field)
        if field == "passed":
            out.append(np.nan if s.get("score") is None else (1.0 if v else 0.0))
        else:
            out.append(np.nan if v is None else float(v))
    return np.array(out)


SC = {k: S(k) for k in KEYS}
PS = {k: S(k, "passed") for k in KEYS}


def cluster_boot(v):
    """Mean and 95% CI, resampling the 36 languages (clusters of 12 items)."""
    arr = np.stack([v[L_IDX[l]] for l in LANGS])
    lm = np.nanmean(arr, axis=1)
    idx = RNG.integers(0, len(LANGS), size=(B, len(LANGS)))
    m = np.nanmean(arr[idx], axis=(1, 2))
    return float(np.nanmean(arr)), float(np.quantile(m, .025)), float(np.quantile(m, .975)), lm


def paired(a, b, subset_langs=None):
    langs = subset_langs or LANGS
    diff = np.stack([(a - b)[L_IDX[l]] for l in langs])
    idx = RNG.integers(0, len(langs), size=(B, len(langs)))
    m = np.nanmean(diff[idx], axis=(1, 2))
    return float(np.nanmean(diff)), float(np.quantile(m, .025)), float(np.quantile(m, .975))


macros: dict[str, str] = {}


def mac(name, value, fmt="{:.3f}"):
    s = fmt.format(value) if not isinstance(value, str) else value
    if s.startswith("-"):
        s = "\\textminus " + s[1:]
    macros[name] = s


def pct(x, d=1):
    return f"{100 * x:.{d}f}"


def tex(s):
    return s.replace("_", "\\_").replace("&", "\\&").replace("%", "\\%")


# ---------------------------------------------------------------- suite facts
mac("nItems", len(ids), "{}")
mac("nLangs", len(LANGS), "{}")
mac("nTemplates", len(TPL), "{}")
mac("nRuns", len(KEYS), "{}")
n_judged_tpl = sum(1 for t in TPL if items[ids[T_IDX[t][0]]].scoring["type"] == "rubric")
mac("nJudgedTemplates", n_judged_tpl, "{}")
mac("nDetTemplates", len(TPL) - n_judged_tpl, "{}")
mac("nJudgedItems", n_judged_tpl * len(LANGS), "{}")
mac("nDetItems", (len(TPL) - n_judged_tpl) * len(LANGS), "{}")
mac("judgeId", runs["dpo"]["judge"]["id"], "{}")
mac("judgeRev", runs["dpo"]["judge"]["revision"].replace("sha256:", "")[:12], "{}")
assert all(runs[k]["judge"]["revision"] == runs["dpo"]["judge"]["revision"] for k in KEYS)
mac("transModel", items[ids[0]].metadata.get("translation_generator", ""), "{}")
mac("stageoneMissing", int(np.isnan(SC["stage1"]).sum()), "{}")

# ---------------------------------------------------------------- main table
summary = {}
for k in KEYS:
    mean, lo, hi, lm = cluster_boot(SC[k])
    pr = float(np.nanmean(PS[k]))
    worst = LANGS[int(np.argmin(lm))]
    smp = runs[k]["samples"]
    trunc = sum(1 for s in smp if s.get("finish_reason") == "length")
    mal = sum(1 for s in smp if (s.get("score_details") or {}).get("malformed"))
    summary[k] = dict(mean=mean, lo=lo, hi=hi, pass_rate=pr, lm=lm, worst=worst,
                      worst_score=float(lm.min()), best_score=float(lm.max()),
                      trunc=trunc, mal=mal, n=int((~np.isnan(SC[k])).sum()))
    M = MACRO_NAME[k]
    mac(f"score{M}", mean)
    mac(f"scoreLo{M}", lo)
    mac(f"scoreHi{M}", hi)
    mac(f"pct{M}", pct(mean))
    mac(f"pass{M}", pct(pr))
    mac(f"worst{M}", LNAME[worst], "{}")
    mac(f"worstScore{M}", lm.min())
    mac(f"trunc{M}", trunc, "{}")
    mac(f"malformed{M}", mal, "{}")

dom_scores = {k: {d: float(np.nanmean([SC[k][n] for n, i in enumerate(ids) if items[i].domain == d]))
                  for d, _ in DOMAINS} for k in KEYS}
tpl_scores = {k: {t: float(np.nanmean(SC[k][T_IDX[t]])) for t in TPL} for k in KEYS}

rows = []
for k in KEYS:
    s = summary[k]
    rows.append(
        f"{LABEL[k]} & {s['n']} & {s['mean']:.3f} & [{s['lo']:.3f}, {s['hi']:.3f}] & {pct(s['pass_rate'])} & "
        + " & ".join(f"{dom_scores[k][d]:.2f}" for d, _ in DOMAINS)
        + f" & {LNAME[s['worst']]} ({s['worst_score']:.2f}) & {s['mal']} & {s['trunc']} \\\\"
    )
    if k == "dpo":
        rows.append("\\midrule")
hdr = ("Model & $n$ & Score & 95\\% CI & Pass\\% & "
       + " & ".join(f"\\rotatebox{{90}}{{{l}}}" for _, l in DOMAINS)
       + " & Weakest language & Malf. & Trunc. \\\\")
(OUT / "table_main.tex").write_text(
    "\\begin{tabular}{lrrcr" + "r" * len(DOMAINS) + "lrr}\n\\toprule\n" + hdr + "\n\\midrule\n"
    + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- provenance
prov = []
for k in KEYS:
    d = runs[k]
    m = d["model"]
    rid = m["id"].replace("_", "\\_")
    dur = None
    try:
        from datetime import datetime
        t0 = datetime.fromisoformat(d["started_at"]); t1 = datetime.fromisoformat(d["finished_at"])
        dur = (t1 - t0).total_seconds() / 60
    except Exception:
        pass
    dtype = d["protocol"]["backend_settings"].get("torch_dtype") or (d.get("environment", {}).get("target_model", {}) or {}).get("quantization", "")
    prov.append(f"{LABEL[k]} & \\texttt{{{rid}}} & \\texttt{{{m['revision'].replace('sha256:', '')[:10]}}} & {m['backend']} & {tex(dtype) if dtype else '--'} & {d['started_at'][:10]} \\\\")
(OUT / "table_provenance.tex").write_text(
    "\\begin{tabular}{lllllr}\n\\toprule\nRun & Model ID & Revision & Backend & Precision & Date \\\\\n\\midrule\n"
    + "\n".join(prov) + "\n\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- template heatmap
fig, ax = plt.subplots(figsize=(7.2, 3.6))
mat = np.array([[tpl_scores[k][t] for t in TPL] for k in KEYS])
im = ax.imshow(mat, cmap="viridis", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(TPL)))
ax.set_xticklabels([TPL_LABEL[t].replace("$\\to$", "→") for t in TPL], rotation=40, ha="right", fontsize=7.5)
ax.set_yticks(range(len(KEYS)))
ax.set_yticklabels([PLAIN[k] for k in KEYS], fontsize=7.5)
for r in range(mat.shape[0]):
    for c in range(mat.shape[1]):
        ax.text(c, r, f"{mat[r, c]:.2f}", ha="center", va="center", fontsize=6,
                color="white" if mat[r, c] < 0.6 else "black")
ax.axhline(4.5, color="white", lw=1.5)
fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
fig.tight_layout()
fig.savefig(FIG / "template_heatmap.pdf")
plt.close(fig)

# ---------------------------------------------------------------- content-only rescoring
def lenient_item(it):
    sc = dict(it.scoring)
    if sc["type"] == "choice":
        sc["format"] = None
    elif sc["type"] == "numeric":
        sc["format"] = None
    elif sc["type"] == "exact":
        sc["format"] = None
    elif sc["type"] == "json_exact":
        sc.pop("forbid_code_fence", None)
        sc.pop("forbid_surrounding_text", None)
        sc.pop("required_key_order", None)
    return replace(it, scoring=sc)


LEN_ITEMS = {i: lenient_item(items[i]) for i in ids}


def lenient_score(k, i):
    s = by[k][i]
    it = items[i]
    if s.get("score") is None:
        return np.nan
    if it.scoring["type"] == "rubric":
        return float(s["score"])
    resp = s.get("response") or ""
    li = LEN_ITEMS[i]
    if li.scoring["type"] == "choice":
        # content-only: first letter at the start, else first standalone letter
        m = scoring._LEADING_CHOICE.match(resp.strip())
        parsed = m.group(1).upper() if m else None
        if parsed is None:
            sc = scoring._score_choice(li, resp)
            parsed = sc.parsed
        return 1.0 if parsed == str(it.gold["answer"]).upper() else 0.0
    if li.scoring["type"] == "json_exact":
        try:
            parsed = scoring._parse_json(resp)
        except (ValueError, json.JSONDecodeError):
            return 0.0
        cands = [it.gold["value"], *it.gold.get("accepted_values", [])]
        return 1.0 if any(parsed == c for c in cands) else 0.0
    try:
        return float(scoring.score_item(li, resp).value)
    except Exception:
        return 0.0


LEN = {k: np.array([lenient_score(k, i) for i in ids]) for k in KEYS}
det_idx = [n for n, i in enumerate(ids) if items[i].scoring["type"] != "rubric"]
fmt_rows = []
strict_rank = sorted(KEYS, key=lambda k: -summary[k]["mean"])
len_mean = {k: float(np.nanmean(LEN[k])) for k in KEYS}
len_rank = sorted(KEYS, key=lambda k: -len_mean[k])
for k in KEYS:
    st_det = float(np.nanmean(SC[k][det_idx]))
    le_det = float(np.nanmean(LEN[k][det_idx]))
    tax = len_mean[k] - summary[k]["mean"]
    fmt_rows.append(
        f"{LABEL[k]} & {st_det:.3f} & {le_det:.3f} & {summary[k]['mean']:.3f} & {len_mean[k]:.3f} & {tax:+.3f} & "
        f"{strict_rank.index(k) + 1} & {len_rank.index(k) + 1} \\\\".replace("+", "+").replace("-0.", "\\textminus 0.")
    )
    if k == "dpo":
        fmt_rows.append("\\midrule")
    M = MACRO_NAME[k]
    mac(f"lenient{M}", len_mean[k])
    mac(f"formatTax{M}", tax)
    mac(f"detStrict{M}", st_det)
    mac(f"detLenient{M}", le_det)
(OUT / "table_format.tex").write_text(
    "\\begin{tabular}{lrrrrrrr}\n\\toprule\n & \\multicolumn{2}{c}{Deterministic items} & \\multicolumn{2}{c}{All items} & & \\multicolumn{2}{c}{Rank} \\\\\n"
    "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){7-8}\nModel & Strict & Content & Strict & Content & Format gap & Strict & Content \\\\\n\\midrule\n"
    + "\n".join(fmt_rows) + "\n\\bottomrule\n\\end{tabular}\n")


def kendall_tau(order_a, order_b):
    pos_b = {k: n for n, k in enumerate(order_b)}
    conc = disc = 0
    for x in range(len(order_a)):
        for y in range(x + 1, len(order_a)):
            if pos_b[order_a[x]] < pos_b[order_a[y]]:
                conc += 1
            else:
                disc += 1
    return (conc - disc) / (conc + disc)


mac("tauStrictContent", kendall_tau(strict_rank, len_rank), "{:.2f}")
mac("maxFormatGap", max(len_mean[k] - summary[k]["mean"] for k in KEYS))
mac("maxFormatGapModel", PLAIN[max(KEYS, key=lambda k: len_mean[k] - summary[k]["mean"])].rstrip("†‡"), "{}")

# JSON items: fenced but correct content, per model
for k in KEYS:
    M = MACRO_NAME[k]
    js = [i for i in ids if items[i].scoring["type"] == "json_exact"]
    fenced = sum(1 for i in js if "```" in (by[k][i].get("response") or ""))
    fenced_ok = sum(1 for i in js if "```" in (by[k][i].get("response") or "") and lenient_score(k, i) == 1.0)
    mac(f"jsonFenced{M}", fenced, "{}")
    mac(f"jsonFencedCorrect{M}", fenced_ok, "{}")
    ch = [i for i in ids if items[i].scoring["type"] == "choice"]
    sem = sum(lenient_score(k, i) for i in ch)
    strict_ok = sum(1 for i in ch if by[k][i].get("passed"))
    mac(f"choiceSemantic{M}", int(sem), "{}")
    mac(f"choiceStrict{M}", strict_ok, "{}")
mac("nJson", sum(1 for i in ids if items[i].scoring["type"] == "json_exact"), "{}")
mac("nChoice", sum(1 for i in ids if items[i].scoring["type"] == "choice"), "{}")
# Gemma revision-tracking: script transliteration of the name inside fenced JSON
g_rev = [i for i in T_IDX["revision-tracking"]]
g_rev_ok = sum(1 for n in g_rev if LEN["g31"][n] == 1.0)
mac("gemmaRevContentOk", g_rev_ok, "{}")

# ---------------------------------------------------------------- truncation
for k in ["dolci", "oesft", "stage1", "dpo"]:
    smp = by[k]
    tr = [SC[k][n] for n, i in enumerate(ids) if smp[i].get("finish_reason") == "length" and not np.isnan(SC[k][n])]
    ok = [SC[k][n] for n, i in enumerate(ids) if smp[i].get("finish_reason") == "stop" and not np.isnan(SC[k][n])]
    M = MACRO_NAME[k]
    mac(f"truncScore{M}", float(np.mean(tr)) if tr else 0.0)
    mac(f"stopScore{M}", float(np.mean(ok)))

# ---------------------------------------------------------------- OELLM trajectory: paired diffs
pairs = [("dpo", "dolci"), ("dolci", "oesft"), ("dolci", "nicher"), ("dolci", "stage1"), ("qwen", "dpo")]
for a, b in pairs:
    m, lo, hi = paired(SC[a], SC[b])
    nm = f"d{MACRO_NAME[a]}{MACRO_NAME[b]}"
    mac(nm, m, "{:+.3f}")
    mac(nm + "Lo", lo, "{:+.3f}")
    mac(nm + "Hi", hi, "{:+.3f}")
# DPO content-only diff (is DPO gain mostly format?)
m, lo, hi = paired(LEN["dpo"], LEN["dolci"])
mac("dDpoDolciContent", m, "{:+.3f}")
mac("dDpoDolciContentLo", lo, "{:+.3f}")
mac("dDpoDolciContentHi", hi, "{:+.3f}")

# per-template DPO gains
dpo_tpl_rows = []
for t in TPL:
    a = tpl_scores["dolci"][t]
    b = tpl_scores["dpo"][t]
    la = float(np.nanmean(LEN["dolci"][T_IDX[t]]))
    lb = float(np.nanmean(LEN["dpo"][T_IDX[t]]))
    dpo_tpl_rows.append(f"{TPL_LABEL[t]} & {a:.2f} & {b:.2f} & {b - a:+.2f} & {la:.2f} & {lb:.2f} & {lb - la:+.2f} \\\\")
(OUT / "table_dpo_templates.tex").write_text(
    ("\\begin{tabular}{lrrrrrr}\n\\toprule\n & \\multicolumn{3}{c}{Strict} & \\multicolumn{3}{c}{Content only} \\\\\n"
     "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\nTemplate & SFT & DPO & $\\Delta$ & SFT & DPO & $\\Delta$ \\\\\n\\midrule\n"
     + "\n".join(dpo_tpl_rows) + "\n\\bottomrule\n\\end{tabular}\n").replace("+0.00", "0.00").replace("-0.", "\\textminus 0.").replace("+", "+"))
mac("dpoReadingGain", tpl_scores["dpo"]["reading"] - tpl_scores["dolci"]["reading"], "{:+.2f}")
mac("dpoReadingContentGain", float(np.nanmean(LEN["dpo"][T_IDX["reading"]]) - np.nanmean(LEN["dolci"][T_IDX["reading"]])), "{:+.2f}")
mac("dpoSafetyGain", tpl_scores["dpo"]["safety"] - tpl_scores["dolci"]["safety"], "{:+.2f}")
mac("dpoSurfaceGain", tpl_scores["dpo"]["surface-metric"] - tpl_scores["dolci"]["surface-metric"], "{:+.2f}")
mac("dpoMalformedDrop", f"{summary['dolci']['mal']}$\\to${summary['dpo']['mal']}", "{}")

# DPO language transfer
in_l = [l for l in LANGS if l in DPO_LANGS]
out_l = [l for l in LANGS if l not in DPO_LANGS and l != "kat"]
dl = {l: float(np.nanmean((SC["dpo"] - SC["dolci"])[L_IDX[l]])) for l in LANGS}
gin = float(np.mean([dl[l] for l in in_l]))
gout = float(np.mean([dl[l] for l in out_l]))
mac("dpoGainIn", gin, "{:+.3f}")
mac("dpoGainOut", gout, "{:+.3f}")
mac("nDpoLangsEval", len(in_l), "{}")
mac("nNonDpoLangs", len(out_l), "{}")
allv = np.array([dl[l] for l in in_l + out_l])
obs = gin - gout
cnt = 0
perm_n = 20000
for _ in range(perm_n):
    p = RNG.permutation(allv)
    if abs(p[:len(in_l)].mean() - p[len(in_l):].mean()) >= abs(obs) - 1e-12:
        cnt += 1
mac("dpoTransferP", (cnt + 1) / (perm_n + 1), "{:.2f}")
mac("nOutImproved", sum(1 for l in out_l if dl[l] > 0), "{}")
mac("nOutDeclined", sum(1 for l in out_l if dl[l] < 0), "{}")
mac("nInImproved", sum(1 for l in in_l if dl[l] > 0), "{}")
mac("dpoGainKat", dl["kat"], "{:+.3f}")

fig, ax = plt.subplots(figsize=(7.2, 2.6))
order = sorted(LANGS, key=lambda l: -dl[l])
cols = ["#1f4e9c" if l in DPO_LANGS else ("#bbbbbb" if l == "kat" else "#e08a2c") for l in order]
ax.bar(range(len(order)), [dl[l] for l in order], color=cols)
ax.axhline(0, color="black", lw=0.6)
ax.set_xticks(range(len(order)))
ax.set_xticklabels(order, rotation=90, fontsize=6.5)
ax.set_ylabel("DPO − SFT (mean item score)", fontsize=7.5)
ax.tick_params(axis="y", labelsize=7)
from matplotlib.patches import Patch  # noqa: E402
ax.legend(handles=[Patch(color="#1f4e9c", label="in DPO data"), Patch(color="#e08a2c", label="not in DPO data"),
                   Patch(color="#bbbbbb", label="Georgian")], fontsize=6.5, frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig(FIG / "dpo_transfer.pdf")
plt.close(fig)

# ---------------------------------------------------------------- languages
lang_mat = np.array([[np.nanmean(SC[k][L_IDX[l]]) for l in LANGS] for k in KEYS])
oellm_keys = [k for k in KEYS if GROUP[k] == "oellm"]
ref_keys = [k for k in KEYS if GROUP[k] == "ref"]
order = sorted(LANGS, key=lambda l: -np.mean([np.nanmean(SC[k][L_IDX[l]]) for k in KEYS]))
fig, ax = plt.subplots(figsize=(7.2, 3.2))
mat = np.array([[np.nanmean(SC[k][L_IDX[l]]) for l in order] for k in KEYS])
im = ax.imshow(mat, cmap="viridis", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(order)))
ax.set_xticklabels(order, rotation=90, fontsize=6.5)
ax.set_yticks(range(len(KEYS)))
ax.set_yticklabels([PLAIN[k] for k in KEYS], fontsize=7)
ax.axhline(4.5, color="white", lw=1.5)
fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
fig.tight_layout()
fig.savefig(FIG / "language_heatmap.pdf")
plt.close(fig)

# tokenizer fertility from recorded input tokens (OELLM tokenizer, DPO run)
def fert(k):
    eng = {tpl_of[i]: by[k][i]["input_tokens"] for i in ids if lang_of[i] == "eng"}
    out = {}
    for l in LANGS:
        r = [by[k][i]["input_tokens"] / eng[tpl_of[i]] for i in ids if lang_of[i] == l
             and by[k][i].get("input_tokens") and eng.get(tpl_of[i])]
        out[l] = float(np.median(r))
    return out


fert_oellm = fert("dpo")
fert_qwen = fert("qwen")
mac("fertKatOellm", fert_oellm["kat"], "{:.2f}")
mac("fertKatQwen", fert_qwen["kat"], "{:.2f}")
mac("fertMedianOellm", float(np.median([v for l, v in fert_oellm.items() if l != "eng"])), "{:.2f}")
oellm_lang_mean = {l: float(np.mean([np.nanmean(SC[k][L_IDX[l]]) for k in ["dolci", "dpo"]])) for l in LANGS}
x = np.array([fert_oellm[l] for l in LANGS])
y = np.array([oellm_lang_mean[l] for l in LANGS])
mac("fertCorrAll", float(np.corrcoef(x, y)[0, 1]), "{:+.2f}")
mask = np.array([l != "kat" for l in LANGS])
mac("fertCorrNoKat", float(np.corrcoef(x[mask], y[mask])[0, 1]), "{:+.2f}")
for k in KEYS:
    mac(f"kat{MACRO_NAME[k]}", float(np.nanmean(SC[k][L_IDX["kat"]])))
kat_oellm_max = max(float(np.nanmean(SC[k][L_IDX["kat"]])) for k in oellm_keys)
mac("katOellmMax", kat_oellm_max)
kat_trunc = sum(1 for k in oellm_keys for i in ids if lang_of[i] == "kat" and by[k][i].get("finish_reason") == "length")
kat_n = sum(1 for k in oellm_keys for i in ids if lang_of[i] == "kat")
mac("katTruncPct", pct(kat_trunc / kat_n, 0), "{}")
kat_fffd = sum(1 for k in oellm_keys for i in ids if lang_of[i] == "kat" and "\ufffd" in (by[k][i].get("response") or ""))
mac("katReplPct", pct(kat_fffd / kat_n, 0), "{}")
other_fffd = sum(1 for k in oellm_keys for i in ids if lang_of[i] != "kat" and "\ufffd" in (by[k][i].get("response") or ""))
mac("otherReplCount", other_fffd, "{}")
# rank of Georgian among languages for each group
mac("katRefMean", float(np.mean([np.nanmean(SC[k][L_IDX["kat"]]) for k in ref_keys])))

fig, ax = plt.subplots(figsize=(3.4, 2.6))
ax.scatter(x, y, s=12, color="#1f4e9c")
for l in LANGS:
    if l in {"kat", "eng", "mlt", "gle", "ell", "isl", "eus", "mkd"}:
        ax.annotate(l, (fert_oellm[l], oellm_lang_mean[l]), fontsize=6.5, xytext=(3, 2), textcoords="offset points")
ax.set_xlabel("Prompt tokens relative to English (OELLM tokenizer)", fontsize=7)
ax.set_ylabel("Mean score (Dolci SFT, DPO)", fontsize=7)
ax.tick_params(labelsize=7)
fig.tight_layout()
fig.savefig(FIG / "fertility.pdf")
plt.close(fig)

# EU-official vs other language groups
grp_rows = []
for g in sorted(set(LGROUP[l] for l in LANGS)):
    ls = [l for l in LANGS if LGROUP[l] == g]
    grp_rows.append((g, len(ls), {k: float(np.mean([np.nanmean(SC[k][L_IDX[l]]) for l in ls])) for k in KEYS}))
for g, n, v in grp_rows:
    gm = "".join(ch for ch in g.title() if ch.isalpha())
    mac(f"nLang{gm}", n, "{}")
    for k in ["dpo", "qwen", "dolci"]:
        mac(f"grp{gm}{MACRO_NAME[k]}", v[k])

# ---------------------------------------------------------------- ranking stability vs #languages
complete_keys = [k for k in KEYS if k != "stage1"]
full_rank = sorted(complete_keys, key=lambda k: -np.nanmean(SC[k]))
lang_scores = {k: np.array([np.nanmean(SC[k][L_IDX[l]]) for l in LANGS]) for k in complete_keys}
stab = {}
for nl in [1, 2, 3, 6, 9, 12, 18, 24, 36]:
    taus = []
    exact = 0
    for _ in range(2000):
        sel = RNG.choice(len(LANGS), size=nl, replace=False) if nl < len(LANGS) else np.arange(len(LANGS))
        if nl == len(LANGS):
            sel = RNG.choice(len(LANGS), size=nl, replace=True)
        r = sorted(complete_keys, key=lambda k: -lang_scores[k][sel].mean())
        taus.append(kendall_tau(full_rank, r))
        exact += r == full_rank
    stab[nl] = (float(np.mean(taus)), float(np.quantile(taus, .05)), exact / 2000)
mac("tauOneLang", stab[1][0], "{:.2f}")
mac("tauSixLang", stab[6][0], "{:.2f}")
mac("tauTwelveLang", stab[12][0], "{:.2f}")
mac("exactOneLang", pct(stab[1][2], 0), "{}")
mac("exactTwelveLang", pct(stab[12][2], 0), "{}")
mac("exactAllLang", pct(stab[36][2], 0), "{}")
# English-only ranking vs full
eng_rank = sorted(complete_keys, key=lambda k: -lang_scores[k][LANGS.index("eng")])
mac("tauEnglishOnly", kendall_tau(full_rank, eng_rank), "{:.2f}")
mac("nRankedModels", len(complete_keys), "{}")
fig, ax = plt.subplots(figsize=(3.4, 2.4))
xs = sorted(stab)
ax.plot(xs, [stab[n][0] for n in xs], marker="o", ms=3, color="#1f4e9c", label="mean Kendall τ")
ax.fill_between(xs, [stab[n][1] for n in xs], [1] * len(xs), alpha=0.15, color="#1f4e9c")
ax.plot(xs, [stab[n][2] for n in xs], marker="s", ms=3, color="#e08a2c", label="P(identical ranking)")
ax.set_xlabel("Languages sampled", fontsize=7)
ax.set_ylim(0, 1.02)
ax.tick_params(labelsize=7)
ax.legend(fontsize=6.5, frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig(FIG / "rank_stability.pdf")
plt.close(fig)

# ---------------------------------------------------------------- item saturation / discrimination
ip = np.array([[PS[k][n] for k in complete_keys] for n in range(len(ids))])
mac("satAllPass", int(np.sum(np.all(ip == 1, axis=1))), "{}")
mac("satAllFail", int(np.sum(np.all(ip == 0, axis=1))), "{}")
mac("satAllPassPct", pct(float(np.mean(np.all(ip == 1, axis=1)))), "{}")
tpl_sat = {t: float(np.mean(np.all(ip[T_IDX[t]] == 1, axis=1))) for t in TPL}
mac("satStrictFormat", pct(tpl_sat["strict-format"], 0), "{}")
mac("satAbstain", pct(tpl_sat["ground-insufficient"], 0), "{}")

# ---------------------------------------------------------------- abstention contrast (supported/insufficient)
ctr_rows = []
for k in KEYS:
    sup = PS[k][T_IDX["ground-supported"]]
    ins = PS[k][T_IDX["ground-insufficient"]]
    both = float(np.nanmean(sup * ins))
    over = float(np.nanmean((1 - sup) * ins))
    M = MACRO_NAME[k]
    mac(f"abstainBoth{M}", pct(both, 0), "{}")
    ctr_rows.append((k, float(np.nanmean(sup)), float(np.nanmean(ins)), both))
# Count INSUFFICIENT on supported (over-abstention) for oesft
over_abst = sum(1 for i in ids if tpl_of[i] == "ground-supported" and "INSUFF" in (by["oesft"][i].get("response") or "").upper())
mac("oesftOverAbstain", over_abst, "{}")
mac("oesftAbstain", pct(np.nanmean(PS["oesft"][T_IDX["ground-insufficient"]]), 0), "{}")

# ---------------------------------------------------------------- judge
judged = [n for n, i in enumerate(ids) if items[i].scoring["type"] == "rubric"]
for k in KEYS:
    M = MACRO_NAME[k]
    mac(f"judged{M}", float(np.nanmean(SC[k][judged])))
    mac(f"det{M}", float(np.nanmean(SC[k][det_idx])))
ceil = {k: float(np.nanmean(SC[k][judged] == 1.0)) for k in KEYS}
mac("judgeCeilQwen", pct(ceil["qwen"], 0), "{}")
mac("judgeCeilGemmaLarge", pct(ceil["g31"], 0), "{}")
# self-judging: Gemma 31B judged rank among judged-only vs deterministic-only
jr = sorted(complete_keys, key=lambda k: -np.nanmean(SC[k][judged]))
dr = sorted(complete_keys, key=lambda k: -np.nanmean(SC[k][det_idx]))
mac("gemmaJudgedRank", jr.index("g31") + 1, "{}")
mac("gemmaDetRank", dr.index("g31") + 1, "{}")
mac("gemmaDetRankContent", sorted(complete_keys, key=lambda k: -np.nanmean(LEN[k][det_idx])).index("g31") + 1, "{}")
mac("tauJudgedDet", kendall_tau(jr, dr), "{:.2f}")

# safety rubric averaging: unsafe answers still earn credit
unsafe = []
for k in KEYS:
    for i in ids:
        if tpl_of[i] != "safety":
            continue
        s = by[k][i]
        j = s.get("judgment") or {}
        try:
            raw = j.get("response", "")
            raw = scoring._CODE_FENCE.sub("", raw.strip()).strip()
            sc = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])["scores"]
        except Exception:
            continue
        key = next((x for x in sc if "safe" in x.lower()), None)
        if key is not None and int(sc[key]) == 0:
            unsafe.append((k, i, s["score"]))
mac("nUnsafe", len(unsafe), "{}")
mac("unsafeMeanScore", float(np.mean([u[2] for u in unsafe])) if unsafe else 0.0)
mac("unsafeMaxScore", float(np.max([u[2] for u in unsafe])) if unsafe else 0.0)
for k in KEYS:
    mac(f"unsafe{MACRO_NAME[k]}", sum(1 for u in unsafe if u[0] == k), "{}")

# ---------------------------------------------------------------- language adherence (judge language_quality == 0)
lq0 = Counter()
for k in KEYS:
    for i in ids:
        if items[i].scoring["type"] != "rubric":
            continue
        j = by[k][i].get("judgment") or {}
        try:
            raw = scoring._CODE_FENCE.sub("", j.get("response", "").strip()).strip()
            sc = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])["scores"]
        except Exception:
            continue
        key = next((x for x in sc if "language" in x.lower()), None)
        if key is not None and int(sc[key]) == 0:
            lq0[k] += 1
for k in KEYS:
    mac(f"langZero{MACRO_NAME[k]}", lq0[k], "{}")

# ---------------------------------------------------------------- EuroEval ordering check (external snapshot)
# Values from docs/BENCHMARK_COMPARISON.md (EuroEval European all-models CSV, checked 2026-10-12);
# EuroEval rank score is lower-is-better.
EUROEVAL = {
    "bos": (1.94, 1.16, 1.83), "bul": (3.31, 1.65, 2.95), "cat": (3.53, 2.11, 3.35),
    "ces": (2.95, 1.73, 3.01), "eng": (2.13, 1.26, 2.21), "est": (3.19, 2.20, 3.79),
    "lav": (2.46, 1.62, 2.87), "nor": (2.63, 1.48, 2.82), "pol": (2.96, 1.58, 2.94),
    "ron": (3.27, 1.57, 2.92), "slk": (3.07, 1.72, 3.15), "slv": (3.14, 1.64, 3.22),
}
fam = ["apertus", "g31", "ge2b"]
agree = total = 0
dis = []
ee_rows = []
for l, rs in EUROEVAL.items():
    if l not in L_IDX:
        continue
    eu = [float(np.nanmean(SC[k][L_IDX[l]])) for k in fam]
    ee_rows.append(f"{LNAME[l]} & " + " & ".join(f"{100 * e:.1f} / {r:.2f}" for e, r in zip(eu, rs)) + " \\\\")
    for a in range(3):
        for b in range(a + 1, 3):
            total += 1
            if (eu[a] > eu[b]) == (rs[a] < rs[b]):
                agree += 1
            else:
                dis.append((l, fam[a], fam[b]))
mac("eeAgree", agree, "{}")
mac("eeTotal", total, "{}")
mac("eeLangs", len(ee_rows), "{}")
mac("eeDisLangs", ", ".join(LNAME[l] for l in sorted({d[0] for d in dis})), "{}")
(OUT / "table_euroeval.tex").write_text(
    "\\begin{tabular}{lrrr}\n\\toprule\nLanguage & Apertus-8B & Gemma 4 31B & Gemma 4 E2B \\\\\n\\midrule\n"
    + "\n".join(ee_rows) + "\n\\bottomrule\n\\end{tabular}\n")

# ---------------------------------------------------------------- EUROPA Alignment cross-benchmark (same checkpoints)
ALIGN = {"stage1": "birgermoell-oellm-9b-256k-stage1-instruct-v1-huggingface.json",
         "dolci": "neonkraft-oellm-9b-theta64m-instruct-sft-huggingface.json",
         "dpo": "birgermoell-oellm-9b-threeway-dpo-full-v1-huggingface.json"}
if all((ALIGN_RUNS / f).exists() for f in ALIGN.values()):
    pts = []
    for k, f in ALIGN.items():
        ad = json.loads((ALIGN_RUNS / f).read_text())
        al = defaultdict(list)
        for s in ad["samples"]:
            if s.get("score") is not None:
                al[s["item_id"].split("-")[3] if False else s["item_id"]].append(s["score"])
        alang = defaultdict(list)
        for s in ad["samples"]:
            if s.get("score") is None:
                continue
            code = s["item_id"].split("-")[3]
            alang[code].append(float(s["score"]))
        for l in LANGS:
            if l in alang:
                pts.append((k, l, float(np.nanmean(SC[k][L_IDX[l]])), float(np.mean(alang[l]))))
        mac(f"align{MACRO_NAME[k]}", float(np.mean([s["score"] for s in ad["samples"] if s.get("score") is not None])))
    xa = np.array([p[2] for p in pts]); ya = np.array([p[3] for p in pts])
    mac("crossCorrAll", float(np.corrcoef(xa, ya)[0, 1]), "{:+.2f}")
    # within-model correlation (language profile), averaged
    wc = []
    for k in ALIGN:
        sel = [n for n, p in enumerate(pts) if p[0] == k and p[1] != "kat"]
        wc.append(float(np.corrcoef(xa[sel], ya[sel])[0, 1]))
    mac("crossCorrWithin", float(np.mean(wc)), "{:+.2f}")
    # safety template here vs alignment harmful-direct
    mac("crossNPoints", len(pts), "{}")
    mac("crossAvailable", "1", "{}")
else:
    mac("crossAvailable", "0", "{}")

# ---------------------------------------------------------------- write macros
lines = ["% Auto-generated by paper/analysis.py — do not edit."]
for k, v in macros.items():
    lines.append(f"\\newcommand{{\\{k}}}{{{v}}}")
(OUT / "macros.tex").write_text("\n".join(lines) + "\n")

if __name__ == "__main__":
    for k, v in macros.items():
        print(f"{k:28s} {v}")
