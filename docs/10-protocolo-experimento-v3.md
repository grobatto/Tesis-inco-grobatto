# Protocolo de Experimentación v3.0

**Validación de Aceleradores MMA en IBM Power10 para Inferencia GenAI**

Universidad de Montevideo - Tesis 2025

---

## Resumen Ejecutivo

Este protocolo define los experimentos para demostrar el valor de los aceleradores MMA (Matrix Math Accelerator) de IBM Power10 para inferencia de modelos de lenguaje. Se utiliza la anonimización de datos clínicos como caso de uso para validar la hipótesis.

**Hipótesis:** Los aceleradores MMA integrados en IBM Power10 proporcionan ganancia de rendimiento cuantificable para inferencia de IA Generativa on-premise, ofreciendo una alternativa viable a GPUs cloud para casos de uso sensibles a la privacidad.

---

## 1. Configuración del Entorno

### 1.1 Hardware

```
Servidor: IBM Power E1080
Procesador: Power10 con MMA
Cores: 12
RAM: 28 GB
Sistema: Red Hat Enterprise Linux 9.4
```

### 1.2 Software

```
Framework: llama.cpp (compilado con soporte MMA)
Contenedor: Docker con optimizaciones Power10
Cuantización: Q4_K_M para todos los modelos
Servidor API: llama-server (modo completion)
```

### 1.3 Verificación MMA

Antes de ejecutar experimentos, verificar que MMA está activo:

```bash
# Verificar soporte MMA
lscpu | grep -i mma

# O usando ppc64_cpu
ppc64_cpu --info | grep MMA
```

---

## 2. Modelos Configurados

| Modelo | Puerto | Archivo GGUF | RAM Est. |
|--------|--------|--------------|----------|
| phi-3.5-mini | 8093 | phi-3.5-mini-instruct.Q4_K_M.gguf | ~3 GB |
| mistral-nemo-12b | 8097 | mistral-nemo-12b-instruct-2407.Q4_K_M.gguf | ~8 GB |
| qwen2.5-7b | 8089 | qwen2.5-7b-instruct.Q4_K_M.gguf | ~5 GB |
| biomistral-7b | 8092 | biomistral-7b.Q4_K_M.gguf | ~5 GB |
| llama-3.1-8b | 8094 | llama-3.1-8b-instruct.Q4_K_M.gguf | ~5 GB |
| gemma-2-9b | 8095 | gemma-2-9b-it.Q4_K_M.gguf | ~6 GB |

### Iniciar modelo (ejemplo):

```bash
cd /root/llama.cpp

./llama-server \
  -m /root/models/mistral-nemo-12b-instruct-2407.Q4_K_M.gguf \
  --host 0.0.0.0 \
  --port 8097 \
  -c 8192 \
  -t 12 \
  --log-disable
```

---

## 3. Experimentos

### 3.1 Experimento 1: Benchmark de Rendimiento MMA

**Objetivo:** Medir TPS, latencia y throughput para cada modelo.

**Ejecución:**

```bash
cd /path/to/benchmarks

python experiment_runner.py --rendimiento \
  --modelos phi-3.5-mini mistral-nemo-12b qwen2.5-7b biomistral-7b llama-3.1-8b gemma-2-9b \
  --iteraciones 3 \
  --output results/exp1_rendimiento
```

**Métricas capturadas:**
- TPS generación
- TPS evaluación de prompt
- Latencia primer token (ms)
- Latencia total (ms)
- Desviación estándar

**Duración estimada:** ~30 minutos

### 3.2 Experimento 2: Comparativa de Prompts

**Objetivo:** Identificar la mejor estrategia de prompting.

**Ejecución:**

```bash
python experiment_runner.py --prompts \
  --modelo mistral-nemo-12b \
  --output results/exp2_prompts
```

**Estrategias evaluadas:**
1. baseline (zero-shot simple)
2. detailed (8 reglas)
3. few_shot (3 ejemplos)
4. chain_of_thought (5 pasos)
5. master_tutor (protocolo tutor)
6. medico (Ley 18.331)
7. structured_output (categorías explícitas)
8. hybrid (few-shot + CoT)

**Duración estimada:** ~45 minutos

### 3.3 Experimento 3: Evaluación de Calidad

**Objetivo:** Validar calidad con métricas de papers académicos.

**Ejecución:**

```bash
python experiment_runner.py --calidad \
  --modelos mistral-nemo-12b phi-3.5-mini qwen2.5-7b \
  --iteraciones 5 \
  --output results/exp3_calidad
```

**Métricas evaluadas:**
- Precision, Recall, F1-micro, F1-macro
- ALID (Average Levenshtein Index of Dissimilarity)
- LR (Levenshtein Recall)
- LRDI (LR Identificadores Directos)
- LRQI (LR Cuasi-Identificadores)

**Duración estimada:** ~90 minutos

---

## 4. Ejecución Completa

Para ejecutar todos los experimentos en secuencia:

```bash
python experiment_runner.py --all \
  --host localhost \
  --output results/experimentos_$(date +%Y%m%d)
```

**Duración total estimada:** ~3 horas

---

## 5. Análisis de Resultados

### 5.1 Resumen Rápido

```bash
python results_analyzer.py --resumen --results-dir results/
```

### 5.2 Reporte Completo

```bash
python results_analyzer.py --reporte \
  --results-dir results/ \
  --output-dir reports/
```

### 5.3 Gráficos

```bash
python results_analyzer.py --graficos \
  --results-dir results/ \
  --output-dir reports/
```

---

## 6. Estructura de Archivos de Resultados

```
results/
├── benchmark_rendimiento_YYYYMMDD_HHMMSS.json
├── comparativa_prompts_YYYYMMDD_HHMMSS.json
├── evaluacion_calidad_YYYYMMDD_HHMMSS.json
└── experimentos_completos_YYYYMMDD_HHMMSS.json

reports/
├── reporte_resultados_YYYYMMDD_HHMMSS.md
├── grafico_tps_modelos.png
└── grafico_calidad_velocidad.png
```

---

## 7. Formato de Resultados JSON

### Ejemplo de resultado individual:

```json
{
  "modelo": "mistral-nemo-12b",
  "prompt": "detailed",
  "caso": "A1",
  "iteracion": 1,
  "rendimiento": {
    "tps_generacion": 12.5,
    "tps_prompt": 34.7,
    "latencia_total_ms": 2500,
    "tokens_generados": 380
  },
  "calidad": {
    "precision": 0.94,
    "recall": 0.91,
    "f1_micro": 0.925,
    "f1_macro": 0.918,
    "alid": 95.2,
    "lr": 92.0,
    "lrdi": 100.0,
    "lrqi": 88.5
  },
  "entidades": {
    "total_esperadas": 15,
    "true_positives": 14,
    "false_negatives": 1,
    "directos_escapados": 0
  }
}
```

---

## 8. Criterios de Éxito

### 8.1 Rendimiento MMA

| Criterio | Umbral | Justificación |
|----------|--------|---------------|
| TPS mínimo | > 10 | Suficiente para batch processing |
| Estabilidad | std < 20% | Resultados reproducibles |
| Disponibilidad | > 95% | Modelos responden correctamente |

### 8.2 Calidad de Anonimización

| Criterio | Umbral | Justificación |
|----------|--------|---------------|
| LRDI | = 100% | Todos los identificadores directos deben anonimizarse |
| Recall | > 0.90 | Alta detección de PHI (prioridad privacidad) |
| F1-micro | > 0.85 | Balance precision/recall aceptable |

---

## 9. Comparativa GPU Documentada

| Plataforma | TPS Est. | Speedup | Costo/hora | Fuente |
|------------|----------|---------|------------|--------|
| **Power10 MMA** | 13-17 | 1.0x | $0 on-prem | Este trabajo |
| Nvidia T4 (AWS) | 20-25 | ~1.5x | $0.526 | [AWS g4dn pricing](https://aws.amazon.com/ec2/instance-types/g4/) |
| Nvidia A10G (AWS) | 40-50 | ~3x | $1.212 | [AWS g5 pricing](https://aws.amazon.com/ec2/instance-types/g5/) |
| Nvidia A100 (GCP) | 80-120 | ~7x | $3.67 | [GCP A2 pricing](https://cloud.google.com/compute/gpus-pricing) |
| RTX 4090 (Local) | 100-150 | ~10x | CapEx $1600 | [llama.cpp benchmarks](https://github.com/ggerganov/llama.cpp) |

---

## 10. Checklist Pre-Experimento

- [ ] Servidor Power10 accesible via SSH
- [ ] MMA verificado activo (`lscpu | grep mma`)
- [ ] Modelos GGUF en `/root/models/`
- [ ] llama.cpp compilado con soporte MMA
- [ ] Puerto del modelo a evaluar respondiendo
- [ ] Scripts de benchmark actualizados
- [ ] Directorio de resultados creado
- [ ] Suficiente RAM disponible

---

## 11. Troubleshooting

### Modelo no responde

```bash
# Verificar si el proceso está corriendo
ps aux | grep llama-server

# Verificar puerto
curl http://localhost:8097/health
```

### Error de memoria

```bash
# Verificar RAM disponible
free -h

# Reducir contexto del modelo
./llama-server -m modelo.gguf -c 2048  # Reducir de 8192 a 2048
```

### Timeout en requests

```bash
# Aumentar timeout en experiment_runner.py
llamar_modelo(prompt, puerto, timeout=180)  # Default: 120
```

---

## 12. Siguientes Pasos Post-Experimento

1. Revisar resultados JSON generados
2. Ejecutar análisis con `results_analyzer.py`
3. Generar tablas para la tesis
4. Crear gráficos de rendimiento
5. Documentar conclusiones
6. Push resultados al repositorio

---

## Referencias

- arXiv:2412.10918 - LLMs-in-the-Loop Part 2
- arXiv:2406.00062 - Unlocking LLMs for Clinical Text Anonymization
- i2b2 2014 De-identification Challenge
- IBM Power E1080 Technical Overview (Redbooks)
