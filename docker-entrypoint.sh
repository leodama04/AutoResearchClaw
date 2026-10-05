#!/usr/bin/env bash
# Avvia llama-server in background, aspetta /health, poi esegue il comando richiesto.
set -uo pipefail

# ARC_NO_LLM=1: esegue il comando senza avviare llama-server (test di fumo, baseline)
if [ "${ARC_NO_LLM:-0}" = "1" ]; then
    exec "$@"
fi

MODEL_PATH="${MODEL_PATH:-/llms/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf}"
MODEL_ALIAS="${MODEL_ALIAS:-qwen3.6-35b}"
LLAMA_PORT="${LLAMA_PORT:-8081}"
LLAMA_CTX="${LLAMA_CTX:-32768}"
LLAMA_NGL="${LLAMA_NGL:-99}"
LLAMA_STARTUP_TIMEOUT="${LLAMA_STARTUP_TIMEOUT:-900}"
LLAMA_EXTRA_ARGS="${LLAMA_EXTRA_ARGS:-}"
LOG_FILE="${LLAMA_LOG_FILE:-/tmp/llama-server.log}"

# LLAMA_ENABLE_THINKING=0 disattiva il thinking di Qwen (evita che consumi il budget di token)
THINK_ARGS=()
if [ "${LLAMA_ENABLE_THINKING:-1}" = "0" ]; then
    THINK_ARGS=(--reasoning off)
fi

export LD_LIBRARY_PATH="/opt/llama:${LD_LIBRARY_PATH:-}"

if [ ! -f "$MODEL_PATH" ]; then
    echo "ERRORE: modello non trovato: $MODEL_PATH" >&2
    echo "Contenuto di $(dirname "$MODEL_PATH"):" >&2
    ls -la "$(dirname "$MODEL_PATH")" >&2 || true
    exit 1
fi

echo "[entrypoint] Avvio llama-server ($MODEL_ALIAS) sulla porta $LLAMA_PORT ..."
# shellcheck disable=SC2086
/opt/llama/llama-server \
    -m "$MODEL_PATH" \
    --alias "$MODEL_ALIAS" \
    --host 127.0.0.1 \
    --port "$LLAMA_PORT" \
    -c "$LLAMA_CTX" \
    -ngl "$LLAMA_NGL" \
    -np 1 \
    --jinja \
    "${THINK_ARGS[@]}" \
    $LLAMA_EXTRA_ARGS \
    >"$LOG_FILE" 2>&1 &
SERVER_PID=$!

cleanup() {
    kill -TERM "$SERVER_PID" 2>/dev/null
    wait "$SERVER_PID" 2>/dev/null
}
trap cleanup EXIT
trap 'exit 143' TERM INT

# Attesa readiness (il caricamento di un 35B puo' richiedere qualche minuto)
elapsed=0
until curl -sf "http://127.0.0.1:${LLAMA_PORT}/health" >/dev/null 2>&1; do
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "[entrypoint] llama-server e' terminato subito. Ultime righe del log:" >&2
        tail -n 60 "$LOG_FILE" >&2
        exit 1
    fi
    if [ "$elapsed" -ge "$LLAMA_STARTUP_TIMEOUT" ]; then
        echo "[entrypoint] Timeout (${LLAMA_STARTUP_TIMEOUT}s) in attesa di llama-server. Log:" >&2
        tail -n 60 "$LOG_FILE" >&2
        exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
done
echo "[entrypoint] llama-server pronto (${elapsed}s) ✅"

# Esegue il comando in foreground (cosi' funziona anche `bash` interattivo)
"$@"
rc=$?
exit "$rc"
