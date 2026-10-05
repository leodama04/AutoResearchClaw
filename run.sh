#!/usr/bin/env bash
# Uso:
#   Immagine generica (arc-llama):
#     ./run.sh build
#     ./run.sh run "<topic>"
#     ./run.sh shell
#     ./run.sh exec <comando...>          (comando singolo nel container)
#   RelBench (immagine arc-relbench):
#     ./run.sh build-relbench
#     ./run.sh smoke                      (test di fumo del GNN su dati finti, senza LLM)
#     ./run.sh baseline                   (GNN ufficiale RelBench + seed: il numero da battere, senza LLM)
#     WITH_LLM=1 ./run.sh baseline        (idem, con Qwen caricato: misura la VRAM davvero disponibile)
#     LLAMA_CTX=65536 ./run.sh vram       (VRAM occupata da Qwen e VRAM rimasta libera)
#     ./run.sh sweep                      (senza LLM, ~10 min: ricette di addestramento/taglia/operatore, correlazione val-test)
#     RB_SWEEP_MODE=arch ./run.sh sweep   (idem, ma varianti ARCHITETTURALI con ricetta fissa 'tuned')
#     RB_SWEEP_MODE=arch RB_SWEEP_ONLY="aggr=max,transformer" RB_SWEEP_SEEDS=10 RB_SWEEP_SEED_OFFSET=100 ./run.sh sweep
#                                         (conferma dei vincitori su semi NUOVI; RB_SHOW_WARNINGS=1 per vedere i warning)
#     ./run.sh report artifacts/rc-XXXX [NOME]   (rapporto automatico di una run in docs/runs/)
#     ./run.sh relbench ["<topic>"]       (pipeline completa fino al paper; RB_RECIPE=official per la ricetta originale; ARC_SEARCH_MODE=code per far riscrivere il codice all'LLM)
set -euo pipefail

ARC_DIR="${ARC_DIR:-/home/damario/AutoResearchClaw}"
LLMS_DIR="${LLMS_DIR:-/llms}"
IMAGE="${IMAGE:-arc-llama:latest}"
RB_IMAGE="${RB_IMAGE:-arc-relbench:latest}"
CUDA_ARCHS="${CUDA_ARCHS:-120}"   # RTX 5090 (Blackwell)

TTY_FLAGS=""
[ -t 0 ] && [ -t 1 ] && TTY_FLAGS="-it"

# Con Docker rootless / userns-remap, root nel container == il tuo utente sull'host:
# passare --user romperebbe i permessi sulla cartella montata.
USER_FLAGS="--user $(id -u):$(id -g)"
if docker info --format '{{.SecurityOptions}}' 2>/dev/null | grep -qE 'rootless|userns'; then
    USER_FLAGS=""
fi

EXTRA_DOCKER_ARGS=()

# Tracciamento delle run: scrive un manifest (data, comando, versione del kit, commit, variabili, GPU) in docs/runs/_manifests/.
# Non deve MAI interrompere il comando: gira in una subshell senza `set -e` e ogni errore viene ignorato.
write_manifest() {
    (
        set +e +o pipefail
        local label="$1"; shift
        local dir="$ARC_DIR/docs/runs/_manifests"
        mkdir -p "$dir" 2>/dev/null || exit 0
        local f="$dir/$(date +%Y%m%d-%H%M%S)_${label}.txt"
        {
            echo "date: $(date -Is)"
            echo "command: ./run.sh $label $*"
            echo "kit: $(cat "$ARC_DIR/rb_task/VERSION" 2>/dev/null || echo unknown)"
            echo "git: $(cd "$ARC_DIR" && git rev-parse --short HEAD 2>/dev/null || echo n/a)$(cd "$ARC_DIR" && git diff --quiet 2>/dev/null || echo ' (uncommitted changes)')"
            echo "host: $(hostname)"
            echo "gpu: $(nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>/dev/null | head -1)"
            echo "env:"
            env | grep -E '^(ARC_|RB_|LLAMA_)' | sort | sed 's/^/  /'
        } > "$f" 2>/dev/null
        echo "[manifest] $f" >&2
    ) || true
}

docker_run() {
    # shellcheck disable=SC2086
    docker run --rm $TTY_FLAGS --init --gpus all \
        $USER_FLAGS -e HOME=/tmp \
        --shm-size=8g \
        -v "$ARC_DIR":/app \
        -v "$LLMS_DIR":/llms:ro \
        -v "$ARC_DIR/docker-entrypoint.sh":/usr/local/bin/docker-entrypoint.sh:ro \
        -e LLAMACPP_API_KEY=none \
        -e LLAMA_LOG_FILE=/app/llama-server.log \
        -e LLAMA_EXTRA_ARGS -e LLAMA_CTX -e LLAMA_NGL -e LLAMA_ENABLE_THINKING \
        -e ARC_MAX_TOKENS_MULT -e ARC_MAX_TOKENS_CAP -e ARC_STAGE12_REPAIRS \
        -e RB_DATASET -e RB_TASK -e RB_TIME_BUDGET_SEC -e RB_GPU_MEM_BUDGET_GB -e RB_NODE_BUDGET_SCALE -e RB_RECIPE -e RB_SWEEP_MODE -e RB_SWEEP_SEEDS -e RB_SWEEP_DEEP -e RB_SWEEP_RECIPE_JSON -e RB_SWEEP_ONLY -e RB_SWEEP_SEED_OFFSET -e RB_SHOW_WARNINGS \
        -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
        -e S2_API_KEY -e GITHUB_TOKEN -e OPENALEX_API_KEY -e TAVILY_API_KEY_UNSET \
        ${EXTRA_DOCKER_ARGS[@]+"${EXTRA_DOCKER_ARGS[@]}"} \
        "$IMAGE" "$@"
}

DEFAULT_RB_TOPIC="Improving graph neural networks for relational deep learning on RelBench: architecture and feature-encoding modifications of the official GraphSAGE baseline on rel-f1 driver-top3 (binary classification)"

case "${1:-}" in
    build)
        cd "$ARC_DIR"
        docker build -f Dockerfile.arc-llama \
            --build-arg CUDA_ARCHS="$CUDA_ARCHS" \
            -t "$IMAGE" .
        ;;
    run)
        TOPIC="${2:-Effect of dropout rate on overfitting in small neural networks}"
        docker_run researchclaw run --config config.arc.yaml \
            --topic "$TOPIC" --auto-approve
        ;;
    shell)
        docker_run bash
        ;;
    exec)
        shift
        docker_run "$@"
        ;;

    build-relbench)
        cd "$ARC_DIR"
        docker build -f Dockerfile.arc-relbench \
            --build-arg CUDA_ARCHS="$CUDA_ARCHS" \
            -t "$RB_IMAGE" .
        ;;
    smoke)
        write_manifest smoke
        IMAGE="$RB_IMAGE"
        EXTRA_DOCKER_ARGS=(-e ARC_NO_LLM=1)
        docker_run bash -c 'cd /app && python3 rb_task/tests/test_loader.py && python3 rb_task/tests/test_fanouts.py && python3 rb_task/tests/test_microbatch.py && python3 rb_task/tests/test_sweep.py && python3 rb_task/tests/test_refine_modes.py && python3 rb_task/tests/test_stage13_config_mode.py && python3 rb_task/tests/smoke_fake.py && python3 rb_task/tests/smoke_main_fake.py && RB_RECIPE=tuned python3 rb_task/tests/smoke_main_fake.py'
        ;;
    baseline)
        write_manifest baseline
        IMAGE="$RB_IMAGE"
        # WITH_LLM=1 ./run.sh baseline  -> avvia anche Qwen: misura la VRAM libera nelle condizioni reali
        if [ "${WITH_LLM:-0}" = "1" ]; then
            export LLAMA_CTX="${LLAMA_CTX:-65536}"
        else
            EXTRA_DOCKER_ARGS=(-e ARC_NO_LLM=1)
        fi
        docker_run bash -c '
            set -e
            DS="${RB_DATASET:-rel-f1}"; TK="${RB_TASK:-driver-top3}"
            echo "=== 1) GNN ufficiale RelBench (examples/gnn_node.py): $DS / $TK ==="
            cd /opt/relbench/examples
            python3 gnn_node.py --dataset "$DS" --task "$TK" --cache_dir /tmp/rb_examples 2>&1 \
                | grep -E "^Epoch|Best|Error|Traceback" | tail -20
            echo
            echo "=== 2) Seed project: baseline_graphsage vs proposed (10 semi) ==="
            W=$(mktemp -d)
            cp /app/rb_task/seed_project/*.py "$W"/
            cp /app/researchclaw/experiment/harness_template.py "$W"/experiment_harness.py
            cd "$W" && python3 main.py 2>&1 | grep -vE "^\s+epoch=|Embedding raw data"
        '
        ;;
    vram)
        # Quanta VRAM occupa Qwen con questa configurazione e quanta ne resta?
        #   LLAMA_CTX=65536 ./run.sh vram
        #   LLAMA_CTX=65536 LLAMA_EXTRA_ARGS="--cache-type-k q8_0 --cache-type-v q8_0 --n-cpu-moe 8" ./run.sh vram
        IMAGE="$RB_IMAGE"
        docker_run bash -c 'sleep 3
            echo "== GPU =="; nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv
            echo; echo "== processi sulla GPU (il tuo e /opt/llama/llama-server; gli altri sono di altri utenti) =="
            nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
            echo; echo "Per gli esperimenti servono ~4.5 GB liberi (baseline: picco 3.9 GB + contesto CUDA)."'
        ;;
    sweep)
        # Senza LLM: quanto e' affidabile la validazione come guida? (config diverse x semi, correlazione val-test)
        write_manifest sweep
        IMAGE="$RB_IMAGE"
        if [ "${WITH_LLM:-0}" = "1" ]; then
            export LLAMA_CTX="${LLAMA_CTX:-65536}"
        else
            EXTRA_DOCKER_ARGS=(-e ARC_NO_LLM=1)
        fi
        docker_run bash -c 'cd /app && RB_SEED_DIR=/app/rb_task/seed_project python3 rb_task/tools/sweep.py 2>&1 | if [ "${RB_SHOW_WARNINGS:-0}" = 1 ]; then cat; else grep -vE "^\s+epoch=|Embedding raw data|UserWarning|ser = pd.to_datetime|^\s+warnings\.warn\("; fi'
        ;;
    report)
        # ./run.sh report artifacts/rc-XXXX [NOME]   -> docs/runs/<NOME>_auto.md (fatti letti dai file della run)
        RUN_DIR="${2:?uso: ./run.sh report <cartella-della-run> [nome]}"
        NAME="${3:-$(basename "$RUN_DIR")}"
        MAN="$(ls -t "$ARC_DIR"/docs/runs/_manifests/*_relbench.txt 2>/dev/null | head -1 || true)"
        (cd "$ARC_DIR" && python3 rb_task/tools/run_report.py "$RUN_DIR" --out "docs/runs/${NAME}_auto.md" ${MAN:+--manifest "$MAN"} --title "$NAME")
        ;;
    relbench)
        write_manifest relbench "$@"
        IMAGE="$RB_IMAGE"
        export LLAMA_CTX="${LLAMA_CTX:-65536}"
        TOPIC="${2:-$DEFAULT_RB_TOPIC}"
        docker_run env \
            ARC_SEED_PROJECT_DIR=/app/rb_task/seed_project \
            RB_RECIPE="${RB_RECIPE:-tuned}" \
            ARC_TASK_SPEC_FILE=/app/rb_task/task_spec/full.md \
            ARC_HIDE_TEST_METRICS=1 \
            ARC_SEARCH_MODE="${ARC_SEARCH_MODE:-config}" \
            ARC_SEARCH_SPACE_FILE=/app/rb_task/task_spec/search_space.json \
            ARC_PROTECTED_FILES="main.py,rb_data.py,rb_loader.py,rb_text.py,rb_train.py" \
            ARC_MIN_IMPROVEMENT="${ARC_MIN_IMPROVEMENT:-0.005}" \
            ARC_KEEP_SEEDS=1 \
            ARC_PRESERVE_FILENAMES=1 \
            ARC_CONFIRM_SEED_OFFSET="${ARC_CONFIRM_SEED_OFFSET:-100}" \
            ARC_REFINE_PATIENCE="${ARC_REFINE_PATIENCE:-5}" \
            ARC_MAX_TOKENS_MULT="${ARC_MAX_TOKENS_MULT:-3}" \
            researchclaw run --config config.arc.relbench.yaml \
            --topic "$TOPIC" --auto-approve
        ;;
    *)
        echo "Uso: $0 {build|run \"<topic>\"|shell|exec <cmd...>|build-relbench|smoke|baseline|vram|sweep|report <run_dir> [nome]|relbench [\"<topic>\"]}" >&2
        exit 1
        ;;
esac
