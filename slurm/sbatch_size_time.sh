#!/bin/bash
#SBATCH --job-name=arc-size-time
#SBATCH --output=%x_%j.out
# Numbers for slide 2: parameters of the official RelBench model and seconds per epoch,
# on the GPU that SLURM assigns to the job. Writes nothing in the repository.
#
# From ~/AutoResearchClaw:
#   sbatch --nodelist=faretra -N 1 --gres=gpu:nvidia_geforce_rtx_3090:1 sbatch_size_time.sh
# Output: arc-size-time_<jobid>.out in the folder you submitted from.
set -uo pipefail
ARC_DIR="${ARC_DIR:-$HOME/AutoResearchClaw}"
cd "$ARC_DIR" || { echo "ERROR: $ARC_DIR not found"; exit 1; }
echo "host: $(hostname)   job: ${SLURM_JOB_ID:-none}   CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}   git: $(git rev-parse --short HEAD)"
[ -n "${CUDA_VISIBLE_DEVICES:-}" ] || { echo "ERROR: no GPU assigned by SLURM (submit with --gres=gpu:...)"; exit 2; }
[ -f rb_task/tools/model_size_time.py ] || { echo "ERROR: rb_task/tools/model_size_time.py missing"; exit 2; }
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv

# Same logic as run.sh: with rootless Docker / userns-remap --user must not be passed.
USER_FLAGS="--user $(id -u):$(id -g)"
docker info --format '{{.SecurityOptions}}' 2>/dev/null | grep -qE 'rootless|userns' && USER_FLAGS=""

# shellcheck disable=SC2086
docker run --rm --init \
    --gpus '"device='"$CUDA_VISIBLE_DEVICES"'"' --memory=30g \
    $USER_FLAGS -e HOME=/tmp --shm-size=8g \
    -v "$ARC_DIR":/app -v "$ARC_DIR/docker-entrypoint.sh":/usr/local/bin/docker-entrypoint.sh:ro \
    -e ARC_NO_LLM=1 -e RB_RECIPE=tuned -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    arc-relbench:latest \
    bash -c 'cd /app && python3 rb_task/tools/model_size_time.py --tasks driver-top3,driver-dnf,driver-position' \
    2>&1 | grep -vE "Embedding raw data|UserWarning|to_datetime|warnings\.warn\("
