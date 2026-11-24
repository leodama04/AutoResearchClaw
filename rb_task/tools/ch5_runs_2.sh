#!/bin/bash
# Seconda esecuzione degli esperimenti del capitolo 5, tutti SENZA LLM e senza modifiche al kit.
# Il 29/10 quasi tutte le valutazioni sono fallite perche' un altro utente occupava 26-29 GB della GPU
# (codice 3 = GPU_UNAVAILABLE dopo 10 minuti di attesa; codice 1 = crash, probabilmente memoria esaurita).
# Differenze rispetto a ch5_runs.sh:
#   - prima di ogni passo aspetta che la GPU abbia almeno NEED_MB liberi (default 8000 MiB) e main.py aspetta fino a 12 ore;
#   - l'ablazione (a) usa la stessa variante dei tipi delle colonne di RUN-004 (3) e poi le varianti 1 e 2, invece di
#     una variante casuale; ha un log completo e scrive i risultati in una cartella sua (non tocca sweep_results.json);
#   - l'archivio finale contiene anche i log delle valutazioni.
# Uso (dalla cartella del repo sul nodo):
#   cp ch5_runs_2.sh ~/AutoResearchClaw/ && cd ~/AutoResearchClaw
#   nohup bash ch5_runs_2.sh > artifacts/ch5_runs_2.log 2>&1 &
#   tail -f artifacts/ch5_runs_2.log
# Per partire anche con l'altro job sulla GPU (rischio di crash per memoria): NEED_MB=6000 nohup bash ch5_runs_2.sh ...
set -u
cd ~/AutoResearchClaw || exit 1
cat rb_task/VERSION                                  # deve iniziare con "relbench-kit 0.6.11"
export RB_GPU_WAIT_SEC=43200                         # main.py: attesa massima di 4,5 GB liberi, 12 ore invece di 10 minuti
NEED_MB="${NEED_MB:-8000}"

R4=artifacts/rc-20261005-183409-9b9601/stage-13/experiment_final    # RUN-004 (driver-top3)
R8=artifacts/rc-20261013-131020-9b9601/stage-13/experiment_final    # RUN-008 (driver-top3)
R11=artifacts/rc-20261014-152719-4d33ce/stage-13/experiment_final   # RUN-011 (driver-dnf)
VAR=artifacts/ch5_c_run004_top3/stypes                              # varianti dei tipi delle colonne scritte il 29/10
ls "$R4/rb_config.py" "$R8/rb_config.py" "$R11/rb_config.py" "$VAR/variant_3.json" artifacts/ch5_aggr_max_only/rb_config.py \
    || { echo "manca qualcosa (progetti finali, varianti o progetto aggr=max del 29/10)"; exit 1; }

wait_gpu() {
    while :; do
        free=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
        if [ "$free" -ge "$NEED_MB" ]; then echo "$(date '+%F %T') GPU: $free MiB liberi -> $1"; return; fi
        echo "$(date '+%F %T') GPU: $free MiB liberi, ne servono $NEED_MB: aspetto 5 minuti ($1)"
        sleep 300
    done
}

UF="--user $(id -u):$(id -g)"                         # come run.sh
docker info --format '{{.SecurityOptions}}' 2>/dev/null | grep -qE 'rootless|userns' && UF=""

# (a) ablazione di RUN-004 con una variante fissata dei tipi delle colonne (stesso container di ./run.sh, LLM spento)
ablation() {
    local v=$1 out=artifacts/ch5_a_ablation_v$1
    mkdir -p "$out"
    wait_gpu "ablazione RUN-004, variante $v"
    { echo "date: $(date -u +%FT%TZ)"; echo "git: $(git rev-parse --short HEAD)"; echo "kit: $(cat rb_task/VERSION)";
      echo "gpu: $(nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader)";
      echo "configs: rb_task/task_spec/ablation_run004.json, seeds 100-109, threads 1, stypes = variant_$v.json"; } > "$out/info.txt"
    # shellcheck disable=SC2086
    docker run --rm --init --gpus all $UF -e HOME=/tmp --shm-size=8g \
        -v "$PWD":/app -v "$PWD/docker-entrypoint.sh":/usr/local/bin/docker-entrypoint.sh:ro \
        -e ARC_NO_LLM=1 -e PYTHONUNBUFFERED=1 -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
        -e RB_CACHE_DIR=/tmp/rbcache -e RB_SEED_DIR=/app/rb_task/seed_project \
        -e RB_SWEEP_CONFIGS_JSON=/app/rb_task/task_spec/ablation_run004.json \
        -e RB_SWEEP_SEEDS=10 -e RB_SWEEP_SEED_OFFSET=100 -e RB_SWEEP_THREADS=1 -e RB_SWEEP_OUT="/app/$out/sweep_results.json" \
        arc-relbench:latest bash -c "mkdir -p /tmp/rbcache/rel-f1 && cp /app/$VAR/variant_$v.json /tmp/rbcache/rel-f1/stypes.json && cd /app && python3 rb_task/tools/sweep.py" \
        > "$out/log.txt" 2>&1
    echo "   codice di uscita $? -> $out/log.txt"; tail -n 12 "$out/log.txt"
}

# (b) e (c): un modello con le varianti 1-3 (repro-stypes; i suoi passi aspettano la GPU dentro main.py)
stypes() {   # $1 = progetto, $2 = nome della cartella, $3 = task
    wait_gpu "$2"
    RB_TASK="$3" ./run.sh repro-stypes --max-worlds 3 --project "$1" --out "artifacts/$2" 2>&1 | tee "artifacts/$2.txt" | grep -E "variant|baseline_graphsage:|no results"
}

stypes "$R11" ch5_c2_run011_top3 driver-top3
stypes artifacts/ch5_aggr_max_only ch5_c2_aggrmax_top3 driver-top3
stypes "$R4"  ch5_c2_run004_top3 driver-top3
ablation 3
stypes "$R8"  ch5_c2_run008_top3 driver-top3
stypes "$R11" ch5_c2_run011_dnf driver-dnf
ablation 1
ablation 2

# archivio piccolo da mandare: riassunti, risultati per seme, log, varianti e manifest (niente cache)
tar czf ch5_risultati_2.tgz artifacts/ch5_runs_2.log artifacts/ch5_c2_*.txt \
    $(find artifacts/ch5_a_ablation_v* artifacts/ch5_c2_* -type f \( -name summary_stypes.md -o -name stypes_info.json \
        -o -name results.json -o -name sweep_results.json -o -name info.txt -o -name log.txt \)) \
    $(find docs/runs/_manifests -type f -newer ch5_runs_2.sh)
echo "FATTO -> ~/AutoResearchClaw/ch5_risultati_2.tgz"
