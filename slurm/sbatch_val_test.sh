#!/bin/bash
#SBATCH --job-name=arc-val-test
#SBATCH --output=%x_%j.out
# Data-only comparison of the validation and test splits of rel-f1 (no model, no GPU, ~1-2 minutes).
#
# From ~/AutoResearchClaw (the script must be in rb_task/tools/):
#   sbatch --nodelist=faretra -N 1 sbatch_val_test.sh
# If the cluster refuses jobs without a GPU, add: --gres=gpu:nvidia_geforce_rtx_3090:1
# Output: arc-val-test_<jobid>.out in the folder you submitted from.
set -uo pipefail
ARC_DIR="${ARC_DIR:-$HOME/AutoResearchClaw}"
cd "$ARC_DIR" || { echo "ERROR: $ARC_DIR not found"; exit 1; }
echo "host: $(hostname)   job: ${SLURM_JOB_ID:-none}   git: $(git rev-parse --short HEAD)"
[ -f rb_task/tools/val_test_analysis.py ] || { echo "ERROR: rb_task/tools/val_test_analysis.py missing"; exit 2; }

# Same logic as run.sh: with rootless Docker / userns-remap --user must not be passed.
USER_FLAGS="--user $(id -u):$(id -g)"
docker info --format '{{.SecurityOptions}}' 2>/dev/null | grep -qE 'rootless|userns' && USER_FLAGS=""

# shellcheck disable=SC2086
docker run --rm --init --memory=16g \
    $USER_FLAGS -e HOME=/tmp \
    -v "$ARC_DIR":/app -v "$ARC_DIR/docker-entrypoint.sh":/usr/local/bin/docker-entrypoint.sh:ro \
    -e ARC_NO_LLM=1 \
    arc-relbench:latest \
    bash -c 'cd /app && python3 rb_task/tools/val_test_analysis.py --tasks driver-top3,driver-dnf' \
    2>&1 | grep -vE "UserWarning|to_datetime|warnings\.warn\("
