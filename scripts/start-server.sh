#!/bin/bash
# start-server.sh - Inicia un servidor de inferencia para un modelo existente
#
# Uso: ./start-server.sh <modelo> [puerto]
# Ejemplo: ./start-server.sh qwen-7b 8089

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuración
MODELS_DIR="${HOME}/models"
DOCKER_IMAGE="quay.io/daniel_casali/llama.cpp-mma:v8"

# Mapeo de modelos a archivos
declare -A MODEL_FILES
MODEL_FILES["mistral-7b"]="Mistral-7B-Instruct-v0.3-Q4_K_S.gguf"
MODEL_FILES["qwen-7b"]="Qwen2.5-7B-Instruct-Q4_K_M.gguf"
MODEL_FILES["llama3-8b"]="Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"
MODEL_FILES["llama3.1-8b"]="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
MODEL_FILES["qwen-14b"]="Qwen2.5-14B-Instruct-Q4_K_M.gguf"

# Puertos por defecto
declare -A DEFAULT_PORTS
DEFAULT_PORTS["mistral-7b"]="8088"
DEFAULT_PORTS["qwen-7b"]="8089"
DEFAULT_PORTS["llama3-8b"]="8090"
DEFAULT_PORTS["llama3.1-8b"]="8090"
DEFAULT_PORTS["qwen-14b"]="8091"

show_help() {
    echo -e "${GREEN}=== Iniciar Servidor LLM ===${NC}"
    echo ""
    echo "Uso: $0 <modelo> [puerto]"
    echo ""
    echo "Modelos disponibles:"
    for key in "${!MODEL_FILES[@]}"; do
        echo "  $key (puerto default: ${DEFAULT_PORTS[$key]})"
    done
    echo ""
    echo "Ejemplo:"
    echo "  $0 qwen-7b        # Usa puerto por defecto 8089"
    echo "  $0 qwen-7b 9000   # Usa puerto 9000"
    echo ""
}

# Verificar argumentos
if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

MODEL_KEY=$1
PORT=${2:-${DEFAULT_PORTS[$MODEL_KEY]}}

# Verificar modelo válido
if [ -z "${MODEL_FILES[$MODEL_KEY]}" ]; then
    echo -e "${RED}Error: Modelo '$MODEL_KEY' no reconocido${NC}"
    show_help
    exit 1
fi

MODEL_FILE="${MODEL_FILES[$MODEL_KEY]}"
MODEL_PATH="$MODELS_DIR/$MODEL_FILE"

# Verificar que el modelo existe
if [ ! -f "$MODEL_PATH" ]; then
    echo -e "${RED}Error: Modelo no encontrado: $MODEL_PATH${NC}"
    echo "Ejecuta primero: ./install-model.sh $MODEL_KEY $PORT"
    exit 1
fi

echo -e "${GREEN}=== Iniciando servidor $MODEL_KEY ===${NC}"

CONTAINER_NAME=$MODEL_KEY

# Verificar si ya está corriendo
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}El contenedor '$CONTAINER_NAME' ya está corriendo${NC}"
    echo ""
    echo "Para detenerlo: docker stop $CONTAINER_NAME"
    echo "Para reiniciarlo: docker restart $CONTAINER_NAME"
    echo "Para ver logs: docker logs $CONTAINER_NAME --tail 50"
    exit 0
fi

# Eliminar contenedor detenido si existe
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Eliminando contenedor detenido..."
    docker rm "$CONTAINER_NAME"
fi

# Determinar threads según RAM disponible
AVAILABLE_RAM=$(free -g | awk '/^Mem:/{print $7}')
if [ "$AVAILABLE_RAM" -gt 20 ]; then
    THREADS=12
elif [ "$AVAILABLE_RAM" -gt 10 ]; then
    THREADS=8
else
    THREADS=4
fi

echo "RAM disponible: ${AVAILABLE_RAM}GB"
echo "Threads a usar: $THREADS"
echo "Puerto: $PORT"
echo ""

# Iniciar contenedor
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:8080" \
    -v "$MODELS_DIR:/models" \
    --restart always \
    "$DOCKER_IMAGE" \
    --host 0.0.0.0 \
    --port 8080 \
    -m "/models/$MODEL_FILE" \
    -c 4096 -b 256 -t "$THREADS" -n -1

echo -e "${YELLOW}Esperando que el servidor cargue el modelo...${NC}"
sleep 5

# Mostrar logs iniciales
echo -e "${GREEN}=== Logs iniciales ===${NC}"
docker logs "$CONTAINER_NAME" --tail 20

echo ""
echo -e "${GREEN}=== Servidor iniciado ===${NC}"
echo "URL: http://localhost:$PORT"
echo ""
echo "Endpoints disponibles:"
echo "  POST /completion    - Completar texto"
echo "  POST /v1/chat/completions - API compatible con OpenAI"
echo "  GET  /health        - Estado del servidor"
echo ""
echo "Para probar:"
echo "  curl http://localhost:$PORT/health"
