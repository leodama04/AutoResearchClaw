#!/usr/bin/env python3
"""Patches needed to run AutoResearchClaw on a fixed benchmark task (RelBench).

Run from the repo root:   python3 rb_task/patches/apply_relbench_patches.py

1. Stage 10 (CODE_GENERATION): if env ARC_SEED_PROJECT_DIR points to a directory
   containing a main.py, that project is used as the experiment code instead of
   asking the LLM to write it from scratch. All LLM-based "rewrite" steps of
   stage 10 (deep-quality repair, alignment regeneration, ablation repair) are
   skipped for a seeded project, so the baseline is never overwritten.
   The iterative refinement of stage 13 then improves the seeded code.
2. PromptManager: `prompts.extra_prompts` also works for sub-prompts
   (iterative_improve, iterative_repair, code_repair, code_exec_fix, ...), so the
   task specification reaches the stage-13 refinement prompts.
3. Updates researchclaw/pipeline/stage_impls/_stage12_repair.py (auto-repair of
   stage 12) so that it also sees the task specification (ARC_TASK_SPEC_FILE).
4. Stage 13 (ITERATIVE_REFINE), in _execution.py:
   - ARC_HIDE_TEST_METRICS=1: test-split metrics are removed from the run
     summaries shown to the LLM (it can only see validation numbers);
   - every evaluated attempt is appended to the prompt context (what changed, the
     validation metric, improved or not), so the LLM learns from earlier attempts;
   - ARC_REFINE_PATIENCE (default 2): consecutive non-improving attempts allowed
     before the loop stops.

5. Stage 13, "modes" (second block of edits, marker "ARC patch: stage13 modes"):
   - validity gate: an iteration counts only if the run exits 0 with every condition and the expected number of seeds
     (partial metrics of crashed runs are no longer accepted as improvements);
   - ARC_PROTECTED_FILES / ARC_SEARCH_SPACE_FILE: the LLM cannot change main.py, rb_data.py, ... nor anything in
     rb_config.py except the PROPOSED_OVERRIDES dict (validated against the search space);
   - ARC_SEARCH_MODE=config: instead of rewriting code, the LLM proposes the next architecture configuration as JSON;
     an executor writes it into rb_config.PROPOSED_OVERRIDES (deterministic fallback if the proposal is invalid);
   - ARC_MIN_IMPROVEMENT: minimum improvement over the best metric to accept an iteration (noise margin);
   - ARC_CONFIRM_SEED_OFFSET: after the loop, re-run the final project on fresh seeds and expose the numbers.
6. Root cause of the corrupted main.py seen in the first RelBench run: pipeline/_helpers._extract_multi_file_blocks
   renames the FIRST returned file to main.py when the LLM answer contains no main.py (a rule meant for single-file
   projects). An answer that contained only rb_config.py therefore overwrote main.py with the config text.
   ARC_PRESERVE_FILENAMES=1 disables that rename.
7. Prompts: ARC_KEEP_SEEDS=1 replaces the "exactly seeds = [0, 1, 2]" rule of the iterative_improve prompt.

Idempotent. Backups are written as *.bak.
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(".").resolve()
HERE = Path(__file__).resolve().parent

CODEGEN = ROOT / "researchclaw/pipeline/stage_impls/_code_generation.py"
MANAGER = ROOT / "researchclaw/prompts/manager.py"
EXECUTION = ROOT / "researchclaw/pipeline/stage_impls/_execution.py"
HELPERS = ROOT / "researchclaw/pipeline/_helpers.py"
REPAIR_DST = ROOT / "researchclaw/pipeline/stage_impls/_stage12_repair.py"
REPAIR_SRC = HERE / "_stage12_repair.py"
REFINE_DST = ROOT / "researchclaw/pipeline/stage_impls/_arc_refine.py"
REFINE_SRC = HERE / "_arc_refine.py"

MARK = "ARC patch: seed project"

# ---------------------------------------------------------------- stage 10
A1_OLD = (
    "    _code_agent_active = False\n"
    "    _beast_mode_used = False\n"
    "    _code_max_tokens = 8192\n"
)
A1_NEW = A1_OLD + '''
    # ARC patch: seed project -- start from an existing baseline instead of
    # LLM-generated code (set ARC_SEED_PROJECT_DIR to a dir containing main.py).
    import os as _arc_os

    _arc_seeded = False
    _arc_seed_dir = _arc_os.environ.get("ARC_SEED_PROJECT_DIR", "").strip()
    if _arc_seed_dir and Path(_arc_seed_dir).is_dir():
        _arc_seed_files = {
            _p.name: _p.read_text(encoding="utf-8")
            for _p in sorted(Path(_arc_seed_dir).glob("*.py"))
        }
        if "main.py" in _arc_seed_files:
            files = dict(_arc_seed_files)
            _arc_seeded = True
            _beast_mode_used = True  # skips Beast Mode / CodeAgent / single-shot
            _code_agent_active = True  # skips the LLM code-review step
            logger.warning(
                "Stage 10: SEEDED from %s (%d files) - LLM code generation skipped",
                _arc_seed_dir,
                len(files),
            )
        else:
            logger.warning(
                "Stage 10: ARC_SEED_PROJECT_DIR=%s has no main.py - ignoring", _arc_seed_dir
            )
'''

GUARDS = [
    (
        "    if critical_deep and llm is not None:\n",
        "    if critical_deep and llm is not None and not _arc_seeded:\n",
    ),
    (
        "    if llm is not None:\n        # Build structured code summary for alignment check\n",
        "    if llm is not None and not _arc_seeded:\n        # Build structured code summary for alignment check\n",
    ),
    (
        '    if llm is not None and main_code and "condition" in main_code.lower():\n',
        '    if llm is not None and not _arc_seeded and main_code and "condition" in main_code.lower():\n',
    ),
]

# ---------------------------------------------------------- prompt manager
M1_OLD = "            if stage not in self._stages:\n"
M1_NEW = (
    "            if stage not in self._stages and stage not in self._sub_prompts:\n"
)
M2_OLD = '''        entry = self._sub_prompts[name]
        kw = {k: str(v) for k, v in kwargs.items()}
        return RenderedPrompt(
            system=_render(entry["system"], kw),
            user=_render(entry["user"], kw),
        )
'''
M2_NEW = '''        entry = self._sub_prompts[name]
        kw = {k: str(v) for k, v in kwargs.items()}
        user_text = _render(entry["user"], kw)
        extra = self._extras.get(name, "")  # ARC patch: extras for sub-prompts
        if extra:
            user_text = (
                f"{user_text}\\n\\n"
                "## Additional Stage Guidance\\n"
                "_(from prompts.extra_prompts in config.yaml)_\\n\\n"
                f"{extra}"
            )
        return RenderedPrompt(
            system=_render(entry["system"], kw),
            user=user_text,
        )
'''

# ---------------------------------------------------------------- stage 13
E1_OLD = "            summary = dict(payload)\n"
E1_NEW = (
    "            summary = dict(payload)\n"
    "            try:  # ARC patch: stage13 refine (hide test metrics)\n"
    "                from researchclaw.pipeline.stage_impls._arc_refine import hide_test\n"
    "\n"
    "                summary = hide_test(summary)\n"
    "            except Exception:  # noqa: BLE001\n"
    "                pass\n"
)
E2_OLD = "        files_context = _files_to_context(best_files)\n"
E2_NEW = (
    "        files_context = _files_to_context(best_files)\n"
    "        _arc_prev_best = dict(best_files)  # ARC patch: stage13 refine\n"
)
E3_OLD = '        log["iterations"].append(iter_record)\n'
E3_NEW = (
    '        log["iterations"].append(iter_record)\n'
    "        try:  # ARC patch: stage13 refine (history for the next attempt)\n"
    "            from researchclaw.pipeline.stage_impls._arc_refine import history_line\n"
    "\n"
    "            run_summaries.append(\n"
    "                history_line(\n"
    "                    iteration, iter_record, _arc_prev_best, candidate_files, best_metric\n"
    "                )\n"
    "            )\n"
    "        except Exception:  # noqa: BLE001\n"
    "            pass\n"
)
E4_OLD = "        if no_improve_streak >= 2:\n"
E4_NEW = (
    "        if no_improve_streak >= int(\n"
    '            __import__("os").environ.get("ARC_REFINE_PATIENCE", "2") or 2\n'
    "        ):  # ARC patch: stage13 refine\n"
)

# ------------------------------------------------------------ stage 13: modes (gate, guard, config search, confirm)
X1_OLD = "    no_improve_streak = 0\n    consecutive_no_metrics = 0\n"
X1_NEW = X1_OLD + (
    "    try:  # ARC patch: stage13 modes\n"
    "        from researchclaw.pipeline.stage_impls import _arc_refine as _arc\n"
    "\n"
    "        _arc_state = _arc.ModeState(run_dir, stage_dir, config.research.topic)\n"
    "    except Exception as _arc_exc:  # noqa: BLE001\n"
    "        logger.warning(\"Stage 13: ARC modes unavailable: %s\", _arc_exc)\n"
    "        _arc = None\n"
    "        _arc_state = None\n"
)
X2_OLD = (
    "            response = _chat_with_prompt(\n"
    "                llm,\n"
    "                ip.system,\n"
    "                user_prompt,\n"
    "                max_tokens=ip.max_tokens or 8192,\n"
    "            )\n"
)
X2_NEW = (
    "            if _arc_state is not None and _arc_state.config_mode:  # ARC patch: stage13 modes\n"
    "                response = _arc.propose_config(\n"
    "                    _chat_with_prompt, llm, _arc_state, best_files, log, iteration,\n"
    "                    best_metric, baseline_metric,\n"
    "                )\n"
    "            else:\n"
    "                response = _chat_with_prompt(\n"
    "                    llm,\n"
    "                    ip.system,\n"
    "                    user_prompt,\n"
    "                    max_tokens=ip.max_tokens or 8192,\n"
    "                )\n"
)
X3_OLD = "        # BUG-R6-02: Preserve entry point when LLM strips main() function.\n"
X3_NEW = (
    "        if _arc_state is not None:  # ARC patch: stage13 modes (guard)\n"
    "            try:\n"
    "                candidate_files, _arc_notes = _arc.guard_candidate(\n"
    "                    best_files, candidate_files, _arc_state.space, _arc_state.protected\n"
    "                )\n"
    "                if _arc_notes:\n"
    "                    logger.warning(\n"
    "                        \"Stage 13 iteration %d guard: %s\", iteration, \"; \".join(_arc_notes[:4])\n"
    "                    )\n"
    "            except Exception as _g_exc:  # noqa: BLE001\n"
    "                logger.warning(\"Stage 13: guard failed: %s\", _g_exc)\n"
) + X3_OLD
X4_OLD = "        if issue_text:\n            iter_record[\"validation_issues\"] = issue_text\n"
X4_NEW = X4_OLD + (
    "        if _arc_state is not None:  # ARC patch: stage13 modes\n"
    "            _arc.annotate(iter_record, _arc_state)\n"
)
X5_OLD = "            metric_val = _find_metric(rerun.metrics, metric_key)\n"
X5_NEW = "            _arc_final_run = rerun  # ARC patch: stage13 modes\n" + X5_OLD
X6_OLD = "                    metric_val = _find_metric(rerun2.metrics, metric_key)\n"
X6_NEW = X6_OLD + "                    _arc_final_run = rerun2  # ARC patch: stage13 modes\n"
X7_OLD = "            runtime_issues = _detect_runtime_issues(rerun)\n"
X7_NEW = (
    "            runtime_issues = (  # ARC patch: stage13 modes (no code repair in config mode)\n"
    "                None\n"
    "                if (_arc_state is not None and _arc_state.config_mode)\n"
    "                else _detect_runtime_issues(rerun)\n"
    "            )\n"
)
X8_OLD = "            if metric_val is not None:\n                consecutive_no_metrics = 0\n"
X8_NEW = (
    "            if _arc_state is not None and _arc_state.gate_enabled and metric_val is not None:\n"
    "                _ok, _why = _arc.run_is_valid(_arc_final_run, _arc_state.expected, metric_key)  # ARC patch: gate\n"
    "                if not _ok:\n"
    "                    logger.warning(\"Stage 13 iteration %d: run rejected (%s)\", iteration, _why)\n"
    "                    iter_record[\"arc_rejected\"] = _why\n"
    "                    iter_record[\"metric\"] = None\n"
    "                    metric_val = None\n"
) + X8_OLD
X9_OLD = "                if _is_better(metric_val, best_metric):\n"
X9_NEW = (
    "                if _is_better(metric_val, best_metric) and (  # ARC patch: noise margin\n"
    "                    _arc_state is None\n"
    "                    or _arc.margin_ok(metric_val, best_metric, metric_direction, _arc_state.margin)\n"
    "                ):\n"
)
X10_OLD = "    _write_project(final_dir, best_files)\n    # Backward compat: also write experiment_final.py (copy of main.py)\n"
X10_NEW = (
    "    if _arc_state is not None and _arc_state.confirm_offset:  # ARC patch: confirmation on fresh seeds\n"
    "        try:\n"
    "            _arc.confirm(\n"
    "                _arc_state, config, stage_dir, best_files, best_version, log,\n"
    "                create_sandbox, _write_project, logger,\n"
    "            )\n"
    "        except Exception as _c_exc:  # noqa: BLE001\n"
    "            logger.warning(\"Stage 13: confirmation failed: %s\", _c_exc)\n"
) + X10_OLD
EXEC_MODES = [(X1_OLD, X1_NEW), (X2_OLD, X2_NEW), (X3_OLD, X3_NEW), (X4_OLD, X4_NEW), (X5_OLD, X5_NEW),
              (X6_OLD, X6_NEW), (X7_OLD, X7_NEW), (X8_OLD, X8_NEW), (X9_OLD, X9_NEW), (X10_OLD, X10_NEW)]

# ------------------------------------------------------------ helpers: do not rename the first file to main.py
H1_OLD = (
    "            if \"main.py\" not in files:\n"
    "                # Pick the first file as main.py\n"
    "                first_key = next(iter(files))\n"
    "                files[\"main.py\"] = files.pop(first_key)\n"
)
H1_NEW = (
    "            if \"main.py\" not in files and __import__(\"os\").environ.get(\n"
    "                \"ARC_PRESERVE_FILENAMES\"\n"
    "            ) != \"1\":  # ARC patch: preserve filenames\n"
    "                # Pick the first file as main.py\n"
    "                first_key = next(iter(files))\n"
    "                files[\"main.py\"] = files.pop(first_key)\n"
)

# ------------------------------------------------------------ prompts: seed policy
S1_OLD = "        extra = self._extras.get(name, \"\")  # ARC patch: extras for sub-prompts\n"
S1_NEW = (
    "        if __import__(\"os\").environ.get(\"ARC_KEEP_SEEDS\") == \"1\":  # ARC patch: seed policy\n"
    "            user_text = __import__(\"re\").sub(\n"
    "                r\"SEED ENFORCEMENT \\(MANDATORY[^\\n]*\\n(?:- [^\\n]*\\n)+\",\n"
    "                \"SEED POLICY: keep the seeds and the number of seeds defined by the existing code \"\n"
    "                \"(rb_config.SEEDS); never reduce the number of seeds and never hard-code them.\\n\",\n"
    "                user_text,\n"
    "            )\n"
) + S1_OLD


def patch(path: Path, pairs, marker: str) -> bool:
    if not path.is_file():
        print(f"ERRORE: non trovo {path}. Lancialo dalla root del repo.", file=sys.stderr)
        return False
    src = path.read_text(encoding="utf-8")
    if marker in src:
        print(f"[gia' applicata] {path.relative_to(ROOT)}")
        return True
    for old, _ in pairs:
        n = src.count(old)
        if n != 1:
            print(
                f"ERRORE in {path.relative_to(ROOT)}: ancora attesa 1 volta, trovata {n}:\n"
                f"{old[:90]!r}\nNon modifico nulla.",
                file=sys.stderr,
            )
            return False
    shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    for old, new in pairs:
        src = src.replace(old, new)
    path.write_text(src, encoding="utf-8")
    print(f"[applicata]      {path.relative_to(ROOT)}")
    return True


def main() -> int:
    ok = patch(CODEGEN, [(A1_OLD, A1_NEW), *GUARDS], MARK)
    ok = patch(MANAGER, [(M1_OLD, M1_NEW), (M2_OLD, M2_NEW)], "ARC patch: extras for sub-prompts") and ok
    ok = patch(
        EXECUTION,
        [(E1_OLD, E1_NEW), (E2_OLD, E2_NEW), (E3_OLD, E3_NEW), (E4_OLD, E4_NEW)],
        "ARC patch: stage13 refine",
    ) and ok
    ok = patch(EXECUTION, EXEC_MODES, "ARC patch: stage13 modes") and ok
    ok = patch(MANAGER, [(S1_OLD, S1_NEW)], "ARC patch: seed policy") and ok
    ok = patch(HELPERS, [(H1_OLD, H1_NEW)], "ARC patch: preserve filenames") and ok
    if REFINE_SRC.is_file():
        shutil.copy2(REFINE_SRC, REFINE_DST)
        print(f"[copiato]        {REFINE_DST.relative_to(ROOT)}")
    else:
        print("ATTENZIONE: _arc_refine.py non copiato", file=sys.stderr)
        ok = False
    if REPAIR_SRC.is_file() and REPAIR_DST.parent.is_dir():
        shutil.copy2(REPAIR_SRC, REPAIR_DST)
        print(f"[copiato]        {REPAIR_DST.relative_to(ROOT)}")
    else:
        print("ATTENZIONE: _stage12_repair.py non copiato", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
