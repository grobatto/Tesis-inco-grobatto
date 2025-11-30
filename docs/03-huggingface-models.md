# 03 - Cómo Descargar Modelos de Hugging Face

## Introducción

Hugging Face es la plataforma principal para descargar modelos de Machine Learning. Para usar modelos con `llama.cpp`, necesitamos modelos en formato **GGUF** (GPT-Generated Unified Format).

## Formato GGUF

### ¿Qué es GGUF?

GGUF es un formato binario diseñado para almacenar modelos de lenguaje de forma eficiente. Es el sucesor de GGML y es el formato nativo de `llama.cpp`.

### Cuantización

Los modelos GGUF vienen en diferentes niveles de cuantización:

| Cuantización | Tamaño | Calidad | Uso Recomendado |
|--------------|--------|---------|-----------------|
| **Q8_0** | Mayor | Mejor | Máxima calidad, más RAM |
| **Q6_K** | Grande | Muy buena | Balance alto |
| **Q5_K_M** | Medio | Buena | Balance medio-alto |
| **Q4_K_M** | Pequeño | Aceptable | **Recomendado para 28GB RAM** |
| **Q4_K_S** | Menor | Básica | Recursos limitados |
| **Q3_K_M** | Mínimo | Baja | Solo pruebas |

> Para nuestro servidor con 28GB RAM, usamos **Q4_K_M** como estándar.

## Modelos Recomendados

### bartowski (Repositorio de Confianza)

El usuario [bartowski](https://huggingface.co/bartowski) mantiene versiones GGUF optimizadas de los modelos más populares.

### Modelos Disponibles

| Modelo | URL | Tamaño | Descripción |
|--------|-----|--------|-------------|
| **Qwen2.5-7B** | [Link](https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF) | ~4.7 GB | Balance ideal |
| **Mistral-7B** | [Link](https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF) | ~4 GB | Rápido y eficiente |
| **Llama-3-8B** | [Link](https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF) | ~4.7 GB | Meta's latest |
| **Qwen2.5-14B** | [Link](https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF) | ~8 GB | Mayor capacidad |

## Métodos de Descarga

### Método 1: wget (Recomendado)

```bash
# Descargar Qwen2.5-7B
wget "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf" \
  -O ~/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf
```

### Método 2: curl

```bash
# Descargar con curl
curl -L "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf" \
  -o ~/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf
```

### Método 3: huggingface-cli

```bash
# Instalar huggingface-cli
pip install huggingface_hub

# Descargar modelo
huggingface-cli download bartowski/Qwen2.5-7B-Instruct-GGUF \
  --include "Qwen2.5-7B-Instruct-Q4_K_M.gguf" \
  --local-dir ~/models/
```

## Construir la URL de Descarga

### Estructura de la URL

```
https://huggingface.co/{usuario}/{repositorio}/resolve/main/{archivo}.gguf
```

### Ejemplo Paso a Paso

1. Ir a [huggingface.co/bartowski](https://huggingface.co/bartowski)
2. Buscar el modelo deseado (ej: `Qwen2.5-7B-Instruct-GGUF`)
3. Ir a la pestaña **Files and versions**
4. Encontrar el archivo `.gguf` con la cuantización deseada
5. Click derecho → Copiar enlace

## Verificar Descarga

### Verificar Tamaño

```bash
ls -lh ~/models/
```

**Tamaños esperados:**
- Qwen2.5-7B-Q4_K_M: ~4.7 GB
- Mistral-7B-Q4_K_S: ~4.0 GB
- Llama-3-8B-Q4_K_M: ~4.7 GB

### Verificar Integridad

```bash
# Calcular checksum
md5sum ~/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf
```

## Modelos para Casos de Uso Específicos

### Anonimización Clínica (Caso de la Tesis)

Para el caso de uso de anonimización de historiales clínicos:

| Modelo | MedQA | PubMedQA | Recomendación |
|--------|-------|----------|---------------|
| **Llama 3.1** | 61-78% | 79-86% | **Mejor para medicina** |
| Qwen 2.5 | ~60% | ~75% | Buena alternativa |
| Mistral | ~55% | ~70% | Ultra eficiente |

### Descargar Llama 3.1 8B

```bash
wget "https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf" \
  -O ~/models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
```

## Script de Descarga Automatizada

Usar el script proporcionado:

```bash
# Descargar Qwen 7B
./scripts/install-model.sh qwen-7b 8089

# Descargar Mistral 7B
./scripts/install-model.sh mistral-7b 8088

# Descargar Llama 3 8B
./scripts/install-model.sh llama3-8b 8090
```

## Siguiente Paso

Continúa con [04-llama-cpp-mma.md](04-llama-cpp-mma.md) para configurar llama.cpp con aceleradores MMA.
