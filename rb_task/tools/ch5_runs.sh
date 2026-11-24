#!/bin/bash
# Esperimenti per il capitolo 5, tutti SENZA LLM (kit 0.6.11, nessuna modifica al kit).
#   (a) ablazione del modello di RUN-004: quanto viene da lr 1e-3 e quanto dall'architettura
#   (b) aggr=max da solo: quanto del +0,032 di RUN-013 (modello di RUN-011 su driver-top3) spiega
#   (c) i modelli finali di RUN-004, RUN-008 e RUN-011 rivalutati con le varianti 1-3 dei tipi delle colonne (RUN-015)
# Uso (dalla cartella del repo sul nodo):
#   cp ch5_runs.sh ~/AutoResearchClaw/ && cd ~/AutoResearchClaw && ./run.sh vram
#   nohup bash ch5_runs.sh > artifacts/ch5_runs.log 2>&1 &
#   tail -f artifacts/ch5_runs.log
set -u
cd ~/AutoResearchClaw || exit 1
cat rb_task/VERSION                     # deve iniziare con "relbench-kit 0.6.11"

R4=artifacts/rc-20261005-183409-9b9601/stage-13/experiment_final    # RUN-004 (driver-top3)
R8=artifacts/rc-20261013-131020-9b9601/stage-13/experiment_final    # RUN-008 (driver-top3)
R11=artifacts/rc-20261014-152719-4d33ce/stage-13/experiment_final   # RUN-011 (driver-dnf)
ls "$R4/rb_config.py" "$R8/rb_config.py" "$R11/rb_config.py" || { echo "manca un progetto finale"; exit 1; }

# ---- (a) ablazione di RUN-004 (rb_task/task_spec/ablation_run004.json, gia' nel kit), semi 100-109 ----
# lo sweep scrive sempre ./sweep_results.json: prima si salva quello che c'e' (RUN-002 o successivi)
[ -f sweep_results.json ] && cp sweep_results.json artifacts/sweep_results_prima_ch5.json
RB_SWEEP_CONFIGS_JSON=/app/rb_task/task_spec/ablation_run004.json RB_SWEEP_SEEDS=10 RB_SWEEP_SEED_OFFSET=100 \
RB_SWEEP_THREADS=1 ./run.sh sweep 2>&1 | tee artifacts/ch5_a_ablation_run004.txt
cp sweep_results.json artifacts/ch5_a_ablation_run004.json

# ---- (b) progetto con il solo aggr=max: modello ufficiale + aggregazione max, ricetta tuned ----
mkdir -p artifacts/ch5_aggr_max_only
cp rb_task/seed_project/*.py artifacts/ch5_aggr_max_only/
sed -i 's/^PROPOSED_OVERRIDES = {}$/PROPOSED_OVERRIDES = {"aggr": "max"}/' artifacts/ch5_aggr_max_only/rb_config.py
grep -q '^PROPOSED_OVERRIDES = {"aggr": "max"}$' artifacts/ch5_aggr_max_only/rb_config.py || { echo "sed non riuscito"; exit 1; }

# ---- (b) e (c): ogni modello con le varianti 1-3 dei tipi delle colonne (50 campioni come RUN-015) ----
# (run.sh stampa alla fine "-> artifacts/repro_stypes_<data>/...": ignoralo, la cartella vera e' quella di --out)
./run.sh repro-stypes --max-worlds 3 --project artifacts/ch5_aggr_max_only --out artifacts/ch5_c_aggrmax_top3 2>&1 | tee artifacts/ch5_c_aggrmax_top3.txt
./run.sh repro-stypes --max-worlds 3 --project "$R4"  --out artifacts/ch5_c_run004_top3 2>&1 | tee artifacts/ch5_c_run004_top3.txt
./run.sh repro-stypes --max-worlds 3 --project "$R8"  --out artifacts/ch5_c_run008_top3 2>&1 | tee artifacts/ch5_c_run008_top3.txt
./run.sh repro-stypes --max-worlds 3 --project "$R11" --out artifacts/ch5_c_run011_top3 2>&1 | tee artifacts/ch5_c_run011_top3.txt
RB_TASK=driver-dnf ./run.sh repro-stypes --max-worlds 3 --project "$R11" --out artifacts/ch5_c_run011_dnf 2>&1 | tee artifacts/ch5_c_run011_dnf.txt

# ---- archivio piccolo da mandare (solo riassunti, risultati per seme, varianti e manifest; niente cache) ----
tar czf ch5_risultati.tgz artifacts/ch5_runs.log artifacts/ch5_a_ablation_run004.json artifacts/ch5_a_ablation_run004.txt \
    artifacts/ch5_c_*.txt artifacts/ch5_aggr_max_only/rb_config.py \
    $(find artifacts/ch5_c_* -type f \( -name summary_stypes.md -o -name stypes_info.json -o -name results.json -o -name 'variant_*.json' \)) \
    $(find docs/runs/_manifests -type f -newer ch5_runs.sh)
echo "FATTO -> ~/AutoResearchClaw/ch5_risultati.tgz"
