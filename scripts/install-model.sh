#!/bin/bash
# install-model.sh - Descarga e instala modelos de Hugging Face
#
# Uso: ./install-model.sh <modelo> <puerto>
# Ejemplo: ./install-model.sh qwen-7b 8089

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
MODELS_DIR="${HOME}/models"
DOCKER_IMAGE="quay.io/daniel_casali/llama.cpp-mma:v8"

# Modelos disponibles
declare -A MODELS
MODELS["mistral-7b"]="https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_S.gguf|Mistral-7B-Instruct-v0.3-Q4_K_S.gguf"
MODELS["qwen-7b"]="https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf|Qwen2.5-7B-Instruct-Q4_K_M.gguf"
MODELS["llama3-8b"]="https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf|Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
MODELS["llama3.1-8b"]="https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf|Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
MODELS["qwen-14b"]="https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF/resolve/main/Qwen2.5-14B-Instruct-Q4_K_M.gguf|Qwen2.5-14B-Instruct-Q4_K_M.gguf"

# Función de ayuda
show_help() {
    echo -e "${GREEN}=== Instalador de Modelos LLM para Power10 ===${NC}"
    echo ""
    echo "Uso: $0 <modelo> <puerto>"
    echo ""
    echo "Modelos disponibles:"
    echo "  mistral-7b    - Mistral 7B Instruct v0.3 (~4 GB)"
    echo "  qwen-7b       - Qwen 2.5 7B Instruct (~4.7 GB)"
    echo "  llama3-8b     - Meta Llama 3 8B Instruct (~4.7 GB)"
    echo "  llama3.1-8b   - Meta Llama 3.1 8B Instruct (~4.7 GB)"
    echo "  qwen-14b      - Qwen 2.5 14B Instruct (~8 GB)"
    echo ""
    echo "Ejemplo:"
    echo "  $0 qwen-7b 8089"
    echo ""
}

# Verificar argumentos
if [ $# -lt 2 ]; then
    show_help
    exit 1
fi

MODEL_KEY=$1
PORT=$2

# Verificar modelo válido
if [ -z "${MODELS[$MODEL_KEY]}" ]; then
    echo -e "${RED}Error: Modelo '$MODEL_KEY' no encontrado${NC}"
    show_help
    exit 1
fi

# Extraer URL y nombre de archivo
IFS='|' read -r MODEL_URL MODEL_FILE <<< "${MODELS[$MODEL_KEY]}"

echo -e "${GREEN}=== Instalando $MODEL_KEY en puerto $PORT ===${NC}"

# Paso 1: Crear directorio de modelos
echo -e "${YELLOW}[1/4] Creando directorio de modelos...${NC}"
mkdir -p "$MODELS_DIR"

# Paso 2: Descargar modelo
MODEL_PATH="$MODELS_DIR/$MODEL_FILE"
if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}[2/4] Modelo ya existe: $MODEL_PATH${NC}"
else
    echo -e "${YELLOW}[2/4] Descargando modelo desde Hugging Face...${NC}"
    echo "URL: $MODEL_URL"
    wget -q --show-progress "$MODEL_URL" -O "$MODEL_PATH"
    echo -e "${GREEN}Descarga completada${NC}"
fi

# Paso 3: Verificar/descargar imagen Docker
echo -e "${YELLOW}[3/4] Verificando imagen Docker...${NC}"
if ! docker image inspect "$DOCKER_IMAGE" > /dev/null 2>&1; then
    echo "Descargando imagen Docker..."
    docker pull "$DOCKER_IMAGE"
else
    echo "Imagen Docker ya existe"
fi

# Paso 4: Iniciar contenedor
CONTAINER_NAME=$MODEL_KEY
echo -e "${YELLOW}[4/4] Iniciando contenedor '$CONTAINER_NAME' en puerto $PORT...${NC}"

# Detener contenedor existente si existe
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Deteniendo contenedor existente..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
fi

# Iniciar nuevo contenedor
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:8080" \
    -v "$MODELS_DIR:/models" \
    --restart always \
    "$DOCKER_IMAGE" \
    --host 0.0.0.0 \
    --port 8080 \
    -m "/models/$MODEL_FILE" \
    -c 4096 -b 256 -t 12 -n -1

# Esperar a que el servidor esté listo
echo -e "${YELLOW}Esperando que el servidor esté listo...${NC}"
sleep 10

# Verificar estado
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${GREEN}=== Instalación Completada ===${NC}"
    echo ""
    echo "Modelo: $MODEL_KEY"
    echo "Puerto: $PORT"
    echo "Contenedor: $CONTAINER_NAME"
    echo ""
    echo "Para probar:"
    echo "  curl -X POST http://localhost:$PORT/completion \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"prompt\": \"Hola, ¿cómo estás?\", \"n_predict\": 50}'"
    echo ""
    echo "Para ver logs:"
    echo "  docker logs $CONTAINER_NAME --tail 50"
else
    echo -e "${RED}Error: El contenedor no se inició correctamente${NC}"
    echo "Verificar logs: docker logs $CONTAINER_NAME"
    exit 1
fi
