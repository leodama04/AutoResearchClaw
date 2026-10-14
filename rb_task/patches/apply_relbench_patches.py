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
7. Cross-pass memory (config mode): the history of ALL evaluated configurations (earlier passes included) is shown to the LLM and used
   for de-duplication, and each new pass starts from the best configuration found so far (warm start).
8. ARC_METHOD_FILE: stage 13 writes an authoritative description of what was actually evaluated (settings changed, search size,
   confirmation numbers and paired statistics); it is appended to the analysis / decision / paper prompts. This stops the paper
   from describing methods that the code never implemented.
9. Prompts: ARC_KEEP_SEEDS=1 replaces the "exactly seeds = [0, 1, 2]" rule of the iterative_improve prompt.
10. 0.6.3 (after RUN-007): stage-13 repair prompts show the same files as the improve prompt (no vendored code: the prompt
   exceeded the context -> HTTP 400 -> stage failed); runtime repair only for real failures (not stderr warnings); an LLM
   error skips the attempt instead of failing the stage; the improve prompt shows the most recent attempts (upstream:
   run_summaries[:20]); the LLM client logs the body of HTTP 400 answers.

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
REPOCTX_SRC = HERE / "_repo_context.py"
REPOCTX_DST = ROOT / "researchclaw/pipeline/stage_impls/_repo_context.py"
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
W1_OLD = "    for iteration in range(1, max_iterations + 1):\n        # BUG-57: Check wall-clock time before starting a new iteration\n"
W1_NEW = (
    "    if _arc_state is not None and _arc_state.config_mode:  # ARC patch: stage13 modes (warm start)\n"
    "        try:\n"
    "            _ws = _arc.warm_start(_arc_state, best_files, best_metric, metric_direction)\n"
    "            if _ws is not None:\n"
    "                best_files, best_metric = _ws[\"files\"], _ws[\"metric\"]\n"
    "                best_version = \"experiment_v0/\"\n"
    "                _write_project(stage_dir / \"experiment_v0\", best_files)\n"
    "                log[\"iterations\"].append(_ws[\"record\"])\n"
    "                logger.warning(\n"
    "                    \"Stage 13: warm start from an earlier pass: %s (%.4f)\", _ws[\"overrides\"], best_metric\n"
    "                )\n"
    "        except Exception as _w_exc:  # noqa: BLE001\n"
    "            logger.warning(\"Stage 13: warm start failed: %s\", _w_exc)\n"
) + W1_OLD
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
D1_OLD = "        extra = self._extras.get(stage, \"\")\n"
D1_NEW = (
    "        extra = self._extras.get(stage, \"\")\n"
    "        if stage in __import__(\"os\").environ.get(  # ARC patch: ground truth about the method\n"
    "            \"ARC_METHOD_STAGES\",\n"
    "            \"result_analysis,research_decision,paper_outline,paper_draft,paper_revision,peer_review\",\n"
    "        ).split(\",\"):\n"
    "            try:\n"
    "                from researchclaw.pipeline.stage_impls._arc_refine import method_text\n"
    "\n"
    "                _gt = method_text()\n"
    "            except Exception:  # noqa: BLE001\n"
    "                _gt = \"\"\n"
    "            if _gt:\n"
    "                extra = (extra + \"\\n\\n\" if extra else \"\") + _gt\n"
)
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

# ------------------------------------------------------------ 0.5: literature + knowledge for code writing
LITERATURE = ROOT / "researchclaw/pipeline/stage_impls/_literature.py"
KNOW_SRC = HERE / "_arc_knowledge.py"
KNOW_DST = ROOT / "researchclaw/pipeline/stage_impls/_arc_knowledge.py"
SKILLS_SRC = HERE.parent / "skills"
SKILLS_DST = ROOT / ".claude" / "skills"

L1_OLD = '    year_min: int = queries_data.get("year_min", 2020)\n'
L1_NEW = L1_OLD + (
    "    try:  # ARC patch: literature queries (ARC_LIT_YEAR_MIN, ARC_LIT_QUERIES_FILE)\n"
    "        from researchclaw.pipeline.stage_impls._arc_knowledge import adjust_queries\n"
    "\n"
    "        queries, year_min = adjust_queries(queries, year_min)\n"
    "    except Exception:  # noqa: BLE001\n"
    "        pass\n"
)
L2_OLD = "    return StageResult(\n        stage=Stage.KNOWLEDGE_EXTRACT,\n        status=StageStatus.DONE,\n"
L2_NEW = (
    "    try:  # ARC patch: knowledge build (full-text implementation cards + official code)\n"
    "        from researchclaw.pipeline.stage_impls._arc_knowledge import build_knowledge\n"
    "\n"
    "        build_knowledge(run_dir, stage_dir, config, llm, _chat_with_prompt, logger)\n"
    "    except Exception as _k_exc:  # noqa: BLE001\n"
    "        logger.warning(\"Stage 6: implementation cards failed: %s\", _k_exc)\n"
) + L2_OLD

K3A_OLD = '        extra = self._extras.get(stage, "")\n'
K3A_NEW = K3A_OLD + (
    "        try:  # ARC patch: knowledge injection\n"
    "            from researchclaw.pipeline.stage_impls._arc_knowledge import knowledge_for\n"
    "\n"
    "            _kn = knowledge_for(stage)\n"
    "        except Exception:  # noqa: BLE001\n"
    "            _kn = \"\"\n"
    "        if _kn:\n"
    "            extra = (extra + \"\\n\\n\" if extra else \"\") + _kn\n"
)
K3B_OLD = '        extra = self._extras.get(name, "")  # ARC patch: extras for sub-prompts\n'
K3B_NEW = K3B_OLD + (
    "        try:  # ARC patch: knowledge injection (sub-prompts)\n"
    "            from researchclaw.pipeline.stage_impls._arc_knowledge import knowledge_for\n"
    "\n"
    "            _kn = knowledge_for(name)\n"
    "        except Exception:  # noqa: BLE001\n"
    "            _kn = \"\"\n"
    "        if _kn:\n"
    "            extra = (extra + \"\\n\\n\" if extra else \"\") + _kn\n"
)

G1_OLD = "            if metric_val is not None:\n                consecutive_no_metrics = 0\n"
G1_NEW = (
    "            if _arc_state is not None and metric_val is not None:  # ARC patch: knowledge gate\n"
    "                _ok2, _why2 = _arc.knowledge_gate(_arc_final_run, candidate_files, _arc_state)\n"
    "                if not _ok2:\n"
    "                    logger.warning(\"Stage 13 iteration %d: rejected (%s)\", iteration, _why2)\n"
    "                    iter_record[\"arc_rejected\"] = _why2\n"
    "                    iter_record[\"metric\"] = None\n"
    "                    metric_val = None\n"
) + G1_OLD
G2_OLD = "        if consecutive_no_metrics >= 3:\n"
G2_NEW = (
    "        if consecutive_no_metrics >= int(  # ARC patch: failure tolerance\n"
    "            __import__(\"os\").environ.get(\"ARC_MAX_NO_METRICS\", \"3\") or 3\n"
    "        ):\n"
)
G3_OLD = "        # BUG-57: Check wall-clock time before starting a new iteration\n"
G3_NEW = (
    "        if _arc is not None and _arc.past_deadline():  # ARC patch: global deadline\n"
    "            logger.warning(\"Stage 13: global deadline reached - stopping the refinement\")\n"
    "            log[\"stop_reason\"] = \"global_deadline\"\n"
    "            break\n"
) + G3_OLD

# Files the LLM cannot change and does not need to read in full (they are restored anyway): hide them from the
# stage-13 prompt to keep it inside the context window (e.g. the frozen official model).
H2_OLD = "        files_context = _files_to_context(best_files)\n"
H2_NEW = (
    "        files_context = _files_to_context(  # ARC patch: hide files from the prompt\n"
    "            {k: v for k, v in best_files.items()\n"
    "             if k not in [x.strip() for x in __import__(\"os\").environ.get(\"ARC_PROMPT_HIDE_FILES\", \"\").split(\",\")]}\n"
    "        )\n"
)

# 0.5.1: keep the END of stderr (the traceback), not the first 2000 characters (full of warnings)
S2_OLD = '                "stderr": rerun.stderr[:2000] if rerun.stderr else "",\n'
S2_NEW = '                "stderr": rerun.stderr[-4000:] if rerun.stderr else "",  # ARC patch: stderr tail\n'
S3_OLD = '                        "timed_out": rerun2.timed_out,\n                    }\n'
S3_NEW = ('                        "timed_out": rerun2.timed_out,\n'
          '                        "stderr": (rerun2.stderr or "")[-4000:],  # ARC patch: stderr after fix\n'
          '                    }\n')
# 0.5.1: warm start + cross-pass memory also in code mode
W2_OLD = "    if _arc_state is not None and _arc_state.config_mode:  # ARC patch: stage13 modes (warm start)\n"
W2_NEW = "    if _arc_state is not None:  # ARC patch: stage13 modes (warm start) [all modes]\n"

# 0.5.2: official code of the papers, vendored at stage 6, is part of the project from stage 10 on
V1_OLD = "            for _p in sorted(Path(_arc_seed_dir).glob(\"*.py\"))\n"
V1_NEW = ("            for _p in sorted(list(Path(_arc_seed_dir).glob(\"*.py\"))  # ARC patch: vendored code\n"
          "                             + list((run_dir / \"stage-06\" / \"vendor\").glob(\"vendor_*.py\")))\n")
H3_OLD = ('             if k not in [x.strip() for x in __import__(\"os\").environ.get(\"ARC_PROMPT_HIDE_FILES\", \"\").split(\",\")]}\n')
H3_NEW = ('             if not __import__(\"researchclaw.pipeline.stage_impls._arc_knowledge\",  # ARC patch: hide prefixes\n'
          '                               fromlist=[\"hidden_file\"]).hidden_file(k)}\n')

# 0.5.3: the runtime repair stored an unlabelled code block as main.py and skipped the guard
R1_OLD = ('                        repaired_files = dict(candidate_files)\n'
          '                        repaired_files["main.py"] = single\n')
R1_NEW = ('                        repaired_files = dict(candidate_files)\n'
          '                        repaired_files[  # ARC patch: repair target\n'
          '                            _arc.target_for_block(single, candidate_files) if _arc is not None else "main.py"\n'
          '                        ] = single\n')
R2_OLD = ('                    merged = dict(candidate_files)\n'
          '                    merged.update(repaired_files)\n'
          '                    candidate_files = merged\n')
R2_NEW = ('                    merged = dict(candidate_files)\n'
          '                    if _arc_state is not None:  # ARC patch: guard after repair\n'
          '                        repaired_files = _arc.retarget_repair(repaired_files, candidate_files, _arc_state.protected)\n'
          '                    merged.update(repaired_files)\n'
          '                    candidate_files = merged\n'
          '                    if _arc_state is not None:\n'
          '                        candidate_files, _g2 = _arc.guard_candidate(\n'
          '                            best_files, candidate_files, _arc_state.space, _arc_state.protected\n'
          '                        )\n')
# 0.5.3: noise-robust acceptance (second evaluation on other seeds before accepting an improvement)
RC_OLD = "                if _is_better(metric_val, best_metric) and (  # ARC patch: noise margin\n"
RC_NEW = (
    "                if (  # ARC patch: recheck before accepting\n"
    "                    _arc_state is not None and _arc.recheck_enabled()\n"
    "                    and _is_better(metric_val, best_metric)\n"
    "                    and _arc.margin_ok(metric_val, best_metric, metric_direction, _arc_state.margin)\n"
    "                ):\n"
    "                    _mv2 = _arc.recheck(metric_val, version_dir, stage_dir, iteration, config, create_sandbox,\n"
    "                                        metric_key, iter_record, _arc_state, logger)\n"
    "                    metric_val = _mv2 if _mv2 is not None else _arc.no_gain_value(best_metric, metric_direction)\n"
    "                    iter_record[\"metric\"] = _mv2\n"
) + RC_OLD

# 0.6: the upstream pipeline caps each refinement pass at 10 iterations (and makes at most 3 passes): a "24 h" run
# stopped after 30 iterations (~2 h). ARC_MAX_REFINE_ITERS lifts the cap; the global deadline stops the run.
C1_OLD = "    max_iterations = max(1, min(requested_iterations, 10))\n"
C1_NEW = ("    max_iterations = max(1, min(requested_iterations, int(  # ARC patch: iteration cap\n"
          "        __import__(\"os\").environ.get(\"ARC_MAX_REFINE_ITERS\", \"10\") or 10)))\n")
# 0.6: a candidate identical to the best version is not executed (saves ~2 min per attempt)
U1_OLD = ("            rerun = sandbox.run_project(\n"
          "                version_dir,\n"
          "                timeout_sec=config.experiment.time_budget_sec,\n"
          "            )\n")
U1_NEW = ("            rerun = (  # ARC patch: skip unchanged candidates\n"
          "                _arc.skipped_run()\n"
          "                if (_arc_state is not None and _arc.skip_run())\n"
          "                else sandbox.run_project(\n"
          "                    version_dir,\n"
          "                    timeout_sec=config.experiment.time_budget_sec,\n"
          "                )\n"
          "            )\n")

# 0.6.1: stage 3 discards the LLM's own search queries when its YAML string is malformed and uses pieces of the
# topic title instead; recover the LLM's queries from its answer (no human-written queries).
Q1_OLD = "    model_plan_parsed = plan is not None\n"
Q1_NEW = (
    "    if plan is None and llm is not None:  # ARC patch: rescue LLM queries\n"
    "        try:\n"
    "            from researchclaw.pipeline.stage_impls._arc_knowledge import rescue_plan\n"
    "\n"
    "            plan = rescue_plan(locals().get(\"payload\"), getattr(locals().get(\"resp\"), \"content\", \"\"), topic)\n"
    "        except Exception:  # noqa: BLE001\n"
    "            plan = None\n"
) + Q1_OLD

# 0.6.2: in code mode the editable model starts as the official model only (rb_model_minimal.py -> rb_model.py),
# so every alternative architecture must come from the papers the LLM found.
SF1_OLD = ('        if "main.py" in _arc_seed_files:\n'
           '            files = dict(_arc_seed_files)\n')
SF1_NEW = (
    '        for _pair in [x for x in _arc_os.environ.get("ARC_SEED_FILE_MAP", "").split(",") if "=" in x]:  # ARC patch: seed file map\n'
    '            _dst, _src = (_s.strip() for _s in _pair.split("=", 1))\n'
    '            if _src in _arc_seed_files:\n'
    '                _arc_seed_files[_dst] = _arc_seed_files.pop(_src)\n'
    '        _arc_seed_files.pop("rb_model_minimal.py", None)\n'
) + SF1_OLD


# ---------------------------------------------------------------------------------------------- 0.6.3
# N1. Repair prompts (validation + runtime) showed ALL project files, vendored official code included (190k characters
#     in RUN-007 -> the prompt exceeded the 65k-token context: HTTP 400 and the whole stage 13 failed). They now show the
#     same files as the improve prompt (vendored and frozen files are read-only; their API is in the knowledge block).
_VIS = '__import__("researchclaw.pipeline.stage_impls._arc_knowledge", fromlist=["visible_files"]).visible_files'
N1A_OLD = ('                issue_text=issue_text,\n'
           '                all_files_ctx=_files_to_context(candidate_files),\n')
N1A_NEW = ('                issue_text=issue_text,\n'
           f'                all_files_ctx=_files_to_context({_VIS}(candidate_files)),  # ARC patch: repair prompt files\n')
N1B_OLD = ('                    issue_text=runtime_issues,\n'
           '                    all_files_ctx=_files_to_context(candidate_files),\n')
N1B_NEW = ('                    issue_text=runtime_issues,\n'
           f'                    all_files_ctx=_files_to_context({_VIS}(candidate_files)),  # ARC patch: repair prompt files\n')
# N2. Runtime repair only when the run really failed (upstream: any "Warning" in stderr, i.e. every RelBench run).
N2_OLD = ("                else _detect_runtime_issues(rerun)\n"
          "            )\n")
N2_NEW = ("                else (_arc.repair_issues(rerun, metric_val, _detect_runtime_issues)  # ARC patch: repair only real failures\n"
          "                      if _arc_state is not None else _detect_runtime_issues(rerun))\n"
          "            )\n")
# N3. An LLM error (HTTP 400, server down, ...) no longer ends stage 13: the attempt is skipped and counted as an
#     attempt without metrics (ARC_MAX_NO_METRICS stops the loop if it keeps happening); a failed repair call keeps
#     the original result.
N3A_OLD = ("            raise\n"
           "        extracted_files = _extract_multi_file_blocks(response.content)\n")
N3A_NEW = ("            if _arc_state is None:  # ARC patch: LLM errors do not end the refinement\n"
           "                raise\n"
           "            consecutive_no_metrics += 1\n"
           "            logger.warning(\"Stage 13 iteration %d: LLM call failed (%s) - attempt skipped\", iteration, exc)\n"
           "            log[\"iterations\"].append({\"iteration\": iteration, \"llm_error\": str(exc)[:500],\n"
           "                                     \"metric\": None, \"improved\": False})\n"
           "            _write_refinement_log()\n"
           "            if consecutive_no_metrics >= int(__import__(\"os\").environ.get(\"ARC_MAX_NO_METRICS\", \"3\") or 3):\n"
           "                log[\"stop_reason\"] = \"consecutive_no_metrics\"\n"
           "                break\n"
           "            continue\n"
           "        extracted_files = _extract_multi_file_blocks(response.content)\n")
N3B_OLD = ("                raise\n"
           "            candidate_files[\"main.py\"] = _extract_code_block(repair_response.content)\n")
N3B_NEW = ("                if _arc_state is None:  # ARC patch: LLM errors do not end the refinement (repair)\n"
           "                    raise\n"
           "                logger.warning(\"Stage 13 iteration %d: repair LLM call failed (%s)\", iteration, exc)\n"
           "                repair_response = None\n"
           "            if repair_response is not None:\n"
           "                candidate_files[\"main.py\"] = _extract_code_block(repair_response.content)\n")
N3C_OLD = ("                    raise\n"
           "                repaired_files = _extract_multi_file_blocks(repair_resp.content)\n"
           "                if not repaired_files:\n")
N3C_NEW = ("                    if _arc_state is None:  # ARC patch: LLM errors do not end the refinement (runtime repair)\n"
           "                        raise\n"
           "                    logger.warning(\"Stage 13 iteration %d: runtime-repair LLM call failed (%s) - repair skipped\",\n"
           "                                   iteration, exc)\n"
           "                    iter_record[\"repair_llm_error\"] = str(exc)[:300]\n"
           "                    repair_resp = None\n"
           "                repaired_files = (_extract_multi_file_blocks(repair_resp.content)\n"
           "                                  if repair_resp is not None else {})\n"
           "                if not repaired_files and repair_resp is not None:\n")
# N4. The improve prompt showed run_summaries[:20] (the FIRST 20 entries): after ~19 attempts the LLM stopped seeing
#     the outcome of its latest attempts. Now: stage-12 summaries + digest of older attempts + the most recent ones.
N4_OLD = "            run_summaries=chr(10).join(run_summaries[:20]),\n"
N4_NEW = ("            run_summaries=chr(10).join(  # ARC patch: recent history\n"
          "                _arc.summaries_for_prompt(run_summaries) if _arc_state is not None else run_summaries[:20]\n"
          "            ),\n")
EXEC_063 = [(N1A_OLD, N1A_NEW), (N1B_OLD, N1B_NEW), (N2_OLD, N2_NEW), (N3A_OLD, N3A_NEW), (N3B_OLD, N3B_NEW),
            (N3C_OLD, N3C_NEW), (N4_OLD, N4_NEW)]
# N5. LLM client: log the body of an HTTP 400 (llama-server says why, e.g. "the request exceeds the available context
#     size"); upstream read it and threw it away.
CLIENT = ROOT / "researchclaw/llm/client.py"
N5_OLD = ("                    if not _transient_400:\n"
          "                        raise  # Genuine bad request — don't retry\n")
N5_NEW = ("                    if not _transient_400:\n"
          "                        logger.warning(\"LLM HTTP 400 from %s: %s\", model, body[:400])  # ARC patch: log 400 body\n"
          "                        raise  # Genuine bad request — don't retry\n")


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
    ok = patch(EXECUTION, [(W1_OLD, W1_NEW)], "ARC patch: stage13 modes (warm start)") and ok
    ok = patch(MANAGER, [(S1_OLD, S1_NEW)], "ARC patch: seed policy") and ok
    ok = patch(MANAGER, [(D1_OLD, D1_NEW)], "ARC patch: ground truth about the method") and ok
    ok = patch(HELPERS, [(H1_OLD, H1_NEW)], "ARC patch: preserve filenames") and ok
    ok = patch(LITERATURE, [(L1_OLD, L1_NEW)], "ARC patch: literature queries") and ok
    ok = patch(LITERATURE, [(L2_OLD, L2_NEW)], "ARC patch: knowledge build") and ok
    ok = patch(MANAGER, [(K3A_OLD, K3A_NEW)], "ARC patch: knowledge injection\n") and ok
    ok = patch(MANAGER, [(K3B_OLD, K3B_NEW)], "ARC patch: knowledge injection (sub-prompts)") and ok
    ok = patch(EXECUTION, [(G1_OLD, G1_NEW)], "ARC patch: knowledge gate") and ok
    ok = patch(EXECUTION, [(G2_OLD, G2_NEW)], "ARC patch: failure tolerance") and ok
    ok = patch(EXECUTION, [(G3_OLD, G3_NEW)], "ARC patch: global deadline") and ok
    ok = patch(EXECUTION, [(H2_OLD, H2_NEW)], "ARC patch: hide files from the prompt") and ok
    ok = patch(EXECUTION, [(S2_OLD, S2_NEW)], "ARC patch: stderr tail") and ok
    ok = patch(EXECUTION, [(S3_OLD, S3_NEW)], "ARC patch: stderr after fix") and ok
    ok = patch(EXECUTION, [(W2_OLD, W2_NEW)], "[all modes]") and ok
    ok = patch(CODEGEN, [(V1_OLD, V1_NEW)], "ARC patch: vendored code") and ok
    ok = patch(EXECUTION, [(R1_OLD, R1_NEW)], "ARC patch: repair target") and ok
    ok = patch(EXECUTION, [(R2_OLD, R2_NEW)], "ARC patch: guard after repair") and ok
    ok = patch(EXECUTION, [(RC_OLD, RC_NEW)], "ARC patch: recheck before accepting") and ok
    ok = patch(EXECUTION, [(C1_OLD, C1_NEW)], "ARC patch: iteration cap") and ok
    ok = patch(EXECUTION, [(U1_OLD, U1_NEW)], "ARC patch: skip unchanged candidates") and ok
    ok = patch(LITERATURE, [(Q1_OLD, Q1_NEW)], "ARC patch: rescue LLM queries") and ok
    ok = patch(CODEGEN, [(SF1_OLD, SF1_NEW)], "ARC patch: seed file map") and ok
    ok = patch(EXECUTION, [(H3_OLD, H3_NEW)], "ARC patch: hide prefixes") and ok
    ok = patch(EXECUTION, EXEC_063, "ARC patch: repair prompt files") and ok
    ok = patch(CLIENT, [(N5_OLD, N5_NEW)], "ARC patch: log 400 body") and ok
    if KNOW_SRC.is_file():
        shutil.copy2(KNOW_SRC, KNOW_DST)
        print(f"[copiato]        {KNOW_DST.relative_to(ROOT)}")
    if SKILLS_SRC.is_dir():  # project skills: loaded automatically by the pipeline's SkillRegistry
        for skill in sorted(p for p in SKILLS_SRC.iterdir() if (p / "SKILL.md").is_file()):
            dst = SKILLS_DST / skill.name
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(skill / "SKILL.md", dst / "SKILL.md")
            print(f"[skill]          .claude/skills/{skill.name}")
    if REPOCTX_SRC.is_file() and REPOCTX_DST.parent.is_dir():  # fix: code excerpts no longer skip examples/
        shutil.copy2(REPOCTX_SRC, REPOCTX_DST)
        print(f"[copiato]        {REPOCTX_DST.relative_to(ROOT)}")
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
