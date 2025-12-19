# Comparativa: IBM Power10 (MMA) vs GPUs para Inferencia LLM

Universidad de Montevideo - Tesis 2025

Este documento compara el rendimiento de inferencia de modelos LLM (específicamente Mistral 7B Q4) en IBM Power10 con aceleradores MMA vs. GPUs en la nube y de consumo.

## Resumen Ejecutivo

| Plataforma | TPS Generación | Costo/hora | Privacidad | Latencia Red |
|------------|----------------|------------|------------|--------------|
| **IBM Power10 (MMA)** | 13-20 t/s | $0 (on-prem) | ✅ Total | Ninguna |
| Nvidia T4 (Cloud) | 20-25 t/s | ~$0.35/h | ⚠️ Cloud | Media |
| Nvidia A10 (Cloud) | 40-50 t/s | ~$0.80/h | ⚠️ Cloud | Media |
| Nvidia A100 (Cloud) | 80-100 t/s | ~$3.00/h | ⚠️ Cloud | Media |
| RTX 4090 (Consumer) | 100-150 t/s | N/A (capital) | ✅ Local | Ninguna |

---

## Datos de Referencia

### IBM Power10 con MMA (Datos Propios)

Resultados obtenidos en servidor demo-inco-power-ai.cloud.ibm.com:
- Arquitectura: ppc64le (IBM POWER10)
- RAM: 28 GB
- Docker: quay.io/daniel_casali/llama.cpp-mma:v8

| Modelo | Cuantización | TPS Generación | TPS Prompt |
|--------|--------------|----------------|------------|
| Qwen2.5-7B | Q4_K_M | 13.1 t/s | 34.7 t/s |
| Mistral-7B | Q4_K_S | 19.9 t/s | 33.2 t/s |
| Phi-3.5-mini | Q4_K_M | 16.8 t/s (esperado) | - |

**Fuente:** Benchmarks internos del proyecto (30 Nov 2025)

### Nvidia T4 (Cloud)

GPU de nivel de entrada para inferencia en la nube.

| Especificaciones | Valor |
|------------------|-------|
| VRAM | 16 GB GDDR6 |
| Bandwidth | 300 GB/s |
| CUDA Cores | 2,560 |
| Tensor Cores | 320 |

**Rendimiento estimado (Mistral 7B Q4):**
- Token generation: ~20-25 t/s
- Tiempo por token: ~46 ms
- Costo AWS (g4dn.xlarge): $0.526/hora on-demand

**Cálculo teórico:** (2 × 7B bytes) / (300 GB/s) = 46 ms/token ≈ 22 t/s

**Fuentes:**
- [Baseten: Guide to LLM Inference](https://www.baseten.co/blog/llm-transformer-inference-guide/)
- [AWS G4 Instances](https://aws.amazon.com/ec2/instance-types/g4/)

### Nvidia A10 (Cloud)

GPU de rango medio optimizada para inferencia ML.

| Especificaciones | Valor |
|------------------|-------|
| VRAM | 24 GB GDDR6 |
| Bandwidth | 600 GB/s |
| CUDA Cores | 9,216 |
| Tensor Cores | 288 |

**Rendimiento estimado (Mistral 7B Q4):**
- Token generation: ~40-50 t/s
- Tiempo por token: ~23 ms
- Es aproximadamente 2-3x más rápida que T4
- Costo AWS (g5.xlarge): ~$0.80-1.00/hora on-demand

**Fuentes:**
- [Nucleusbox: How to Choose GPU for LLMs](https://www.nucleusbox.com/choose-gpu-for-llms-t4-a10-a100/)
- [LLM Inference Bench - ArXiv](https://arxiv.org/html/2411.00136v1)

### Nvidia A100 (Cloud)

GPU de datacenter de alto rendimiento.

| Especificaciones | Valor |
|------------------|-------|
| VRAM | 40/80 GB HBM2e |
| Bandwidth | 1,555/2,039 GB/s |
| CUDA Cores | 6,912 |
| Tensor Cores | 432 |

**Rendimiento estimado (Mistral 7B Q4):**
- Token generation: ~80-100 t/s
- Aproximadamente 4x más rápida que A10
- Costo AWS (p4d.24xlarge): ~$3.00+/hora por GPU

**Fuentes:**
- [Hardware Corner: GPU Ranking for LLMs](https://www.hardware-corner.net/gpu-ranking-local-llm/)

### RTX 4090 (Consumer)

GPU de consumo de gama alta.

| Especificaciones | Valor |
|------------------|-------|
| VRAM | 24 GB GDDR6X |
| Bandwidth | 1,008 GB/s |
| CUDA Cores | 16,384 |
| Tensor Cores | 512 |

**Rendimiento medido (Mistral 7B Q4):**
- Token generation: ~100-150 t/s
- Tiempo por token: ~6.7 ms (4.5-bit weights)
- Alcanza 58% del pico teórico con llama.cpp
- Costo: ~$1,600 USD (capital inicial)

**Fuentes:**
- [zeux.io: LLM Inference Speed of Light](https://zeux.io/2024/03/15/llm-inference-sol/)
- [CimpleO: LLM Inference Benchmark RTX4090](https://cimpleo.com/blog/llm-inference-benchmark-part-1-xeon--rtx4090-gpu/)

---

## Análisis Comparativo

### Rendimiento vs. Costo

```
           TPS
    150 ┤                                          ★ RTX 4090
        │
    100 ┤                               ★ A100
        │
     50 ┤                    ★ A10
        │
     25 ┤         ★ T4
        │
     15 ┤  ★ Power10 (MMA)
        │
      0 └────────────────────────────────────────────────
          $0      $0.50     $1.00     $2.00     $3.00+
                        Costo/hora (Cloud)
```

### Costo Total de Propiedad (TCO) - Escenario 1 año

**Caso de uso:** Procesamiento batch nocturno, 8 horas/día, 250 días/año = 2,000 horas

| Plataforma | Costo/hora | Costo Anual | TPS | Costo por 1M tokens |
|------------|------------|-------------|-----|---------------------|
| IBM Power10 (on-prem) | $0 | $0* | 15 | $0.00 |
| T4 Cloud | $0.52 | $1,040 | 22 | $0.013 |
| A10 Cloud | $0.80 | $1,600 | 45 | $0.010 |
| A100 Cloud | $3.00 | $6,000 | 90 | $0.019 |

*Asumiendo infraestructura Power10 existente (caso INCO/Facultad de Medicina)

### Análisis de Privacidad

| Plataforma | Ubicación Datos | Riesgo de Fuga | Cumplimiento Ley 18.331 |
|------------|-----------------|----------------|-------------------------|
| IBM Power10 (on-prem) | Local | Mínimo | ✅ Completo |
| Cloud (cualquier GPU) | Datacenter externo | Medio-Alto | ⚠️ Requiere DPA |

**Consideraciones de privacidad para datos médicos:**
- Los datos clínicos nunca salen del perímetro de la organización
- No hay transmisión de PHI (Protected Health Information) por internet
- Cumplimiento nativo con regulaciones de protección de datos
- Eliminación del riesgo de brechas en proveedores cloud

---

## Conclusiones para la Tesis

### 1. Power10 es suficiente para el caso de uso

Con ~15 tokens/segundo, IBM Power10 puede procesar:
- **54,000 tokens/hora** = ~135 páginas de texto médico
- **432,000 tokens/día** (8 horas) = ~1,080 páginas
- **Suficiente para procesamiento batch nocturno** de historias clínicas

### 2. La privacidad justifica la diferencia de rendimiento

Aunque GPUs en la nube son 2-5x más rápidas:
- El procesamiento on-premises elimina completamente el riesgo de fuga de datos PHI
- No hay costos recurrentes de cloud ni contratos de procesamiento de datos
- Cumplimiento automático con Ley 18.331 y regulaciones de salud

### 3. El hardware MMA está subutilizado

La hipótesis de la tesis se confirma:
- Los aceleradores matriciales (MMA) en Power10 permiten inferencia eficiente de LLMs
- El rendimiento de ~13-20 TPS es competitivo con GPUs de entrada (T4)
- Representa una alternativa viable para organizaciones con infraestructura Power existente

### 4. Recomendación final

> **"Para des-identificación de datos clínicos en la Facultad de Medicina UdelaR,
> IBM Power10 con MMA ofrece el balance óptimo entre rendimiento, costo y
> privacidad. El procesamiento batch nocturno a 15 t/s es suficiente para
> el volumen de historias clínicas, mientras que la ejecución on-premises
> garantiza cumplimiento regulatorio sin costos adicionales de cloud."**

---

## Referencias

1. [Baseten: Guide to LLM Inference and Performance](https://www.baseten.co/blog/llm-transformer-inference-guide/)
2. [zeux.io: LLM Inference Speed of Light](https://zeux.io/2024/03/15/llm-inference-sol/)
3. [Nucleusbox: How to Choose GPU for LLMs](https://www.nucleusbox.com/choose-gpu-for-llms-t4-a10-a100/)
4. [Hardware Corner: GPU Ranking for Local LLM](https://www.hardware-corner.net/gpu-ranking-local-llm/)
5. [AWS EC2 G4 Instances](https://aws.amazon.com/ec2/instance-types/g4/)
6. [Google Cloud GPU Pricing](https://cloud.google.com/compute/gpus-pricing)
7. [CimpleO: LLM Inference Benchmark](https://cimpleo.com/blog/llm-inference-benchmark-part-1-xeon--rtx4090-gpu/)
8. [ArXiv: LLM-Inference-Bench](https://arxiv.org/html/2411.00136v1)
9. [GetDeploying: GPU Price Comparison 2025](https://getdeploying.com/reference/cloud-gpu)
