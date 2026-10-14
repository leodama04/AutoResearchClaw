#!/usr/bin/env python3
"""Generate a factual Markdown report from an AutoResearchClaw run directory.

    python3 rb_task/tools/run_report.py artifacts/rc-XXXX [--out docs/runs/RUN-003_auto.md] [--manifest path]

Everything printed here is read from the run's own files (no interpretation). The "Interpretation" section is left
for a human. Standard library only (PyYAML is used if available).
"""
import argparse
import glob
import json
import math
import re
import sys
from pathlib import Path


def jload(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return default


def f4(x):
    return f"{x:.4f}" if isinstance(x, (int, float)) and math.isfinite(x) else "n/a"


def stage_sort_key(name):
    m = re.match(r"stage-(\d+)(?:_(.*))?$", name)
    return (int(m.group(1)), m.group(2) or "") if m else (999, name)


def collect_metric_numbers(obj, out):
    """Floats found as VALUES in nested dicts/lists; strings (stdout, logs) are ignored on purpose."""
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, (int, float)):
        if math.isfinite(obj):
            out.add(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            collect_metric_numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_metric_numbers(v, out)


def known_metric_numbers(R, passes):
    known = set()
    best = jload(R / "experiment_summary_best.json", {})
    summ14 = jload(R / "stage-14" / "experiment_summary.json", {})
    for data in (best, summ14):
        collect_metric_numbers(data.get("metrics_summary", {}), known)
    collect_metric_numbers((jload(R / "stage-12" / "runs" / "run-1.json", {}) or {}).get("metrics", {}), known)
    for n in passes:
        for it in (jload(R / n / "refinement_log.json", {}) or {}).get("iterations", []):
            for key in ("sandbox", "sandbox_after_fix"):
                collect_metric_numbers(((it or {}).get(key) or {}).get("metrics", {}), known)
        collect_metric_numbers((jload(R / n / "confirmation.json", {}) or {}).get("metrics", {}), known)
    return known


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out")
    ap.add_argument("--manifest")
    ap.add_argument("--title", default="")
    a = ap.parse_args()
    R = Path(a.run_dir)
    if not R.is_dir():
        sys.exit(f"not a directory: {R}")
    L = []
    w = L.append

    summ = jload(R / "pipeline_summary.json", {})
    run_id = summ.get("run_id", R.name)
    w(f"# Run report: {a.title or run_id}\n")
    w("> Generated automatically by `rb_task/tools/run_report.py` from the run directory. Facts only; interpretation is in the last section.\n")

    # ------------------------------------------------------------------ overview
    stages = sorted([p.parent.name for p in R.glob("stage-*/stage_health.json")], key=stage_sort_key)
    durs = {s: (jload(R / s / "stage_health.json", {}) or {}) for s in stages}
    total = sum(d.get("duration_sec", 0) for d in durs.values())
    w("## 1. Overview\n")
    w("| field | value |\n|---|---|")
    w(f"| run id | `{run_id}` |")
    w(f"| final status | {summ.get('final_status')} ({summ.get('stages_done')}/{summ.get('stages_executed')} stage executions done, "
      f"{summ.get('stages_failed')} failed, degraded={summ.get('degraded')}) |")
    w(f"| generated | {summ.get('generated')} |")
    w(f"| total stage time | {total / 3600:.2f} h |")
    cfg = None
    try:
        import yaml  # type: ignore
        cfg = yaml.safe_load((R / "config.yaml").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        cfg = None
    if cfg:
        e = cfg.get("experiment", {})
        w(f"| topic | {cfg.get('research', {}).get('topic')} |")
        w(f"| llm | {cfg.get('llm', {}).get('primary_model')} |")
        w(f"| experiment | mode={e.get('mode')}, time_budget_sec={e.get('time_budget_sec')}, max_iterations={e.get('max_iterations')}, "
          f"metric={e.get('metric_key')} ({e.get('metric_direction')}) |")
    cp = jload(R / "checkpoint.json", {})
    if cp:
        w(f"| checkpoint | {json.dumps({k: v for k, v in cp.items() if not isinstance(v, (dict, list))})[:200]} |")
    if a.manifest and Path(a.manifest).is_file():
        w(f"| manifest | `{a.manifest}` |")
        w("\n<details><summary>manifest (environment / settings used)</summary>\n\n```\n" +
          Path(a.manifest).read_text(encoding="utf-8", errors="replace")[:3000] + "\n```\n</details>")
    dh = jload(R / "decision_history.json", [])
    if dh:
        w(f"\nPipeline decisions after the analysis: {[(d.get('decision'), d.get('rollback_target')) for d in dh]}")

    w("\n### Stage durations\n")
    w("| stage | status | seconds |\n|---|---|---|")
    for s in stages:
        w(f"| {s} | {durs[s].get('status')} | {round(durs[s].get('duration_sec', 0))} |")

    # ------------------------------------------------------------------ reference run
    w("\n## 2. Reference evaluation (stage 12)\n")
    r1 = jload(R / "stage-12" / "runs" / "run-1.json", {})
    m = r1.get("metrics") or {}
    conds = sorted(k[: -len("_n_seeds")] for k in m if k.endswith("_n_seeds"))
    if conds:
        w(f"status={r1.get('status')}, elapsed={round(r1.get('elapsed_sec', 0))} s, peak GPU memory {f4(m.get('peak_gpu_mem_gb'))} GB\n")
        w("| condition | seeds | val ROC-AUC | test ROC-AUC |\n|---|---|---|---|")
        for c in conds:
            w(f"| {c} | {int(m[c + '_n_seeds'])} | {f4(m.get(c + '_val_roc_auc_mean'))} ± {f4(m.get(c + '_val_roc_auc_std'))} "
              f"| {f4(m.get(c + '_test_roc_auc_mean'))} ± {f4(m.get(c + '_test_roc_auc_std'))} |")
        w(f"\nprimary_metric (selection metric) = {f4(m.get('primary_metric'))}")
    else:
        w("No per-condition metrics found in stage-12/runs/run-1.json.")

    # ------------------------------------------------------------------ refinement
    w("\n## 3. Iterative refinement (stage 13)\n")
    passes = sorted([p.parent.name for p in R.glob("stage-13*/refinement_log.json")],
                    key=lambda n: str((jload(R / n / "refinement_log.json", {}) or {}).get("generated", "")))
    best_overall = []
    for name in passes:
        log = jload(R / name / "refinement_log.json", {})
        mode = "config" if any((i or {}).get("arc_source") for i in log.get("iterations", [])) else "code"
        w(f"### {name}  (mode: {mode}; generated {log.get('generated')})\n")
        w(f"baseline_metric={f4(log.get('baseline_metric'))}, best_metric={f4(log.get('best_metric'))} "
          f"({log.get('best_version')}), stop_reason={log.get('stop_reason')}, iterations={len(log.get('iterations', []))}\n")
        w("| it | metric | improved | rc | seconds | detail |\n|---|---|---|---|---|---|")
        for it in log.get("iterations", []):
            sb = it.get("sandbox_after_fix") or it.get("sandbox") or {}
            detail = ""
            if "arc_overrides" in it:
                detail = f"overrides `{json.dumps(it['arc_overrides'], sort_keys=True)}` ({it.get('arc_source')})"
                if it.get("arc_rationale"):
                    detail += f" — {str(it['arc_rationale'])[:90]}"
            else:
                detail = "files: " + ", ".join(it.get("files", [])[:7])
            if it.get("arc_official_code"):
                detail += f" [official code: {', '.join(it['arc_official_code'])}]"
            if it.get("arc_recheck"):
                rc = it["arc_recheck"]
                detail += f" [re-check seeds+{rc.get('seed_offset')}: {f4(rc.get('first'))} / {f4(rc.get('second'))}]"
            if it.get("arc_rejected"):
                detail += f" **REJECTED: {it['arc_rejected']}**"
            if it.get("runtime_repaired"):
                detail += " (runtime-repaired)"
            if it.get("llm_error"):
                detail = f"**LLM call failed, attempt skipped: {str(it['llm_error'])[:120]}**"
            if it.get("repair_llm_error"):
                detail += f" (repair LLM call failed: {str(it['repair_llm_error'])[:80]})"
            if "GPU_UNAVAILABLE" in str((it.get("sandbox") or {}).get("stdout", "")):
                detail += " **GPU occupied by other processes: not evaluated**"
            ns = (sb.get("metrics") or {}).get("proposed_n_seeds")
            if ns is not None:
                detail += f" [proposed seeds={int(ns)}]"
            w(f"| {it.get('iteration')} | {f4(it.get('metric'))} | {it.get('improved')} | {sb.get('returncode')} | "
              f"{round(sb.get('elapsed_sec') or 0)} | {detail} |")
        conf = log.get("confirmation")
        if conf:
            w(f"\nConfirmation on fresh seeds: {conf}")
        best_overall.append(name)

    cj = None
    for name in passes:
        p = R / name / "confirmation.json"
        if p.is_file():
            cj = jload(p, {})
            w(f"\n### Confirmation on fresh seeds ({name}/confirmation.json)\n")
            cm = cj.get("metrics") or {}
            w(f"seed offset {cj.get('seed_offset')}, valid={cj.get('valid')}, rc={cj.get('returncode')}\n")
            w("| condition | val ROC-AUC | test ROC-AUC |\n|---|---|---|")
            for c in sorted(k[: -len('_n_seeds')] for k in cm if k.endswith('_n_seeds')):
                w(f"| {c} | {f4(cm.get(c + '_val_roc_auc_mean'))} ± {f4(cm.get(c + '_val_roc_auc_std'))} "
                  f"| {f4(cm.get(c + '_test_roc_auc_mean'))} ± {f4(cm.get(c + '_test_roc_auc_std'))} |")

    # ------------------------------------------------------------------ analysis / paper
    w("\n## 4. Analysis, paper and checks\n")
    q = jload(R / "stage-20" / "quality_report.json", {})
    fl = jload(R / "stage-20" / "fabrication_flags.json", {})
    vr = jload(R / "stage-23" / "verification_report.json", {})
    w(f"- quality report: score {q.get('score_1_to_10')}/10 — {q.get('verdict')}")
    w(f"- fabrication flags: suspected={fl.get('fabrication_suspected')}, verified values={fl.get('verified_values_count')}")
    if vr:
        w(f"- citations: {summ.get('content_metrics', {}).get('verified_citations')}/{summ.get('content_metrics', {}).get('total_citations')} verified")
    for k in ("weaknesses", "required_actions"):
        if q.get(k):
            w(f"- {k}: " + "; ".join(str(x)[:160] for x in q[k][:4]))
    pdf = R / "stage-22" / "paper.pdf"
    w(f"- paper PDF: {'`' + str(pdf) + '`' if pdf.exists() else 'not produced'}")

    paper_p = R / "stage-23" / "paper_final_verified.md"
    if paper_p.exists():
        paper = paper_p.read_text(encoding="utf-8", errors="replace")
        w(f"- paper length: {len(paper.split())} words")
        # numbers in the paper that appear nowhere in the run's results
        known = known_metric_numbers(R, passes)
        # a number printed with d decimals matches a result if rounding the result to d decimals gives the same value
        found = {}
        for m_ in re.finditer(r"(?<![\w.])(0\.\d{3,4})(?![\w])", paper):
            txt = m_.group(1)
            if 0.5 <= float(txt) < 1.0:
                found[txt] = len(txt) - 2
        unmatched = sorted(t for t, d in found.items() if not any(round(k, d) == float(t) for k in known))
        w(f"- numbers (0.5–1.0, 3–4 decimals) in the paper: {len(found)}; **without a match among the run's aggregated results: {len(unmatched)}**"
          + (f" → {unmatched[:25]}" if unmatched else ""))
        seeds_claimed = sorted({m.group(1).lower() for m in re.finditer(r"\b(three|3|five|5|ten|10|twenty|20)\s+(?:independent\s+)?seeds", paper, re.I)})
        w(f"- seed counts claimed in the paper text: {seeds_claimed or 'none found'}")
        i = paper.lower().find("abstract")
        if i >= 0:
            w("\n<details><summary>abstract (as written by the pipeline)</summary>\n\n" + paper[i:i + 1400].replace("\n", " ") + "\n</details>")

    w("\n## 5. Interpretation (to be written by a human)\n")
    w("- **What was done:** \n- **Results that can be trusted (and why):** \n- **What went wrong / limitations:** \n- **Decision / next step:** \n")

    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
