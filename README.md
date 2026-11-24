# AutoResearchClaw on RelBench with a local LLM

Code of the bachelor thesis **Autonomous Research with Local LLM Agents: Iteratively Improving Graph Neural Networks on
Relational Databases**. Leonardo D'Amario, Department of Computer Science and Engineering, University of Bologna.
Bachelor's Degree in Engineering and Computer Science, A.A. 2025–2026. Supervisor: Prof. Gianluca Moro. Co-supervisors:
Dr. Giacomo Frisoni and Dr. Lorenzo Molfetta.

This branch (`thesis`) is a fork of [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw), whose original README
is in [`docs/README_upstream.md`](docs/README_upstream.md). The pipeline is adapted so that an agent driven by a **local LLM**
tries to improve the official RelBench graph neural network on the `rel-f1` database (tasks `driver-top3` and `driver-dnf`).
The LLM is Qwen3.6-35B-A3B in 4 bits, served by llama.cpp on the same GPU that trains the models. An optional mode uses
**Gemini 3.1 Pro** through its API.

Branches: `thesis` is the final code. `local_llm` and `gemini_api` are the development branches it comes from, kept for
history. `main` is not used by the thesis.

## What is where

| Path | Content |
|---|---|
| `researchclaw/` | The 23-stage pipeline with the changes of the thesis: papers read in full and turned into implementation cards (`pipeline/stage_impls/_arc_knowledge.py`), refinement loop with the acceptance gates (`_arc_refine.py`), automatic repair of crashed experiments (`_stage12_repair.py`). |
| `rb_task/seed_project/` | The official RelBench GNN split into small files: the project the agent edits. |
| `rb_task/task_spec/` | The task description given to the LLM. |
| `rb_task/tools/` | Evaluations and analyses run without the LLM (transfer, RelGNN checkpoints and training, reproducibility checks, run reports, the scripts of chapters 4 and 5, the validation/test analysis). |
| `rb_task/patches/`, `rb_task/tests/`, `rb_task/VERSION` | Kit patches (already applied in this branch), smoke tests and build-time prefetch, kit version. |
| `config.arc.relbench*.yaml` | Pipeline configurations: code mode, configuration mode, and their Gemini variants. |
| `Dockerfile.arc-relbench` | The image of every experiment of the thesis: llama.cpp with CUDA, the pipeline, the RelBench stack and the `rel-f1` data. |
| `Dockerfile.arc-llama` | Generic image of the original pipeline (`./run.sh build`, `./run.sh run`). It is not needed for RelBench. |
| `run.sh`, `docker-entrypoint.sh` | Every command. `./run.sh` without arguments prints the list. |
| `slurm/` | The SLURM job scripts used on the lab cluster. |
| `docs/runs/` | One report per run (RUN-000 … RUN-018), the automatic reports (`RUN-NNN_auto.md`), a manifest of every `./run.sh` command (`_manifests/`) and the cross-run analyses. Start from [`docs/runs/README.md`](docs/runs/README.md). |
| `docs/env/` | `pip freeze` of the image on the two nodes used (moro43 and faretra). |
| `README_RELBENCH.md` | Notes of the kit: order of the checks, variables, known problems. |

The reports in `docs/runs/` and the kit notes are in Italian; the thesis is in English.

## Requirements

- **GPU.** Linux with an NVIDIA GPU and a driver that supports CUDA 12.8 (≥ 570). With the local LLM the GPU must hold Qwen
  (about 23 GB with a 65,536-token context) and the experiments (about 4.5 GB). The thesis used an RTX 5090 with 32 GB; with
  Gemini, an RTX 3090 with 24 GB was enough.
- **Docker** with GPU support. Rootless Docker works: `run.sh` detects it.

## Setup

```bash
git clone -b thesis https://github.com/leodama04/AutoResearchClaw.git
cd AutoResearchClaw
export ARC_DIR="$PWD"        # run.sh defaults to /home/damario/AutoResearchClaw
```

1. **Results of the thesis.** This step is optional; it is needed only to re-analyse the runs of the thesis. Extract the
   archive `AutoResearchClaw_data.zip` in the root of the repository:
   ```bash
   unzip AutoResearchClaw_data.zip -d "$ARC_DIR"
   ```
   It creates `artifacts/` and `data/`. `artifacts/` is ignored by git and is the folder where `run.sh` writes and reads runs and
   checkpoints. The archive is described [below](#data-archive).
2. **Model weights.** This step is for the local LLM only. Put `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` in a folder and pass that folder
   as `LLMS_DIR`. The file is the Unsloth dynamic 4-bit quantisation of Qwen3.6-35B-A3B, from Hugging Face. `LLMS_DIR` defaults to
   `/llms`, the shared model folder of the lab nodes.
3. **Image.** It compiles llama.cpp and downloads relbench 1.1.0 with the `rel-f1` data and the GloVe text encoder.
   `CUDA_ARCHS` is 120 for an RTX 5090 and 86 for an RTX 3090.
   ```bash
   CUDA_ARCHS=120 ./run.sh build-relbench
   ```
4. **Checks without the LLM.** These must work before any run:
   ```bash
   ./run.sh smoke        # the GNN on fake data
   ./run.sh baseline     # the official RelBench model on rel-f1: the number to beat
   ```

## Running the agent

**Local LLM**, as in the runs of the thesis:

```bash
ARC_DEADLINE_HOURS=24 ./run.sh relbench                      # driver-top3, code mode
RB_TASK=driver-dnf ARC_DEADLINE_HOURS=24 ./run.sh relbench   # driver-dnf
ARC_SEARCH_MODE=config ./run.sh relbench                     # search over configurations only (RUN-003)
```

With the current kit (0.6.11) the pipeline runs in the unguided code mode used from RUN-007 on. The guided runs (RUN-004 to
RUN-006) used earlier kit versions; their reports give the details.

**Gemini 3.1 Pro**, as in RUN-018. The keys are read without echo and passed only as environment variables: never write them in
a file of the repository.

```bash
read -s -p "Gemini key: " GEMINI_API_KEY; echo; export GEMINI_API_KEY
read -s -p "OpenAlex key (optional): " OPENALEX_API_KEY; echo; export OPENALEX_API_KEY
./run.sh gemini-test
mkdir -p ~/no_llms
ARC_LLM=gemini ARC_MAX_TOKENS_MULT=6 ARC_MAX_TOKENS_CAP=49152 ARC_DEADLINE_HOURS=3 LLMS_DIR=~/no_llms ./run.sh relbench
```

On a SLURM cluster, export the keys and `ARC_MAX_TOKENS_MULT=6 ARC_MAX_TOKENS_CAP=49152`, then submit
[`slurm/sbatch_gemini.sh`](slurm/sbatch_gemini.sh); its header has the full command.

**What a run leaves behind.**
- Every `./run.sh` command writes a manifest in `docs/runs/_manifests/`, with the date, command, kit version, commit, variables
  and GPU.
- A pipeline run ends in `artifacts/rc-<date>-<time>-<hash>/`.
- `./run.sh report artifacts/rc-... RUN-NNN` writes the automatic report of a run in `docs/runs/`.

## Reproducing the thesis

The exact command of every run is in its manifest and in its report in `docs/runs/`.

| Experiment | Runs | Command |
|---|---|---|
| Preliminary sweep and confirmation | RUN-000, RUN-002 | `./run.sh sweep` (variables in the reports) |
| Pipeline runs with Qwen | RUN-001, RUN-003 … RUN-008, RUN-011 | `./run.sh relbench` |
| Official RelGNN checkpoints | RUN-009 | `./run.sh relgnn-ckpt` |
| A run's final model on the other tasks | RUN-010, RUN-013 | `./run.sh transfer --projects artifacts/rc-... --tasks driver-top3,driver-dnf,driver-position` |
| RelGNN with the authors' settings | RUN-012 | `./run.sh relgnn-train --epochs 10,30` |
| Why the baselines change between runs | RUN-014, RUN-015 | `./run.sh repro-check`, `./run.sh repro-stypes` |
| Ablation of RUN-004 and column-type variants (chapter 5) | RUN-016, RUN-017 | `rb_task/tools/ch5_runs.sh`, then `ch5_runs_2.sh` (see the reports) |
| Pipeline run with Gemini | RUN-018 | `slurm/sbatch_gemini.sh` |

**Scripts without the LLM** run in the image with `ARC_NO_LLM=1`. Add `--gpus all` for the ones that train models, and
`--user "$(id -u):$(id -g)"` if Docker is not rootless:

```bash
docker run --rm --init -e HOME=/tmp -e ARC_NO_LLM=1 -v "$ARC_DIR":/app arc-relbench:latest \
    python3 /app/rb_task/tools/<script>.py
```

| Script | What it prints |
|---|---|
| `model_size_time.py` | parameters and seconds per epoch of the RelBench models (GPU; [`slurm/sbatch_size_time.sh`](slurm/sbatch_size_time.sh)) |
| `info_cap4.py` | tables and splits of `rel-f1` used in chapter 4 (output in `docs/runs/info_cap4.txt`) |
| `val_test_analysis.py` | validation against test, data only (CPU; output in `docs/runs/ANALISI_val_test_2026-11-19.md`) |
| `tool_stats.py` | papers, official code and attempts of every run (`./run.sh tool-stats`) |

## Data archive

`AutoResearchClaw_data.zip` is not on GitHub. It is kept on the lab node faretra (137.204.107.40), in the home of `damario`,
next to this repository. Extract it in the root of the repository.

| Folder | Content |
|---|---|
| `artifacts/rc-*` | Every pipeline run (RUN-001 … RUN-011, RUN-018 and the test runs before them): the output of each stage, every attempt of the refinement loop (`stage-13*/experiment_vN/`), refinement logs, final confirmations and the generated papers. |
| `artifacts/transfer_*`, `relgnn_train_*`, `repro_*`, `repro_stypes_*`, `ch5_*` | The runs without the LLM (RUN-010 … RUN-017). |
| `artifacts/relgnn_checkpoints/` | The official RelGNN checkpoints of RUN-009. `./run.sh relgnn-ckpt` can download them again. |
| `artifacts/logs/` | SLURM outputs and token-usage logs of the Gemini runs, the archives of the chapter-5 results and `sweep_results.json`. |
| `data/relbench_cache/` | The `rel-f1` database and task tables used by every run, copied from `/opt/cache/relbench` in the image (relbench 1.1.0). They are kept because some files on the RelBench server changed after the release (see `README_RELBENCH.md`). |

Intermediate files were removed before archiving: Python caches, caches of the prepared data (`*/cache/rel-f1/materialized`)
and the git metadata of cloned reference repositories.

## Notes

- **Test metrics.** They are computed once per model for the final report, and removed from everything the LLM reads.
- **Keys.** No key or token is stored in the repository.
- **License.** MIT, as the original AutoResearchClaw (Aiming Lab); see `LICENSE`.
