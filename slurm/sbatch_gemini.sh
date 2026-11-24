#!/bin/bash
#SBATCH --job-name=arc-gemini
#SBATCH --output=%x_%j.out
# 3-hour unguided run on driver-top3 with Gemini as the LLM, on the GPU that SLURM assigns to the job.
# The GPU is used only by the experiments (the LLM is the Gemini API).
#
# From ~/AutoResearchClaw, on branch gemini_api, after the Gemini test:
#   read -s -p "Chiave Gemini: " GEMINI_API_KEY; echo; export GEMINI_API_KEY
#   sbatch --nodelist=faretra -N 1 --gres=gpu:nvidia_geforce_rtx_3090:1 --time=<limit> sbatch_gemini.sh
#   unset GEMINI_API_KEY
# sbatch passes the key to the job through the environment: it is never written in a file.
# Follow it with:  tail -f arc-gemini_<jobid>.out      Stop it with:  scancel <jobid>
set -uo pipefail
ARC_DIR="${ARC_DIR:-$HOME/AutoResearchClaw}"
cd "$ARC_DIR" || { echo "ERROR: $ARC_DIR not found"; exit 1; }
echo "host: $(hostname)   job: ${SLURM_JOB_ID:-none}   CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo "git: $(git rev-parse --abbrev-ref HEAD) $(git rev-parse --short HEAD)"
[ -n "${GEMINI_API_KEY:-}" ] || { echo "ERROR: GEMINI_API_KEY is not in the job environment: export it before sbatch"; exit 2; }
[ -n "${CUDA_VISIBLE_DEVICES:-}" ] || { echo "ERROR: no GPU assigned by SLURM (submit with --gres=gpu:...)"; exit 2; }
[ -f config.arc.relbench.code.gemini.yaml ] || { echo "ERROR: Gemini patch missing: git checkout gemini_api"; exit 2; }
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv
mkdir -p "$HOME/no_llms"   # no local model is needed: an empty folder is mounted as /llms

DOCKER_GPUS="\"device=$CUDA_VISIBLE_DEVICES\"" \
LLMS_DIR="$HOME/no_llms" \
ARC_DIR="$ARC_DIR" \
ARC_LLM=gemini \
ARC_DEADLINE_HOURS=3 \
    ./run.sh relbench
