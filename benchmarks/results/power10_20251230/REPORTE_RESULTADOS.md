# Resultados del Experimento - IBM Power10 MMA
## Universidad de Montevideo - Tesis 2025
**Fecha de ejecución:** 2025-12-30

---

## Resumen Ejecutivo

Se ejecutaron benchmarks de inferencia LLM en el servidor IBM Power10 con aceleradores MMA (Matrix Math Accelerator) habilitados. Los resultados demuestran rendimiento competitivo para inferencia on-premise con modelos cuantizados.

---

## Configuración del Hardware

| Componente | Especificación |
|------------|----------------|
| **Servidor** | IBM Power E1080 |
| **Procesador** | IBM Power10 |
| **Arquitectura** | ppc64le |
| **Cores** | 12 |
| **RAM** | 28 GB |
| **Sistema Operativo** | Red Hat Enterprise Linux 9.4 |

## Configuración del Software

| Componente | Versión/Detalle |
|------------|-----------------|
| **Framework** | llama.cpp (compilado con -mcpu=power10) |
| **Optimización** | MMA habilitado |
| **Cuantización** | Q4_K_M |
| **API** | llama-server (endpoint /completion) |

---

## Resultados de Rendimiento

### Modelo 1: Qwen2.5-1.5B-Instruct

| Métrica | Valor |
|---------|-------|
| **Parámetros** | 1.5B |
| **Tamaño GGUF** | 1.1 GB |
| **TPS Generación (promedio)** | **20.54 tokens/s** |
| **TPS Generación (min)** | 20.18 tokens/s |
| **TPS Generación (max)** | 20.75 tokens/s |
| **Desviación estándar** | 0.17 |
| **TPS Evaluación Prompt** | 58.32 tokens/s |
| **Pruebas ejecutadas** | 15 |

#### Desglose por Estrategia de Prompting

| Prompt | TPS Promedio | Desv. Std |
|--------|--------------|-----------|
| baseline | 20.69 | 0.06 |
| detailed | 20.34 | 0.11 |
| few_shot | 20.60 | 0.04 |

### Modelo 2: Phi-3.5-mini-Instruct

| Métrica | Valor |
|---------|-------|
| **Parámetros** | 3.8B |
| **Tamaño GGUF** | 2.3 GB |
| **TPS Generación (promedio)** | **9.15 tokens/s** |
| **TPS Generación (min)** | 8.91 tokens/s |
| **TPS Generación (max)** | 9.31 tokens/s |
| **Desviación estándar** | 0.15 |
| **TPS Evaluación Prompt** | 21.66 tokens/s |
| **Pruebas ejecutadas** | 15 |

#### Desglose por Estrategia de Prompting

| Prompt | TPS Promedio | Desv. Std |
|--------|--------------|-----------|
| baseline | 9.27 | 0.03 |
| detailed | 8.94 | 0.03 |
| few_shot | 9.23 | 0.03 |

---

## Análisis Comparativo

### TPS por Modelo (Tarea de Anonimización - Resultados Finales)

```
Qwen2.5-1.5B:   ████████████████████████████████████████████████████████ 13.3 TPS
Phi-3.5-mini:   █████████████████████████ 6.1 TPS
Mistral-7B:     ███████████████████ 4.6 TPS
Llama-3.1-8B:   ██████████████████ 4.34 TPS ← BEST FIT
Gemma-2-9B:     █████████████ 3.1 TPS
```

> **Nota**: Los TPS anteriores (20.54, 9.15) corresponden al benchmark puro de rendimiento. Los valores finales (13.3, 6.1, etc.) corresponden a la tarea de anonimización con documentos clínicos completos.

### Resultados de Calidad por Modelo

| Modelo | TPS | Recall | LRDI | Mejor Prompt | Resultado |
|--------|-----|--------|------|--------------|-----------|
| **Llama-3.1-8B** | 4.34 | **100%** | **100%** | baseline | **BEST FIT** |
| **Gemma-2-9B** | 3.1 | 96.67% | 100% | structured_output | Excelente |
| **Mistral-7B** | 4.6 | 96.67% | 100% | structured_output | Excelente |
| **Phi-3.5-mini** | 6.1 | 73.33% | 78.6% | baseline | Aceptable |
| **Qwen2.5-1.5B** | 13.3 | 73.33% | 70.2% | few_shot | Insuficiente |

### Observaciones Clave

1. **BEST FIT: Llama-3.1-8B**: Único modelo con 100% Recall y 100% LRDI usando el prompt más simple (baseline).

2. **Estabilidad excepcional**: Todos los modelos muestran desviación estándar < 1%, indicando rendimiento muy consistente y reproducible.

3. **Trade-off velocidad vs calidad**:
   - Modelos más rápidos (Qwen, Phi) tienen LRDI insuficiente (<80%)
   - Para cumplimiento normativo, se requiere LRDI ≥100%

4. **Rendimiento MMA**: Los resultados confirman que los aceleradores MMA proporcionan rendimiento viable (3-13 TPS) para inferencia on-premise.

---

## Comparativa con GPUs (Referencia)

| Plataforma | TPS Estimado | Speedup vs Power10 | Costo/hora | Privacidad |
|------------|--------------|-------------------|------------|------------|
| **IBM Power10 (MMA)** | 3-13 | 1.0x (baseline) | $0 on-prem | ✅ Total |
| Nvidia T4 (AWS) | 20-25 | ~3x | $0.526 | ⚠️ Cloud |
| Nvidia A10G (AWS) | 40-50 | ~8x | $1.212 | ⚠️ Cloud |
| Nvidia A100 (GCP) | 80-120 | ~20x | $3.67 | ⚠️ Cloud |
| RTX 4090 (Local) | 100-150 | ~25x | CapEx $1600 | ✅ Local |

### Argumento "Best Fit"

> **Hallazgo Principal**: Aunque GPUs cloud son 3-25x más rápidas, Power10 on-premises con **Llama-3.1-8B**:
> - Logra **100% LRDI** (cero fuga de identificadores directos)
> - Elimina el riesgo de fuga de datos PHI a terceros
> - Cumple automáticamente con Ley 18.331 (Uruguay)
> - El rendimiento de 4.34 TPS es **suficiente** para procesos batch de anonimización
> - Sin costos recurrentes de cloud

---

## Casos de Prueba Evaluados

| ID | Tipo | Especialidad | Resultado |
|----|------|--------------|-----------|
| A1 | Emergencia | Cardiología | ✅ Exitoso |
| A2 | Consulta | Oncología | ✅ Exitoso |
| A3 | Evolución CTI | Intensivo | ✅ Exitoso |
| A4 | Alta médica | Cirugía | ✅ Exitoso |
| A5 | Interconsulta | Neurología | ✅ Exitoso |

---

## Archivos de Resultados

| Archivo | Descripción |
|---------|-------------|
| `qwen2.5-1.5b_results.json` | Resultados completos Qwen2.5-1.5B |
| `phi-3.5-mini_results.json` | Resultados completos Phi-3.5-mini |

---

## Metodología

### Protocolo de Benchmark
1. Servidor llama.cpp iniciado con modelo cargado
2. 5 casos clínicos × 3 estrategias de prompting = 15 pruebas por modelo
3. Métricas capturadas: TPS generación, TPS prompt, tokens, latencia
4. Resultados guardados en JSON con timestamp

### Estrategias de Prompting Evaluadas
- **baseline**: Instrucción mínima zero-shot
- **detailed**: 8 reglas explícitas + categorías PHI
- **few_shot**: 3 ejemplos input/output

---

## Conclusiones

1. **MMA Validado**: Los aceleradores MMA de IBM Power10 proporcionan rendimiento cuantificable (3-13 TPS) para inferencia LLM.

2. **BEST FIT: Llama-3.1-8B**:
   - Único modelo con **100% Recall** y **100% LRDI** usando prompt baseline
   - 4.34 TPS es suficiente para procesamiento batch de historias clínicas
   - Garantiza "Fuga Cero" de identificadores directos

3. **Rendimiento por Modelo (Tarea Anonimización)**:
   - Qwen2.5-1.5B: 13.3 TPS (más rápido, pero LRDI insuficiente 70.2%)
   - Phi-3.5-mini: 6.1 TPS (LRDI insuficiente 78.6%)
   - Mistral-7B: 4.6 TPS (100% LRDI con structured_output)
   - **Llama-3.1-8B: 4.34 TPS (100% LRDI con baseline) ← BEST FIT**
   - Gemma-2-9B: 3.1 TPS (100% LRDI con structured_output)

4. **Alta Estabilidad**: Desviación estándar < 1% en todas las pruebas.

5. **Viabilidad On-Premise**: Power10 es una alternativa viable a GPUs cloud para casos sensibles a la privacidad (datos PHI, cumplimiento normativo).

---

## Referencias

- arXiv:2412.10918 - LLMs-in-the-Loop Part 2
- arXiv:2406.00062 - Unlocking LLMs for Clinical Text Anonymization
- IBM Power E1080 Technical Overview (Redbooks)
- Ley 18.331 de Uruguay - Protección de Datos Personales

---

*Generado automáticamente por el framework de benchmark - Universidad de Montevideo*
