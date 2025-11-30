#!/bin/bash
# benchmark.sh - Ejecuta benchmarks de rendimiento para modelos LLM
#
# Uso: ./benchmark.sh <puerto> [iteraciones] [tokens]
# Ejemplo: ./benchmark.sh 8089 5 100

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parámetros
PORT=${1:-8089}
ITERATIONS=${2:-5}
TOKENS=${3:-100}

# Prompts de prueba
PROMPTS=(
    "Explica qué es la inteligencia artificial en términos simples:"
    "¿Cuáles son los beneficios de la computación en la nube?"
    "Describe el proceso de machine learning:"
    "¿Qué es IBM Power10 y cuáles son sus características principales?"
    "Explica brevemente qué es la cuantización de modelos:"
)

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     BENCHMARK LLM EN IBM POWER10 + MMA             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Configuración:${NC}"
echo "  Puerto: $PORT"
echo "  Iteraciones: $ITERATIONS"
echo "  Tokens por respuesta: $TOKENS"
echo ""

# Verificar que el servidor está corriendo
echo -e "${YELLOW}Verificando servidor...${NC}"
if ! curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
    echo "Error: No se puede conectar al servidor en puerto $PORT"
    exit 1
fi
echo -e "${GREEN}Servidor OK${NC}"
echo ""

# Variables para acumular resultados
total_prompt_rate=0
total_gen_rate=0
total_ttft=0
results=()

echo -e "${YELLOW}Ejecutando benchmark...${NC}"
echo ""

for i in $(seq 1 $ITERATIONS); do
    # Seleccionar prompt aleatorio
    PROMPT="${PROMPTS[$((RANDOM % ${#PROMPTS[@]}))]}"

    echo -e "${CYAN}Iteración $i/$ITERATIONS${NC}"
    echo "  Prompt: ${PROMPT:0:50}..."

    # Ejecutar request y capturar resultado
    START_TIME=$(date +%s%3N)

    result=$(curl -s -X POST "http://localhost:$PORT/completion" \
        -H "Content-Type: application/json" \
        -d "{
            \"prompt\": \"$PROMPT\",
            \"n_predict\": $TOKENS,
            \"temperature\": 0.7
        }")

    END_TIME=$(date +%s%3N)
    TOTAL_TIME=$((END_TIME - START_TIME))

    # Extraer métricas
    prompt_rate=$(echo "$result" | jq -r '.timings.prompt_per_second // 0')
    gen_rate=$(echo "$result" | jq -r '.timings.predicted_per_second // 0')
    prompt_ms=$(echo "$result" | jq -r '.timings.prompt_ms // 0')
    predicted_n=$(echo "$result" | jq -r '.timings.predicted_n // 0')

    echo "  Prompt eval: ${prompt_rate} tokens/seg"
    echo "  Generación: ${gen_rate} tokens/seg"
    echo "  Tokens generados: ${predicted_n}"
    echo "  Tiempo total: ${TOTAL_TIME} ms"
    echo ""

    # Acumular para promedio
    total_prompt_rate=$(echo "$total_prompt_rate + $prompt_rate" | bc)
    total_gen_rate=$(echo "$total_gen_rate + $gen_rate" | bc)
    total_ttft=$(echo "$total_ttft + $prompt_ms" | bc)

    # Guardar resultado
    results+=("$prompt_rate,$gen_rate,$TOTAL_TIME")

    # Pequeña pausa entre iteraciones
    sleep 1
done

# Calcular promedios
avg_prompt=$(echo "scale=2; $total_prompt_rate / $ITERATIONS" | bc)
avg_gen=$(echo "scale=2; $total_gen_rate / $ITERATIONS" | bc)
avg_ttft=$(echo "scale=2; $total_ttft / $ITERATIONS" | bc)

# Mostrar resultados
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    RESULTADOS                      ║${NC}"
echo -e "${GREEN}╠════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║${NC}  Prompt eval (promedio):    ${CYAN}${avg_prompt} tokens/seg${NC}       ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Generación (promedio):     ${CYAN}${avg_gen} tokens/seg${NC}        ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  TTFT (promedio):           ${CYAN}${avg_ttft} ms${NC}               ${GREEN}║${NC}"
echo -e "${GREEN}║${NC}  Tokens por respuesta:      ${CYAN}${TOKENS}${NC}                    ${GREEN}║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"

# Exportar resultados a CSV
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CSV_FILE="benchmark_${PORT}_${TIMESTAMP}.csv"

echo "iteration,prompt_rate,gen_rate,total_time_ms" > "$CSV_FILE"
for i in "${!results[@]}"; do
    echo "$((i+1)),${results[$i]}" >> "$CSV_FILE"
done

echo ""
echo -e "${GREEN}Resultados exportados a: $CSV_FILE${NC}"

# Comparar con referencia
echo ""
echo -e "${YELLOW}Comparación con valores de referencia (Qwen 7B):${NC}"
echo "  Referencia prompt: ~26 tokens/seg"
echo "  Referencia gen:    ~16.6 tokens/seg"

if (( $(echo "$avg_gen > 15" | bc -l) )); then
    echo -e "  Estado: ${GREEN}ÓPTIMO${NC}"
elif (( $(echo "$avg_gen > 10" | bc -l) )); then
    echo -e "  Estado: ${YELLOW}ACEPTABLE${NC}"
else
    echo -e "  Estado: ${RED}REVISAR CONFIGURACIÓN${NC}"
fi
