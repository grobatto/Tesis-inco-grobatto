# 04 - Configuración de llama.cpp con Aceleradores MMA

## Introducción

Esta guía explica cómo configurar y ejecutar modelos de lenguaje usando `llama.cpp` optimizado para los aceleradores **Matrix Math Accelerator (MMA)** de IBM Power10/Power11.

## ¿Qué es MMA?

### Matrix Math Accelerator

MMA es una unidad de aceleración de hardware integrada en los procesadores IBM Power10/11 diseñada específicamente para operaciones matriciales.

| Característica | Descripción |
|----------------|-------------|
| **Unidades por core** | 4 unidades MMA |
| **Operaciones** | Multiplicación de matrices, operaciones GEMM |
| **Precisión** | FP32, FP16, BF16, INT8 |
| **Ganancia** | ~5x vs Power9 sin MMA |

### Beneficios para LLMs

1. **Multiplicación de matrices acelerada**: Las operaciones de atención y FFN se ejecutan más rápido
2. **Eficiencia energética**: Menor consumo por operación
3. **Sin GPU externa**: No requiere hardware adicional

## Imagen Docker Optimizada

### Imagen Recomendada

```bash
quay.io/daniel_casali/llama.cpp-mma:v8
```

Esta imagen está compilada específicamente para arquitectura `ppc64le` con soporte para MMA habilitado.

### Verificar la Imagen

```bash
# Descargar imagen
docker pull quay.io/daniel_casali/llama.cpp-mma:v8

# Verificar arquitectura
docker inspect quay.io/daniel_casali/llama.cpp-mma:v8 | grep Architecture
```

**Salida esperada:**
```
"Architecture": "ppc64le"
```

## Ejecutar el Servidor de Inferencia

### Comando Básico

```bash
docker run -d \
  --name <nombre-contenedor> \
  -p <puerto-host>:8080 \
  -v ~/models:/models \
  --restart always \
  quay.io/daniel_casali/llama.cpp-mma:v8 \
  --host 0.0.0.0 \
  --port 8080 \
  -m /models/<archivo-modelo>.gguf \
  -c 4096 -b 256 -t 12 -n -1
```

### Parámetros Explicados

| Parámetro | Descripción | Valor Recomendado |
|-----------|-------------|-------------------|
| `-c` | Tamaño del contexto (tokens) | 4096 |
| `-b` | Tamaño del batch | 256 |
| `-t` | Número de threads | 12 (ajustar según vCPUs) |
| `-n` | Máximo de tokens a generar | -1 (sin límite) |
| `--host` | IP de escucha | 0.0.0.0 |
| `--port` | Puerto interno | 8080 |

### Ejemplo Completo: Qwen2.5-7B

```bash
docker run -d \
  --name qwen-7b \
  -p 8089:8080 \
  -v ~/models:/models \
  --restart always \
  quay.io/daniel_casali/llama.cpp-mma:v8 \
  --host 0.0.0.0 \
  --port 8080 \
  -m /models/Qwen2.5-7B-Instruct-Q4_K_M.gguf \
  -c 4096 -b 256 -t 12 -n -1
```

## Verificar que MMA está Activo

### Durante la Carga del Modelo

```bash
docker logs qwen-7b 2>&1 | head -50
```

Buscar líneas que indiquen el uso de optimizaciones de Power:

```
llm_load_tensors: ggml ctx size = ...
llm_load_tensors: offloading 0 repeating layers to GPU
llm_load_tensors: offloaded 0/... layers to GPU
llm_load_tensors: CPU buffer size = 4655.05 MiB
```

### Monitorear Rendimiento

```bash
# Ver uso de CPU durante inferencia
htop

# Ver logs en tiempo real
docker logs -f qwen-7b
```

## Endpoints de la API

### Endpoint /completion

```bash
curl -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explica qué es IBM POWER10:",
    "n_predict": 100,
    "temperature": 0.7
  }'
```

### Endpoint /v1/chat/completions (OpenAI Compatible)

```bash
curl -X POST http://localhost:8089/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {"role": "user", "content": "¿Qué es MMA en IBM Power10?"}
    ],
    "temperature": 0.7
  }'
```

### Endpoint /health

```bash
curl http://localhost:8089/health
```

## Optimización de Threads

### Cálculo Recomendado

Para 28GB RAM con modelos 7B:

```
Threads óptimos = Cores físicos * 0.75
```

Para nuestro servidor (12 cores físicos):
- **Threads recomendados:** 12

### Tabla de Configuración

| RAM | Modelo | Threads | Contexto |
|-----|--------|---------|----------|
| 16 GB | 7B | 8 | 2048 |
| 28 GB | 7B | 12 | 4096 |
| 28 GB | 14B | 8 | 2048 |
| 64 GB | 14B | 16 | 8192 |

## Múltiples Modelos

### Ejecutar Varios Modelos Simultáneamente

```bash
# Modelo 1: Mistral en puerto 8088
docker run -d --name mistral-7b -p 8088:8080 \
  -v ~/models:/models --restart always \
  quay.io/daniel_casali/llama.cpp-mma:v8 \
  --host 0.0.0.0 --port 8080 \
  -m /models/Mistral-7B-Instruct-v0.3-Q4_K_S.gguf \
  -c 4096 -b 256 -t 8 -n -1

# Modelo 2: Qwen en puerto 8089
docker run -d --name qwen-7b -p 8089:8080 \
  -v ~/models:/models --restart always \
  quay.io/daniel_casali/llama.cpp-mma:v8 \
  --host 0.0.0.0 --port 8080 \
  -m /models/Qwen2.5-7B-Instruct-Q4_K_M.gguf \
  -c 4096 -b 256 -t 8 -n -1
```

> **Nota:** Al ejecutar múltiples modelos, reduce los threads por modelo para evitar contención.

## Gestión de Contenedores

### Comandos Útiles

```bash
# Listar contenedores
docker ps -a

# Ver logs
docker logs <nombre> --tail 100

# Detener contenedor
docker stop <nombre>

# Reiniciar contenedor
docker restart <nombre>

# Eliminar contenedor
docker rm -f <nombre>
```

## Troubleshooting

### Error: Model file not found

```bash
# Verificar que el modelo existe
ls -la ~/models/

# Verificar permisos
chmod 644 ~/models/*.gguf
```

### Error: Out of memory

```bash
# Usar modelo con menor cuantización
# Cambiar de Q4_K_M a Q4_K_S o Q3_K_M

# Reducir contexto
-c 2048  # en lugar de 4096
```

### Error: Port already in use

```bash
# Verificar puertos en uso
ss -tlnp | grep 8089

# Detener contenedor existente
docker stop qwen-7b && docker rm qwen-7b
```

## Siguiente Paso

Continúa con [05-benchmarking.md](05-benchmarking.md) para aprender a medir el rendimiento de los modelos.
