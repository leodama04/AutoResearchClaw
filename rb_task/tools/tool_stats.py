#!/usr/bin/env python3
"""Statistics of the tools of each pipeline run, read from the run directories only (no new experiments).

Co-supervisor (call of 2026-10-13): "how many papers did the pipeline find, how many did it actually use, how many
code changes did it make, also in lines of code - things you can extract from the logs, also for the earlier runs".

Usage (host or container, from the repo root):
  python3 rb_task/tools/tool_stats.py artifacts/rc-*                      -> docs/runs/tool_stats.md / .json
  python3 rb_task/tools/tool_stats.py artifacts/rc-A artifacts/rc-B --out docs/runs/tool_stats_AB
Older runs simply have fewer fields ("-"): the files they did not produce are skipped.
"""
from __future__ import annotations

import argparse
import difflib
import glob
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path


def jload(p: Path, default=None):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def lines_changed(a: str, b: str) -> tuple[int, int]:
    add = rem = 0
    for ln in difflib.unified_diff(a.splitlines(), b.splitlines(), lineterm="", n=0):
        if ln.startswith("+") and not ln.startswith("+++"):
            add += 1
        elif ln.startswith("-") and not ln.startswith("---"):
            rem += 1
    return add, rem


def spearman(xs: list, ys: list) -> float | None:
    if len(xs) < 3:
        return None

    def rank(a):
        o = sorted(range(len(a)), key=lambda i: a[i])
        r = [0.0] * len(a)
        for k, i in enumerate(o):
            r[i] = float(k)
        return r

    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else None


def metric_key(m: dict) -> str | None:
    for k in m or {}:
        mm = re.match(r"^proposed_val_(\w+)_mean$", k)
        if mm:
            return mm.group(1)
    return None


def stats(run: Path) -> dict:
    s: dict = {"run": run.name}
    summ = jload(run / "pipeline_summary.json", {}) or {}
    s["run_id"] = summ.get("run_id", run.name)
    s["status"] = summ.get("final_status")
    durs = [jload(p, {}).get("duration_sec") or 0 for p in run.glob("stage-*/stage_health.json")]
    s["hours"] = round(sum(durs) / 3600, 2) if durs else None
    # ---------------------------------------------------------------- literature
    q = jload(run / "stage-03" / "queries.json", {}) or {}
    s["queries"] = len(q.get("queries") or []) or None
    s["queries_by_llm"] = q.get("model_queries_extracted")
    s["candidates"] = (jload(run / "stage-04" / "search_meta.json", {}) or {}).get("total_candidates")
    sl = run / "stage-05" / "shortlist.jsonl"
    s["shortlist"] = sum(1 for ln in sl.read_text(encoding="utf-8").splitlines() if ln.strip()) if sl.is_file() else None
    km = jload(run / "stage-06" / "knowledge_meta.json", {}) or {}
    cards = km.get("cards") or []
    s["cards"] = len(cards) if km else None
    s["cards_fulltext"] = sum(1 for c in cards if c.get("pdf")) if km else None
    s["discarded_no_fulltext"] = len(km.get("discarded_no_fulltext") or []) if km else None
    s["card_titles"] = [f"{c.get('id')}: {str(c.get('title'))[:70]}" for c in cards]
    s["card_repos"] = [c.get("repo") for c in cards if c.get("repo")]
    s["stage5_repos"] = len((jload(run / "stage-05" / "code_repos.json", {}) or {}).get("repos") or []) or 0
    vend = list((run / "stage-06" / "vendor").glob("*.py"))
    s["vendored_files"] = len(vend)
    s["vendored_chars"] = sum(p.stat().st_size for p in vend)
    # ---------------------------------------------------------------- refinement
    seed_dir = run / "stage-10" / "experiment"
    seed_model = (seed_dir / "rb_model.py").read_text(encoding="utf-8") if (seed_dir / "rb_model.py").is_file() else ""
    passes = sorted([d for d in run.glob("stage-13*") if (d / "refinement_log.json").is_file()],
                    key=lambda d: str((jload(d / "refinement_log.json", {}) or {}).get("generated", "")))
    s["passes"] = len(passes)
    c = Counter()
    imports, cites, gtypes, loc = Counter(), Counter(), Counter(), []
    vals, tests = [], []
    for d in passes:
        L = jload(d / "refinement_log.json", {}) or {}
        for it in L.get("iterations", []):
            if not isinstance(it, dict) or it.get("arc_carried_from"):
                continue
            c["attempts"] += 1
            sb = it.get("sandbox") or {}
            c["evaluated"] += it.get("metric") is not None
            c["first_run_crash"] += sb.get("returncode") not in (0, None)
            c["skipped_unchanged"] += "SKIPPED" in str(sb.get("stderr") or "")
            c["rejected"] += bool(it.get("arc_rejected"))
            c["runtime_repaired"] += bool(it.get("runtime_repaired"))
            c["llm_error"] += bool(it.get("llm_error"))
            c["improved"] += bool(it.get("improved"))
            vd = d / str(it.get("version_dir", "")).strip("/")
            # official code imported by this attempt, read from its code (works for every kit version; the field
            # arc_official_code exists only from kit 0.6)
            own = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in vd.glob("*.py")
                            if not p.name.startswith("vendor_") and p.name != "rb_model_official.py") if vd.is_dir() else ""
            oc = sorted(set(re.findall(r"^\s*(?:from|import)\s+(vendor_\w+)", own, re.M))) or (it.get("arc_official_code") or [])
            c["official_code_attempts"] += bool(oc)
            imports.update(oc)
            cfg = (vd / "rb_config.py").read_text(encoding="utf-8") if (vd / "rb_config.py").is_file() else ""
            src = re.search(r"^PROPOSED_SOURCE\s*=\s*(.*)$", cfg, re.M)
            for k in set(re.findall(r"\bK\d+\b", src.group(1) if src else "")):
                cites[k] += 1
            ovl = re.search(r"^PROPOSED_OVERRIDES\s*=\s*(.*)$", cfg, re.M)  # not the BASELINE dict above it
            gt = re.search(r"['\"]gnn_type['\"]\s*:\s*['\"]([^'\"]+)", ovl.group(1) if ovl else "")
            if gt:
                gtypes[gt.group(1)] += 1
            if seed_model and (vd / "rb_model.py").is_file():
                loc.append(sum(lines_changed(seed_model, (vd / "rb_model.py").read_text(encoding="utf-8"))))
            m = (it.get("sandbox_after_fix") or sb).get("metrics") or {}
            mk = metric_key(m)
            if it.get("metric") is not None and mk and f"proposed_test_{mk}_mean" in m:
                vals.append(m[f"proposed_val_{mk}_mean"])
                tests.append(m[f"proposed_test_{mk}_mean"])
    s.update(dict(c))
    s["official_imports"] = dict(imports.most_common(8))
    s["card_citations"] = dict(sorted(cites.items()))
    s["distinct_gnn_types"] = len(gtypes)
    s["top_gnn_types"] = dict(gtypes.most_common(5))
    s["rb_model_lines_changed_median"] = statistics.median(loc) if loc else None
    r = spearman(vals, tests)
    s["val_test_spearman"] = f"{r:.3f} (n={len(vals)})" if r is not None else None
    # ---------------------------------------------------------------- final model
    final = None
    for d in reversed(passes):
        if (d / "experiment_final").is_dir():
            final = d / "experiment_final"
            break
    if final is not None:
        changed, new, add_tot, rem_tot = {}, [], 0, 0
        for f in sorted(final.glob("*.py")):
            ref = seed_dir / f.name
            if not ref.is_file():
                new.append(f.name)
                continue
            a, b = lines_changed(ref.read_text(encoding="utf-8"), f.read_text(encoding="utf-8"))
            if a or b:
                changed[f.name] = f"+{a}/-{b}"
                add_tot, rem_tot = add_tot + a, rem_tot + b
        s["final_files_changed"] = changed
        s["final_new_files"] = [n for n in new if not n.startswith("vendor_")]
        s["final_lines_added"], s["final_lines_removed"] = add_tot, rem_tot
        cfg = (final / "rb_config.py").read_text(encoding="utf-8") if (final / "rb_config.py").is_file() else ""
        src = re.search(r"^PROPOSED_SOURCE\s*=\s*(.*)$", cfg, re.M)
        ov = re.search(r"^PROPOSED_OVERRIDES\s*=\s*(.*)$", cfg, re.M)
        s["final_source"] = src.group(1).strip() if src else None
        s["final_overrides"] = ov.group(1).strip() if ov else None
        code = "\n".join(p.read_text(encoding="utf-8") for p in final.glob("*.py")
                         if not p.name.startswith("vendor_") and p.name != "rb_model_official.py")
        s["final_uses_official_code"] = sorted(set(re.findall(r"^\s*(?:from|import)\s+(vendor_\w+)", code, re.M)))
    conf = jload(passes[-1] / "confirmation.json", {}) if passes else {}
    if conf and conf.get("valid"):
        m = conf.get("metrics") or {}
        mk = metric_key(m) or "roc_auc"
        for cond in ("baseline_graphsage", "baseline_tuned", "proposed"):
            s[f"confirm_{cond}_val"] = m.get(f"{cond}_val_{mk}_mean")
            s[f"confirm_{cond}_test"] = m.get(f"{cond}_test_{mk}_mean")
        for k in ("val", "test"):
            st = (conf.get("paired") or {}).get(f"proposed-baseline_tuned:{k}") or {}
            s[f"confirm_delta_{k}"] = st.get("mean_diff")
            s[f"confirm_p_{k}"] = st.get("p_signflip")
            a, b = s.get(f"confirm_proposed_{k}"), s.get(f"confirm_baseline_tuned_{k}")
            if s[f"confirm_delta_{k}"] is None and isinstance(a, (int, float)) and isinstance(b, (int, float)):
                s[f"confirm_delta_{k}"] = a - b   # older kits: no paired statistics, difference of the means only (no p)
    q20 = jload(run / "stage-20" / "quality_report.json", {}) or {}
    s["paper_quality"] = q20.get("score_1_to_10")
    return s


ROWS = [
    ("durata (h)", "hours"), ("stato", "status"), ("query (scritte dall'LLM)", lambda s: f"{s.get('queries')} ({s.get('queries_by_llm')})"),
    ("candidati trovati", "candidates"), ("shortlist", "shortlist"), ("schede dal testo completo", "cards_fulltext"),
    ("paper scartati (senza testo completo)", "discarded_no_fulltext"), ("schede", "card_titles"),
    ("repository dei paper delle schede", "card_repos"), ("repository clonati allo stage 5", "stage5_repos"),
    ("file vendorizzati (caratteri)", lambda s: f"{s.get('vendored_files')} ({s.get('vendored_chars')})"),
    ("passate dello stage 13", "passes"), ("tentativi", "attempts"), ("valutati", "evaluated"),
    ("crash alla prima esecuzione", "first_run_crash"), ("riparati", "runtime_repaired"), ("identici, non eseguiti", "skipped_unchanged"),
    ("respinti dai controlli", "rejected"), ("errori dell'LLM", "llm_error"), ("miglioramenti accettati", "improved"),
    ("tentativi con codice ufficiale importato", "official_code_attempts"), ("moduli ufficiali importati", "official_imports"),
    ("schede citate (tentativi)", "card_citations"), ("tipi di architettura distinti", "distinct_gnn_types"),
    ("più provati", "top_gnn_types"), ("righe cambiate in rb_model.py per tentativo (mediana)", "rb_model_lines_changed_median"),
    ("correlazione val-test sui tentativi", "val_test_spearman"),
    ("modello finale: file cambiati", "final_files_changed"), ("modello finale: righe +/-", lambda s: f"+{s.get('final_lines_added')}/-{s.get('final_lines_removed')}" if "final_lines_added" in s else "-"),
    ("modello finale: nuovi file", "final_new_files"), ("modello finale: usa codice ufficiale",
     lambda s: ("no" if not s["final_uses_official_code"] else s["final_uses_official_code"]) if "final_uses_official_code" in s else None),
    ("modello finale: fonte dichiarata", "final_source"),
    ("conferma: test baseline_tuned / proposed", lambda s: f"{_f(s.get('confirm_baseline_tuned_test'))} / {_f(s.get('confirm_proposed_test'))}"),
    ("conferma: Δ val (p)", lambda s: f"{_f(s.get('confirm_delta_val'), True)} ({_f(s.get('confirm_p_val'))})"),
    ("conferma: Δ test (p)", lambda s: f"{_f(s.get('confirm_delta_test'), True)} ({_f(s.get('confirm_p_test'))})"),
    ("qualità del paper (revisione automatica)", "paper_quality"),
]


def _f(x, sign=False):
    if not isinstance(x, (int, float)):
        return "-"
    return f"{x:+.4f}" if sign else f"{x:.4f}"


def cell(s: dict, getter) -> str:
    v = getter(s) if callable(getter) else s.get(getter)
    if v is None or v == {} or v == []:
        return "-"
    if isinstance(v, dict):
        return ", ".join(f"{k}: {x}" for k, x in v.items())
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return str(v).replace("|", "/")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", default=sorted(glob.glob("artifacts/rc-*")))
    ap.add_argument("--out", default="docs/runs/tool_stats")
    a = ap.parse_args()
    runs = [Path(r) for r in a.runs if Path(r).is_dir()]
    if not runs:
        print("no run directories", file=sys.stderr)
        return 1
    data = [stats(r) for r in runs]
    lines = ["# Statistiche dei tool per run (lette dai file delle run)", "",
             "| | " + " | ".join(d["run_id"] for d in data) + " |", "|---|" + "---|" * len(data)]
    for label, getter in ROWS:
        lines.append(f"| {label} | " + " | ".join(cell(d, getter) for d in data) + " |")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines) + f"\n\nsaved: {out.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
