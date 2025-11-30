# Ejecución de LLMs en IBM Power Virtual Server

[![IBM Power](https://img.shields.io/badge/IBM-POWER10-054ADA?style=for-the-badge&logo=ibm&logoColor=white)](https://www.ibm.com/power)
[![Docker](https://img.shields.io/badge/Docker-28.5.2-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Models-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-MMA-orange?style=for-the-badge)](https://github.com/ggerganov/llama.cpp)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

> **Proyecto Final de Grado** - Licenciatura en Ciencia de Datos para Negocios
> **Universidad de Montevideo** - Diciembre 2025
>
> *Optimización Estratégica y Aplicación de Inteligencia Artificial (Machine Learning e IA Generativa) en Infraestructuras de Alto Rendimiento IBM Power*

## Integrantes

| Nombre | Rol |
|--------|-----|
| Agustina Albez | Desarrollo |
| **Guillermo Robatto** | Desarrollo |
| Franco Subirán | Desarrollo |

**Tutor:** Sebastián Garcia Parra
**Cliente:** INCO Soluciones 

---

## Tabla de Contenidos

- [Descripción del Proyecto](#descripción-del-proyecto)
- [Hipótesis Central](#hipótesis-central)
- [Arquitectura](#arquitectura)
- [Quick Start](#quick-start)
- [Especificaciones del Servidor](#especificaciones-del-servidor)
- [Modelos Disponibles](#modelos-disponibles)
- [Documentación](#documentación)
- [Scripts](#scripts)
- [Ejemplos](#ejemplos)
- [Benchmarks](#benchmarks)
- [Referencias](#referencias)

---

## Descripción del Proyecto

Este repositorio contiene la implementación práctica de una **Prueba de Concepto (PoC)** para demostrar el valor de los aceleradores **Matrix Math Accelerator (MMA)** integrados en los procesadores IBM Power10/Power11 para la ejecución de modelos de lenguaje grandes (LLMs) en infraestructura on-premise.

### Caso de Uso Principal

**Anonimización automática de historiales clínicos** de la Facultad de Medicina de la Universidad de la República (UdelaR), eliminando información de salud protegida (PHI) mientras se preserva la utilidad clínica del contenido.

---

## Hipótesis Central

> *"Los núcleos de aceleración matricial (MMA) integrados en los servidores IBM Power están subutilizados por los clientes de INCO Soluciones. Su activación proporciona una ganancia de rendimiento cuantificable y significativa para inferencia de IA."*

### ¿Por qué IBM Power10 + MMA?

| Característica | Descripción | Ventaja para IA |
|----------------|-------------|-----------------|
| **MMA (4 unidades/core)** | Aceleración hardware para operaciones matriciales | 5x más rendimiento vs Power9 |
| **SMT-8** | 8 threads por core | Mejor utilización del CPU |
| **Arquitectura NUMA** | 2 nodos optimizados | Acceso eficiente a memoria |
| **Privacidad** | Datos permanecen on-premise | Sin egress fees |

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────────┐
│                        USUARIO FINAL                              │
│                    (API REST / curl / App)                        │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP Request
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     IBM Power Virtual Server                      │
│                      (CentOS Stream 9)                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    CONTENEDOR DOCKER                        │  │
│  │              quay.io/daniel_casali/llama.cpp-mma:v8        │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │               llama.cpp Server                        │  │  │
│  │  │         (Optimizado para POWER10 + MMA)               │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                          │                                  │  │
│  │                          ▼                                  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │            MODELO GGUF CUANTIZADO                     │  │  │
│  │  │     (Qwen2.5-7B / Mistral-7B / Llama-3-8B)           │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Volumen: ~/models → /models                                      │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Conectar al servidor PowerVS

```bash
ssh -i tu-clave-privada root@<IP_DEL_SERVIDOR>
```

### 2. Instalar un modelo (ejemplo: Qwen2.5-7B)

```bash
# Usar el script de instalación
./scripts/install-model.sh qwen-7b 8089
```

O manualmente:

```bash
# Descargar modelo de Hugging Face
mkdir -p ~/models
wget "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf" \
  -O ~/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf

# Ejecutar con Docker
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

### 3. Probar el modelo

```bash
curl -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explica qué es IBM POWER10:",
    "n_predict": 100,
    "temperature": 0.7
  }'
```

---

## Especificaciones del Servidor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ESPECIFICACIONES DEL SERVIDOR                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Hostname:        demo-inco-power-ai.cloud.ibm.com                           │
│ Sistema Op.:     CentOS Stream 9                                            │
│ Arquitectura:    ppc64le (PowerPC 64-bit Little Endian)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                              PROCESADOR                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Modelo:          IBM POWER10                                                 │
│ CPUs Virtuales:  96 vCPUs                                                    │
│ Sockets:         2                                                           │
│ Cores/Socket:    6 (12 cores físicos totales)                               │
│ Threads/Core:    8 (SMT-8)                                                   │
│ Nodos NUMA:      2                                                           │
│ Virtualización:  pHyp (PowerVM Hypervisor)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                               MEMORIA                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ RAM Total:       28 GB                                                       │
│ RAM Disponible:  ~24 GB                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                           ALMACENAMIENTO                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Disco Principal: 120 GB                                                      │
│ Espacio Libre:   ~85 GB                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                              SOFTWARE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Docker:          v28.5.2                                                     │
│ Kernel:          5.14.0-642.el9.ppc64le                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Modelos Disponibles

| Modelo | Tamaño | Puerto | RAM Requerida | Uso Recomendado |
|--------|--------|--------|---------------|-----------------|
| Mistral-7B | ~4 GB | 8088 | 16 GB | General, rápido |
| **Qwen2.5-7B** | ~4.7 GB | 8089 | 16 GB | Balance ideal |
| Llama-3-8B | ~4.7 GB | 8090 | 16 GB | Meta's latest |
| Qwen2.5-14B | ~8 GB | 8091 | 24 GB | Mayor capacidad |

### URLs de Descarga (Hugging Face)

```bash
# Mistral 7B
https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_S.gguf

# Qwen 2.5 7B
https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf

# Llama 3 8B
https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf
```

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [01-setup-powervs.md](docs/01-setup-powervs.md) | Configuración inicial de IBM Power Virtual Server |
| [02-docker-setup.md](docs/02-docker-setup.md) | Instalación y configuración de Docker |
| [03-huggingface-models.md](docs/03-huggingface-models.md) | Cómo descargar modelos de Hugging Face |
| [04-llama-cpp-mma.md](docs/04-llama-cpp-mma.md) | Configuración de llama.cpp con aceleradores MMA |
| [05-benchmarking.md](docs/05-benchmarking.md) | Guía de benchmarking y métricas |
| [06-benchmark-anonimizacion.md](docs/06-benchmark-anonimizacion.md) | **Benchmark de anonimización clínica** |

---

## Scripts

| Script | Descripción | Uso |
|--------|-------------|-----|
| [install-model.sh](scripts/install-model.sh) | Instala un modelo desde Hugging Face | `./install-model.sh qwen-7b 8089` |
| [start-server.sh](scripts/start-server.sh) | Inicia el servidor de inferencia | `./start-server.sh qwen-7b` |
| [benchmark.sh](scripts/benchmark.sh) | Ejecuta benchmarks de rendimiento | `./benchmark.sh 8089` |

---

## Ejemplos

- [curl-examples.md](examples/curl-examples.md) - Ejemplos de uso con curl
- [python-client.py](examples/python-client.py) - Cliente Python de ejemplo

---

## Benchmarks

### Rendimiento de Qwen2.5-7B en Power10

| Métrica | Valor |
|---------|-------|
| Prompt (tokens/seg) | ~26 |
| Generación (tokens/seg) | ~16.6 |
| Latencia primer token | ~500ms |
| Contexto máximo | 4096 tokens |

### Benchmark de Anonimización Clínica

Script especializado para evaluar la capacidad de anonimización de historiales clínicos.

```bash
# Ejecutar benchmark de anonimización
cd benchmarks
python benchmark_anon.py --port 8089

# Ejecutar en todos los modelos
./run_all_models.sh
```

| Modelo | TPS Esperado | Calidad Anonimización |
|--------|--------------|----------------------|
| Qwen2.5-7B | ~15-20 | Muy buena |
| Mistral-7B | ~18-22 | Buena |
| Llama-3.1-8B | ~14-18 | Excelente (medicina) |

Ver documentación completa: [06-benchmark-anonimizacion.md](docs/06-benchmark-anonimizacion.md)

---

## Comparativa: Power10 vs GPU vs TPU

| Aspecto | Power10 + MMA | GPU (NVIDIA) | TPU (Google) |
|---------|---------------|--------------|--------------|
| **Caso de uso óptimo** | Inferencia on-premise | Entrenamiento LLMs | Inferencia cloud |
| **Privacidad de datos** | Total (datos locales) | Requiere mover datos | Solo en Google Cloud |
| **Costo de egreso** | $0 | Variable | Variable |
| **Latencia** | Muy baja | Media | Baja |
| **Ecosistema** | Enterprise | Muy maduro (CUDA) | Propietario |

> **Nota**: Según IBM, el 92% de los proyectos de IA empresarial se ejecutan on-premise o en nubes privadas (IBM Institute of Business Value, 2024).

---

## Stack Tecnológico

```
┌─────────────────────────────────────────────────────┐
│                    Open WebUI                        │
│              (Interfaz de Usuario)                   │
├─────────────────────────────────────────────────────┤
│              llama.cpp Server                        │
│         (Motor de Inferencia + MMA)                  │
├─────────────────────────────────────────────────────┤
│          Modelo GGUF Cuantizado                      │
│     (Qwen2.5-7B / Llama 3.1 / Mistral)              │
├─────────────────────────────────────────────────────┤
│              IBM Power10/11                          │
│      (Aceleradores MMA - 4 unidades/core)           │
└─────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Docker no inicia

```bash
# Ver logs de Docker
journalctl -u docker.service -n 50

# Solucionar conflicto de firewall
firewall-cmd --permanent --zone=trusted --remove-interface=docker0
firewall-cmd --reload
ip link delete docker0
systemctl restart docker
```

### Modelo no responde

```bash
# Verificar logs del contenedor
docker logs <nombre-contenedor> --tail 100

# Verificar puerto
ss -tlnp | grep <puerto>
```

### Memoria insuficiente

```bash
# Verificar uso de memoria
free -h

# Usar modelo más pequeño (Q4_K_S en lugar de Q4_K_M)
```

---

## Referencias

### Documentación Técnica

- Simon, T., et al. (2024). *IBM Power E1080 Technical Overview*. IBM Redbooks.
- IBM Developer. (2021). *IBM Power10 Business Inferencing at Scale with MMA*.
- Vaswani, A., et al. (2017). *Attention Is All You Need*. NeurIPS.

### Modelos

- [bartowski/Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF)
- [bartowski/Mistral-7B-Instruct-v0.3-GGUF](https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF)

### Herramientas

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Motor de inferencia
- [GGUF Format](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md) - Especificación del formato

---

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

---

## Contacto

**Proyecto Final de Grado** - Universidad de Montevideo
**Cliente:** INCO Soluciones
**Fecha:** Diciembre 2025
