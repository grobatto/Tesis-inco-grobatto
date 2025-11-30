#!/bin/bash
# run_all_models.sh - Ejecuta benchmarks en todos los modelos disponibles
#
# Uso: ./run_all_models.sh
#
# Este script ejecuta el benchmark de anonimización en todos los modelos
# configurados y guarda los resultados en el directorio results/

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"
BENCHMARK_SCRIPT="$SCRIPT_DIR/benchmark_anon.py"

# Modelos a probar
declare -A MODELS
MODELS["qwen-7b"]=8089
MODELS["mistral-7b"]=8088
MODELS["llama3-8b"]=8090

# Crear directorio de resultados
mkdir -p "$RESULTS_DIR"

echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  BENCHMARK MULTI-MODELO - ANONIMIZACIÓN CLÍNICA    ║${NC}"
echo -e "${GREEN}║  IBM Power10 + MMA - Universidad de Montevideo     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SUMMARY_FILE="$RESULTS_DIR/summary_$TIMESTAMP.txt"

echo "Benchmark Multi-Modelo - $TIMESTAMP" > "$SUMMARY_FILE"
echo "======================================" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

for model in "${!MODELS[@]}"; do
    port=${MODELS[$model]}

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  Probando: $model (puerto $port)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Verificar si el servidor está corriendo
    if ! curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${RED}  SKIP: Servidor no disponible en puerto $port${NC}"
        echo "$model: NO DISPONIBLE" >> "$SUMMARY_FILE"
        continue
    fi

    # Ejecutar benchmark
    OUTPUT_FILE="$RESULTS_DIR/${model}_$TIMESTAMP.json"

    python3 "$BENCHMARK_SCRIPT" --port "$port" --save --output "$OUTPUT_FILE"

    if [ -f "$OUTPUT_FILE" ]; then
        # Extraer TPS del resultado
        TPS=$(python3 -c "import json; print(f\"{json.load(open('$OUTPUT_FILE'))['tps_avg']:.2f}\")" 2>/dev/null || echo "N/A")
        echo "$model: $TPS TPS" >> "$SUMMARY_FILE"
        echo -e "${GREEN}  Completado: $TPS TPS${NC}"
    else
        echo -e "${RED}  Error al ejecutar benchmark${NC}"
        echo "$model: ERROR" >> "$SUMMARY_FILE"
    fi

    echo ""
    sleep 2
done

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  RESUMEN${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat "$SUMMARY_FILE"
echo ""
echo -e "${GREEN}Resultados guardados en: $RESULTS_DIR${NC}"
