#!/usr/bin/env bash
# Uso:
#   ./run.sh build
#   ./run.sh run "Effect of dropout rate on overfitting in small neural networks"
#   ./run.sh shell
#   ./run.sh exec python3 -c "print(1)"   (comando singolo nel container)
set -euo pipefail

ARC_DIR="${ARC_DIR:-/home/damario/AutoResearchClaw}"
LLMS_DIR="${LLMS_DIR:-/llms}"
IMAGE="${IMAGE:-arc-llama:latest}"
CUDA_ARCHS="${CUDA_ARCHS:-120}"   # RTX 5090 (Blackwell)

TTY_FLAGS=""
[ -t 0 ] && [ -t 1 ] && TTY_FLAGS="-it"

# Con Docker rootless / userns-remap, root nel container == il tuo utente sull'host:
# passare --user romperebbe i permessi sulla cartella montata.
USER_FLAGS="--user $(id -u):$(id -g)"
if docker info --format '{{.SecurityOptions}}' 2>/dev/null | grep -qE 'rootless|userns'; then
    USER_FLAGS=""
fi

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
        -e LLAMA_EXTRA_ARGS -e LLAMA_CTX -e LLAMA_NGL -e LLAMA_ENABLE_THINKING -e ARC_MAX_TOKENS_MULT -e ARC_MAX_TOKENS_CAP -e ARC_STAGE12_REPAIRS \
        -e S2_API_KEY -e GITHUB_TOKEN -e OPENALEX_API_KEY -e TAVILY_API_KEY_UNSET \
        "$IMAGE" "$@"
}

case "${1:-}" in
    build)
        cd "$ARC_DIR"
        docker build -f Dockerfile \
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
    *)
        echo "Uso: $0 {build|run \"<topic>\"|shell|exec <comando...>}" >&2
        exit 1
        ;;
esac