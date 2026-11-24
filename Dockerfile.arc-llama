# syntax=docker/dockerfile:1
#
# Immagine unica: llama.cpp (CUDA) + AutoResearchClaw.
# Build dalla cartella del repo:
#   docker build -f Dockerfile.arc-llama -t arc-llama:latest .
#
# Argomenti di build utili:
#   --build-arg CUDA_ARCHS="120"      (RTX 5090=120, 4090/L40=89, H100=90, A100=80)
#   --build-arg CUDA_VERSION=12.4.1   (se il driver del cluster e' vecchio)
#   --build-arg WITH_LATEX=false      (immagine piu' leggera, niente compilazione PDF)

ARG CUDA_VERSION=12.8.1
ARG UBUNTU=ubuntu24.04

# ---------------------------------------------------------------------------
# Stage 1: compila llama-server con CUDA
# ---------------------------------------------------------------------------
FROM nvidia/cuda:${CUDA_VERSION}-devel-${UBUNTU} AS llama-build

ARG CUDA_ARCHS="120"
ARG LLAMA_CPP_REF=master

RUN apt-get update && apt-get install -y --no-install-recommends \
        git cmake build-essential ca-certificates libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 --branch "${LLAMA_CPP_REF}" https://github.com/ggml-org/llama.cpp .

RUN cmake -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DGGML_CUDA=ON \
        -DGGML_NATIVE=OFF \
        -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCHS}" \
        -DLLAMA_CURL=OFF \
        -DCMAKE_EXE_LINKER_FLAGS=-Wl,--allow-shlib-undefined \
    && cmake --build build --config Release --target llama-server -j"$(nproc)" \
    && mkdir -p /opt/llama \
    && cp build/bin/llama-server /opt/llama/ \
    && (cp build/bin/*.so* /opt/llama/ 2>/dev/null || true)

# ---------------------------------------------------------------------------
# Stage 2: runtime con Python + AutoResearchClaw
# ---------------------------------------------------------------------------
FROM nvidia/cuda:${CUDA_VERSION}-runtime-${UBUNTU}

ARG WITH_LATEX=true

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev build-essential git curl ca-certificates \
        libgomp1 libssl3t64 \
    && if [ "$WITH_LATEX" = "true" ]; then \
         apt-get install -y --no-install-recommends \
           texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
           texlive-science texlive-bibtex-extra latexmk ; \
       fi \
    && rm -rf /var/lib/apt/lists/*

# Librerie per gli esperimenti generati dalla pipeline (sandbox = /usr/bin/python3).
# Torch con CUDA 12.8 (supporta Blackwell/RTX 5090): gli esperimenti usano la GPU
# insieme a llama-server. torchvision serve: il codice generato lo importa spesso.
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 \
 && pip install numpy scipy pandas matplotlib seaborn scikit-learn pillow

# Dataset pre-scaricati in /opt/datasets (la pipeline assume questo percorso e usa
# download=False nel codice generato; senza questi file gli esperimenti non partono).
RUN python3 -c "from torchvision import datasets as d; [D('/opt/datasets', train=t, download=True) for D in (d.CIFAR10, d.CIFAR100, d.MNIST, d.FashionMNIST) for t in (True, False)]" \
 && chmod -R a+rX /opt/datasets

# llama-server
COPY --from=llama-build /opt/llama /opt/llama
ENV LD_LIBRARY_PATH=/opt/llama

# AutoResearchClaw (editable: a runtime montiamo la stessa cartella su /app)
WORKDIR /app
COPY . /app
RUN pip install -e ".[all]"

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV MODEL_PATH=/llms/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf \
    MODEL_ALIAS=qwen3.6-35b \
    LLAMA_PORT=8081 \
    LLAMA_CTX=32768 \
    LLAMA_NGL=99 \
    LLAMA_STARTUP_TIMEOUT=900 \
    LLAMA_EXTRA_ARGS="" \
    LLAMACPP_API_KEY=none

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]