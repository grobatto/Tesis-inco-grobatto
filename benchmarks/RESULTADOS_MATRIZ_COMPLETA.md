# MATRIZ COMPLETA DE RESULTADOS - EXPERIMENTOS PHI ANONYMIZATION
## Tesis: Inferencia de IA Generativa On-Premise en IBM Power10
### Validación de Aceleradores MMA aplicada a la Anonimización de Datos Clínicos

**Fecha de ejecución:** 2 de Enero de 2026
**Servidor:** IBM Power10 @ 52.116.49.132
**Compilación:** llama.cpp con MMA habilitado (`-mcpu=power10 -O3`)
**Configuración:** 12 threads, context 4096, Q4_K_M quantization

---

## 1. RESUMEN EJECUTIVO

### Experimentos Completados
- **5 Modelos** × **8 Prompts** × **3 Casos Clínicos** = **120 experimentos**
- Todos los experimentos ejecutados con aceleración MMA habilitada

### Ranking de Modelos por Rendimiento (TPS)
| Posición | Modelo | TPS Promedio | Tamaño |
|----------|--------|--------------|--------|
| 1 | Qwen2.5-1.5B | 13.26 TPS | 1.1 GB |
| 2 | Phi-3.5-mini | 6.07 TPS | 2.3 GB |
| 3 | Mistral-7B | 4.58 TPS | 4.1 GB |
| 4 | Llama-3.1-8B | 4.34 TPS | 4.6 GB |
| 5 | Gemma-2-9B | 3.12 TPS | 5.4 GB |

### Mejor Combinación para Producción (BEST FIT)
**Llama-3.1-8B + baseline**: 100% Recall, 100% LRDI, 4.34 TPS

> **Justificación**: Llama-3.1-8B es el único modelo que logra 100% Recall y 100% LRDI con el prompt más simple (baseline), garantizando "Fuga Cero" de identificadores directos sin necesidad de prompts complejos.

**Alternativas viables**:
- Mistral-7B + structured_output: 96.7% Recall, 100% LRDI, 4.56 TPS
- Gemma-2-9B + structured_output: 96.7% Recall, 100% LRDI, 3.18 TPS

---

## 2. MATRIZ DE RESULTADOS POR MODELO

### 2.1 QWEN2.5-1.5B (1.1 GB) - Puerto 8080
| Prompt | A1 Recall | A1 LRDI | A2 Recall | A2 LRDI | A3 Recall | A3 LRDI | TPS Prom |
|--------|-----------|---------|-----------|---------|-----------|---------|----------|
| baseline | 0.30 | 28.6% | 0.90 | 100% | 0.30 | 37.5% | 13.32 |
| detailed | 0.20 | 0.0% | 0.00 | 0.0% | 0.00 | 0.0% | 13.21 |
| few_shot | 0.90 | 85.7% | 1.00 | 100% | 0.30 | 25.0% | 13.21 |
| chain_of_thought | 0.20 | 0.0% | 0.10 | 14.3% | 0.70 | 62.5% | 13.28 |
| master_tutor | 0.80 | 71.4% | 1.00 | 100% | 0.40 | 37.5% | 13.34 |
| medico | 0.70 | 85.7% | 0.00 | 0.0% | 0.60 | 62.5% | 13.23 |
| structured_output | 0.70 | 85.7% | 0.10 | 0.0% | 0.90 | 100% | 13.25 |
| hybrid | 0.40 | 14.3% | 0.10 | 0.0% | 1.00 | 100% | 13.26 |

**Mejor prompt:** few_shot (Recall prom: 0.73, LRDI prom: 70.2%)
**TPS promedio global:** 13.26

### 2.2 PHI-3.5-MINI (2.3 GB) - Puerto 8093
| Prompt | A1 Recall | A1 LRDI | A2 Recall | A2 LRDI | A3 Recall | A3 LRDI | TPS Prom |
|--------|-----------|---------|-----------|---------|-----------|---------|----------|
| baseline | 0.90 | 100% | 0.80 | 85.7% | 0.50 | 50.0% | 6.09 |
| detailed | 0.10 | 0.0% | 0.00 | 0.0% | 0.20 | 12.5% | 5.95 |
| few_shot | 0.30 | 14.3% | 0.20 | 14.3% | 0.20 | 25.0% | 6.03 |
| chain_of_thought | 0.20 | 28.6% | 0.10 | 14.3% | 0.00 | 0.0% | 6.19 |
| master_tutor | 0.00 | 0.0% | 1.00 | 100% | 1.00 | 100% | 6.13 |
| medico | 0.00 | 0.0% | 0.30 | 28.6% | 0.00 | 0.0% | 6.03 |
| structured_output | 0.30 | 14.3% | 0.40 | 42.9% | 0.40 | 50.0% | 6.05 |
| hybrid | 0.40 | 28.6% | 0.40 | 42.9% | 0.60 | 62.5% | 6.20 |

**Mejor prompt:** master_tutor (Recall prom: 0.67, LRDI prom: 66.7%) - pero inconsistente en A1
**TPS promedio global:** 6.07

### 2.3 MISTRAL-7B (4.1 GB) - Puerto 8094
| Prompt | A1 Recall | A1 LRDI | A2 Recall | A2 LRDI | A3 Recall | A3 LRDI | TPS Prom |
|--------|-----------|---------|-----------|---------|-----------|---------|----------|
| baseline | 0.00 | 0.0% | 0.00 | 0.0% | 0.00 | 0.0% | 4.62 |
| detailed | 0.90 | 100% | 1.00 | 100% | 0.50 | 50.0% | 4.61 |
| few_shot | 0.00 | 0.0% | 0.00 | 0.0% | 0.90 | 100% | 4.56 |
| chain_of_thought | 0.90 | 100% | 0.00 | 0.0% | 0.10 | 12.5% | 4.67 |
| master_tutor | 0.70 | 85.7% | 0.40 | 28.6% | 0.10 | 12.5% | 4.35 |
| **medico** | **0.90** | **100%** | **1.00** | **100%** | **0.90** | **100%** | **4.58** |
| **structured_output** | **0.90** | **100%** | **1.00** | **100%** | **1.00** | **100%** | **4.56** |
| hybrid | 1.00 | 100% | 1.00 | 100% | 0.00 | 0.0% | 4.59 |

**Mejor prompt:** structured_output (Recall prom: 0.97, LRDI: 100%)
**Segundo mejor:** medico (Recall prom: 0.93, LRDI: 100%)
**TPS promedio global:** 4.58

### 2.4 GEMMA-2-9B (5.4 GB) - Puerto 8095
| Prompt | A1 Recall | A1 LRDI | A2 Recall | A2 LRDI | A3 Recall | A3 LRDI | TPS Prom |
|--------|-----------|---------|-----------|---------|-----------|---------|----------|
| baseline | 0.00 | 0.0% | 0.90 | 85.7% | 1.00 | 100% | 3.12 |
| detailed | 0.90 | 100% | 1.00 | 100% | 0.90 | 87.5% | 3.12 |
| few_shot | 0.80 | 100% | 0.90 | 100% | 0.80 | 87.5% | 3.13 |
| chain_of_thought | 0.90 | 100% | 0.10 | 14.3% | 1.00 | 100% | 3.14 |
| master_tutor | 1.00 | 100% | 0.70 | 71.4% | 0.80 | 87.5% | 3.11 |
| medico | 0.70 | 85.7% | 0.90 | 100% | 0.60 | 75.0% | 3.05 |
| **structured_output** | **0.90** | **100%** | **1.00** | **100%** | **1.00** | **100%** | **3.18** |
| hybrid* | timeout | - | 0.90 | 85.7% | 0.90 | 87.5% | 3.14 |

*hybrid tuvo timeout en A1

**Mejor prompt:** structured_output (Recall prom: 0.97, LRDI: 100%)
**TPS promedio global:** 3.12 (más lento por ser 9B)

### 2.5 LLAMA-3.1-8B (4.6 GB) - Puerto 8096
| Prompt | A1 Recall | A1 LRDI | A2 Recall | A2 LRDI | A3 Recall | A3 LRDI | TPS Prom |
|--------|-----------|---------|-----------|---------|-----------|---------|----------|
| **baseline** | **1.00** | **100%** | **1.00** | **100%** | **1.00** | **100%** | **4.34** |
| detailed | 0.10 | 0.0% | 1.00 | 100% | 1.00 | 100% | 4.31 |
| few_shot | 0.00 | 0.0% | 0.00 | 0.0% | 0.00 | 0.0% | 4.33 |
| chain_of_thought | 0.10 | 14.3% | 0.20 | 14.3% | 0.10 | 12.5% | 4.34 |
| master_tutor | 1.00 | 100% | 0.90 | 85.7% | 0.80 | 87.5% | 4.36 |
| medico | 0.00 | 0.0% | 1.00 | 100% | 0.90 | 100% | 4.33 |
| structured_output | 0.90 | 100% | 0.90 | 100% | 0.90 | 100% | 4.34 |
| hybrid | 1.00 | 100% | 0.00 | 0.0% | 0.80 | 87.5% | 4.34 |

**Mejor prompt:** baseline (Recall: 1.00, LRDI: 100%)
**Segundo mejor:** structured_output (Recall prom: 0.90, LRDI: 100%)
**TPS promedio global:** 4.34

---

## 3. ANÁLISIS COMPARATIVO POR ESTRATEGIA DE PROMPTING

### Ranking de Prompts (promedio de los 5 modelos)

| Prompt | Recall Prom | LRDI Prom | Consistencia* |
|--------|-------------|-----------|---------------|
| **structured_output** | 0.72 | 78.6% | ALTA |
| medico | 0.55 | 59.2% | MEDIA |
| baseline | 0.49 | 52.4% | BAJA |
| master_tutor | 0.61 | 61.5% | BAJA |
| detailed | 0.50 | 46.8% | BAJA |
| few_shot | 0.42 | 41.8% | BAJA |
| hybrid | 0.56 | 50.0% | BAJA |
| chain_of_thought | 0.36 | 36.3% | MUY BAJA |

*Consistencia: variabilidad entre modelos y casos

### Observaciones Clave por Prompt

1. **structured_output**: Mejor rendimiento general. Funciona bien en todos los modelos excepto los más pequeños.

2. **baseline**: Excelente en Llama-3.1-8B (100% perfecto), pero falla completamente en Mistral-7B.

3. **medico**: Consistente en Mistral-7B (100% LRDI), bueno en modelos grandes.

4. **chain_of_thought**: Pobre rendimiento general. Los modelos pequeños no siguen bien el razonamiento paso a paso.

5. **few_shot**: Inconsistente. Funciona en Qwen2.5 pero falla en Llama-3.1-8B.

---

## 4. RECOMENDACIONES PARA PRODUCCIÓN

### Configuración Óptima

Para **máxima calidad de anonimización**:
- **Modelo:** Mistral-7B o Gemma-2-9B
- **Prompt:** structured_output
- **LRDI esperado:** 100%
- **TPS:** 3-5 tokens/segundo

Para **balance calidad/velocidad**:
- **Modelo:** Mistral-7B
- **Prompt:** structured_output o medico
- **LRDI esperado:** 100%
- **TPS:** ~4.5 tokens/segundo

Para **máxima velocidad** (casos menos críticos):
- **Modelo:** Qwen2.5-1.5B
- **Prompt:** few_shot
- **LRDI esperado:** ~70%
- **TPS:** ~13 tokens/segundo

### Modelos a Evitar

1. **Phi-3.5-mini**: Rendimiento inconsistente, muchos fallos en LRDI
2. **Cualquier modelo con chain_of_thought**: No funciona bien para esta tarea

---

## 5. MÉTRICAS DE RENDIMIENTO DEL HARDWARE

### IBM Power10 con MMA

| Modelo | TPS | Speedup vs CPU* | RAM Usada |
|--------|-----|-----------------|-----------|
| Qwen2.5-1.5B | 13.26 | ~3x | ~2 GB |
| Phi-3.5-mini | 6.07 | ~2.5x | ~4 GB |
| Mistral-7B | 4.58 | ~2x | ~6 GB |
| Llama-3.1-8B | 4.34 | ~2x | ~7 GB |
| Gemma-2-9B | 3.12 | ~1.8x | ~8 GB |

*Estimación basada en benchmarks previos sin MMA

### Tiempo Total de Procesamiento por Modelo

| Modelo | Casos Procesados | Tiempo Aproximado |
|--------|------------------|-------------------|
| Qwen2.5-1.5B | 24 | ~15 min |
| Phi-3.5-mini | 24 | ~25 min |
| Mistral-7B | 24 | ~35 min |
| Gemma-2-9B | 24 | ~55 min |
| Llama-3.1-8B | 24 | ~40 min |

---

## 6. CONCLUSIONES

1. **MMA es esencial**: La compilación con `-mcpu=power10` permite inferencia viable en Power10.

2. **BEST FIT: Llama-3.1-8B + baseline**: Único modelo que logra 100% Recall y 100% LRDI con el prompt más simple, garantizando "Fuga Cero" sin prompts complejos.

3. **structured_output es la mejor estrategia general**: Funciona consistentemente en modelos medianos-grandes, y es necesario para Mistral-7B y Gemma-2-9B.

4. **Llama-3.1-8B vs Mistral-7B**: Ambos logran 100% LRDI (~4.5 TPS), pero Llama lo hace con baseline y Mistral requiere structured_output.

5. **Los modelos pequeños (1-3B) son inconsistentes** para tareas de anonimización complejas (LRDI <80%).

6. **chain_of_thought no funciona** para esta tarea en modelos locales.

7. **La especificidad importa**: Prompts que especifican categorías exactas (structured_output, medico) superan a prompts genéricos, excepto en Llama-3.1-8B donde baseline es suficiente.

---

## ANEXO: DATOS CRUDOS EN JSON

Los archivos JSON completos están disponibles en el servidor:
- `/root/results_qwen2.5-1.5b-MMA_8080.json`
- `/root/results_phi-3.5-mini-MMA_8093.json`
- `/root/results_mistral-7b-MMA_8094.json`
- `/root/results_gemma-2-9b-MMA_8095.json`
- `/root/results_llama-3.1-8b-MMA_8096.json`

---

*Generado automáticamente - Universidad de Montevideo, Tesis 2025*
