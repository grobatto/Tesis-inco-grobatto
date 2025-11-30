# 05 - Guía de Benchmarking y Métricas

## Introducción

Esta guía explica cómo medir y evaluar el rendimiento de los modelos LLM ejecutándose en IBM Power10 con aceleradores MMA.

## Métricas Clave

### Métricas de Rendimiento

| Métrica | Descripción | Unidad |
|---------|-------------|--------|
| **Prompt eval rate** | Velocidad de procesamiento del prompt | tokens/seg |
| **Token generation rate** | Velocidad de generación de respuesta | tokens/seg |
| **Time to first token (TTFT)** | Latencia hasta el primer token | ms |
| **Total time** | Tiempo total de la respuesta | ms |

### Métricas de Recursos

| Métrica | Descripción | Herramienta |
|---------|-------------|-------------|
| **CPU Usage** | Uso de CPU durante inferencia | htop, top |
| **Memory Usage** | Consumo de RAM | free -h |
| **Load Average** | Carga del sistema | uptime |

## Método de Benchmarking

### 1. Benchmark Básico con curl

```bash
# Medir tiempo de respuesta
time curl -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explica en detalle qué es la inteligencia artificial y sus aplicaciones en medicina:",
    "n_predict": 200,
    "temperature": 0.7
  }'
```

### 2. Benchmark con Métricas Detalladas

El servidor llama.cpp devuelve métricas en la respuesta:

```bash
curl -s -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test de benchmark:",
    "n_predict": 100,
    "temperature": 0.7
  }' | jq '.timings'
```

**Respuesta ejemplo:**
```json
{
  "prompt_n": 5,
  "prompt_ms": 187.432,
  "prompt_per_token_ms": 37.486,
  "prompt_per_second": 26.677,
  "predicted_n": 100,
  "predicted_ms": 6024.89,
  "predicted_per_token_ms": 60.249,
  "predicted_per_second": 16.598
}
```

### 3. Script de Benchmark Automatizado

```bash
#!/bin/bash
# benchmark.sh

PORT=${1:-8089}
ITERATIONS=${2:-5}
TOKENS=${3:-100}

echo "=== Benchmark LLM en Power10 ==="
echo "Puerto: $PORT"
echo "Iteraciones: $ITERATIONS"
echo "Tokens por iteración: $TOKENS"
echo ""

PROMPT="Explica brevemente qué es la computación cuántica:"

total_prompt_rate=0
total_gen_rate=0

for i in $(seq 1 $ITERATIONS); do
    echo "Iteración $i/$ITERATIONS..."

    result=$(curl -s -X POST "http://localhost:$PORT/completion" \
        -H "Content-Type: application/json" \
        -d "{
            \"prompt\": \"$PROMPT\",
            \"n_predict\": $TOKENS,
            \"temperature\": 0.7
        }")

    prompt_rate=$(echo $result | jq -r '.timings.prompt_per_second')
    gen_rate=$(echo $result | jq -r '.timings.predicted_per_second')

    echo "  Prompt: ${prompt_rate} tokens/seg"
    echo "  Generación: ${gen_rate} tokens/seg"

    total_prompt_rate=$(echo "$total_prompt_rate + $prompt_rate" | bc)
    total_gen_rate=$(echo "$total_gen_rate + $gen_rate" | bc)

    sleep 1
done

avg_prompt=$(echo "scale=2; $total_prompt_rate / $ITERATIONS" | bc)
avg_gen=$(echo "scale=2; $total_gen_rate / $ITERATIONS" | bc)

echo ""
echo "=== RESULTADOS ==="
echo "Prompt promedio: $avg_prompt tokens/seg"
echo "Generación promedio: $avg_gen tokens/seg"
```

## Resultados de Referencia

### Qwen2.5-7B en Power10 (28GB RAM)

| Métrica | Valor | Condiciones |
|---------|-------|-------------|
| Prompt eval rate | ~26 tokens/seg | Q4_K_M, 12 threads |
| Token generation | ~16.6 tokens/seg | Contexto 4096 |
| TTFT | ~500 ms | Prompt corto |
| Memoria utilizada | ~5 GB | Durante inferencia |

### Comparativa de Modelos

| Modelo | Prompt (t/s) | Generación (t/s) | RAM |
|--------|--------------|------------------|-----|
| Mistral-7B Q4_K_S | ~30 | ~18 | 4 GB |
| Qwen2.5-7B Q4_K_M | ~26 | ~16.6 | 4.7 GB |
| Llama-3-8B Q4_K_M | ~24 | ~15 | 4.7 GB |
| Qwen2.5-14B Q4_K_M | ~15 | ~10 | 8 GB |

## Monitoreo en Tiempo Real

### Uso de htop

```bash
# Instalar htop si no está disponible
dnf install -y htop

# Monitorear durante benchmark
htop
```

### Script de Monitoreo

```bash
#!/bin/bash
# monitor.sh - Monitorear recursos durante benchmark

while true; do
    echo "=== $(date) ==="
    echo "CPU:"
    top -bn1 | head -5
    echo ""
    echo "Memoria:"
    free -h
    echo ""
    echo "Contenedores:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    echo ""
    sleep 5
done
```

## Comparativa MMA vs Sin MMA

### Impacto de los Aceleradores MMA

| Configuración | Prompt (t/s) | Generación (t/s) | Mejora |
|---------------|--------------|------------------|--------|
| Power9 (sin MMA) | ~5 | ~3 | Baseline |
| **Power10 (con MMA)** | ~26 | ~16.6 | **~5x** |

> **Nota:** Los valores exactos pueden variar según la carga del sistema y configuración específica.

## Benchmark de Caso de Uso: Anonimización

### Test de Anonimización Clínica

```bash
curl -s -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "[INST] Anonimiza el siguiente texto clínico reemplazando nombres, fechas y ubicaciones con marcadores genéricos:\n\nPaciente: Juan García López\nFecha: 15/03/2024\nHospital: Centro Médico Nacional\n\nEl paciente Juan presenta síntomas de hipertensión desde hace 3 meses. [/INST]",
    "n_predict": 200,
    "temperature": 0.3
  }' | jq '.'
```

### Métricas para Anonimización

| Métrica | Objetivo | Resultado |
|---------|----------|-----------|
| Precisión | >95% PHI detectado | Evaluar manualmente |
| Recall | >90% PHI anonimizado | Evaluar manualmente |
| Latencia | <5 segundos | ~3 segundos |
| Throughput | >10 docs/min | ~20 docs/min |

## Exportar Resultados

### Formato CSV

```bash
#!/bin/bash
# export-benchmark.sh

echo "timestamp,model,prompt_rate,gen_rate,tokens" > benchmark_results.csv

for i in {1..10}; do
    timestamp=$(date +%Y-%m-%d_%H:%M:%S)
    result=$(curl -s -X POST http://localhost:8089/completion \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Test:", "n_predict": 100}')

    prompt_rate=$(echo $result | jq -r '.timings.prompt_per_second')
    gen_rate=$(echo $result | jq -r '.timings.predicted_per_second')

    echo "$timestamp,qwen-7b,$prompt_rate,$gen_rate,100" >> benchmark_results.csv
    sleep 2
done

echo "Resultados guardados en benchmark_results.csv"
```

## Interpretación de Resultados

### Rangos de Rendimiento

| Rango | Prompt (t/s) | Generación (t/s) | Evaluación |
|-------|--------------|------------------|------------|
| Excelente | >30 | >20 | Óptimo para producción |
| Bueno | 20-30 | 15-20 | Adecuado para la mayoría |
| Aceptable | 10-20 | 10-15 | Funcional, mejorable |
| Bajo | <10 | <10 | Revisar configuración |

### Factores que Afectan el Rendimiento

1. **Cuantización del modelo**: Q4_K_S > Q4_K_M > Q5_K_M
2. **Número de threads**: Optimizar según cores disponibles
3. **Tamaño del contexto**: Mayor contexto = más lento
4. **Carga del sistema**: Evitar procesos concurrentes
5. **Temperatura**: Menor temperatura = ligeramente más rápido

## Siguiente Paso

Con los benchmarks completados, puedes comparar resultados con diferentes modelos y configuraciones para optimizar tu despliegue.
