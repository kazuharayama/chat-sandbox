#!/bin/bash
set -e

# chat-sandbox startup script with GPU auto-detection

COMPOSE_FILE="docker-compose.yml"

echo "=== chat-sandbox startup ==="

# Check for NVIDIA GPU + Docker GPU runtime
detect_gpu() {
    if ! command -v nvidia-smi &>/dev/null; then
        echo "[INFO] nvidia-smi not found"
        return 1
    fi

    if ! nvidia-smi &>/dev/null; then
        echo "[INFO] nvidia-smi found but GPU not available"
        return 1
    fi

    if ! docker info 2>/dev/null | grep -q "nvidia"; then
        echo "[WARN] GPU detected but nvidia-container-toolkit not installed in Docker"
        echo "  Install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
        return 1
    fi

    echo "[INFO] NVIDIA GPU detected with Docker GPU runtime"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    return 0
}

# Parse arguments
PROFILE=""
EXTRA_ARGS=""

case "${1}" in
    --gpu)
        PROFILE="gpu"
        shift
        ;;
    --cpu)
        PROFILE="cpu"
        shift
        ;;
    --no-llm)
        PROFILE=""
        shift
        ;;
    *)
        # Auto-detect
        if detect_gpu; then
            PROFILE="gpu"
        else
            PROFILE="cpu"
        fi
        ;;
esac

EXTRA_ARGS="$@"

# Models to pull on startup (LLM + Embedding)
OLLAMA_MODELS=("gemma2:2b" "llama3.2:3b" "nomic-embed-text")

# Point backend at the Ollama instance that matches the chosen profile.
# (backend defaults to ollama-cpu; without this the GPU profile starts
#  ollama-gpu but the backend keeps looking at ollama-cpu and cannot reach it.)
if [ "$PROFILE" = "gpu" ]; then
    export LLM_BASE_URL="${LLM_BASE_URL:-http://ollama-gpu:11434}"
elif [ "$PROFILE" = "cpu" ]; then
    export LLM_BASE_URL="${LLM_BASE_URL:-http://ollama-cpu:11434}"
fi

# Start services
if [ -n "$PROFILE" ]; then
    echo ""
    echo "Starting with profile: ${PROFILE}"
    echo "  docker compose --profile ${PROFILE} up -d ${EXTRA_ARGS}"
    docker compose --profile "${PROFILE}" up -d ${EXTRA_ARGS}
else
    echo ""
    echo "Starting without local LLM"
    echo "  docker compose up -d ${EXTRA_ARGS}"
    docker compose up -d ${EXTRA_ARGS}
fi

# Auto-pull Ollama models when LLM profile is active
if [ "$PROFILE" = "gpu" ] || [ "$PROFILE" = "cpu" ]; then
    OLLAMA_SVC="ollama-${PROFILE}"
    echo ""
    echo "=== Ensuring Ollama models are available (${OLLAMA_SVC}) ==="
    # Wait for ollama to accept connections
    for i in {1..30}; do
        if docker compose --profile "${PROFILE}" exec -T "${OLLAMA_SVC}" ollama list >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    for model in "${OLLAMA_MODELS[@]}"; do
        if docker compose --profile "${PROFILE}" exec -T "${OLLAMA_SVC}" ollama list 2>/dev/null | grep -q "^${model}"; then
            echo "  [skip] ${model} already present"
        else
            echo "  [pull] ${model}"
            docker compose --profile "${PROFILE}" exec -T "${OLLAMA_SVC}" ollama pull "${model}" || \
                echo "  [warn] failed to pull ${model} (continuing)"
        fi
    done
fi

echo ""
echo "=== Services ==="
echo "  Frontend:  http://localhost:5174"
echo "  Backend:   http://localhost:8000"
echo "  Nginx:     http://localhost:8080"
echo "  Langfuse:  http://localhost:3000"
if [ "$PROFILE" = "gpu" ] || [ "$PROFILE" = "cpu" ]; then
    echo "  Ollama:    http://localhost:11434"
fi
if [ "$PROFILE" = "gpu" ]; then
    echo "  vLLM:      http://localhost:8001"
fi
echo ""
echo "Usage: $0 [--gpu|--cpu|--no-llm] [docker compose args...]"
