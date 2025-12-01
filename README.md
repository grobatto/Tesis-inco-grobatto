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

### Caso de Uso Principal: Des-identificación de Datos Clínicos

La **Facultad de Medicina de la Universidad de la República (UdelaR)** genera y almacena volúmenes significativos de documentación clínica. Estos registros contienen **información de salud protegida (Protected Health Information, PHI)** que incluye identificadores directos e indirectos de los pacientes. La utilización secundaria de estos datos para investigación, docencia o desarrollo de sistemas de inteligencia artificial requiere un proceso previo de des-identificación que elimine o enmascare la información sensible sin comprometer la utilidad clínica del contenido.

#### Contexto Internacional

El desafío de des-identificación de texto clínico ha sido abordado sistemáticamente por la comunidad científica internacional. El proyecto **i2b2** (Informatics for Integrating Biology and the Bedside) del Centro Nacional de Informática Biomédica de Estados Unidos estableció en 2014 un desafío compartido que se ha convertido en el estándar de referencia para evaluar sistemas de anonimización. Según Stubbs et al. (2015), este desafío proporcionó un corpus de **1,304 notas clínicas longitudinales** de 296 pacientes diabéticos, conteniendo más de **28,000 instancias de PHI** distribuidas en 25 subcategorías agrupadas en siete categorías principales: nombres, profesiones, ubicaciones, edades, fechas, contactos e identificadores.

#### Objetivo

Implementar un sistema de **anonimización automática de historiales clínicos en español** que permita procesar documentación médica de la Facultad de Medicina de UdelaR, eliminando o enmascarando información de salud protegida mientras se preserva la utilidad clínica del contenido para fines de investigación y docencia.

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

![Arquitectura del Sistema](images/arquitectura.jpeg)

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

![Especificaciones del Servidor](images/especificaciones-servidor.jpeg)

---

## Modelos Disponibles

### Modelos Grandes (Recomendados para Producción)

| Modelo | Tamaño | Puerto | Fabricante | TPS | Calidad |
|--------|--------|--------|------------|-----|---------|
| **Mistral-Nemo-12B** | 7.1 GB | 8097 | Mistral AI | 9.2 | ★★★★★ **MEJOR** |
| **Qwen2.5-14B** | 8.6 GB | 8096 | Alibaba | 6.5 | ★★★★☆ |

### Modelos Medianos (Balance Velocidad/Calidad)

| Modelo | Tamaño | Puerto | Fabricante | TPS | Calidad |
|--------|--------|--------|------------|-----|---------|
| **Phi-3.5-mini** | 2.3 GB | 8093 | Microsoft | 16.8 | ★★★★★ |
| **BioMistral-7B** | 4.1 GB | 8092 | CNRS | 13.1 | ★★★★☆ |
| **Gemma-2-9B** | 5.4 GB | 8094 | Google | 9.6 | ★★★☆☆ |

### Por qué estos modelos

| Modelo | Justificación | Referencia |
|--------|---------------|------------|
| **Mistral-Nemo-12B** | Mejor multilingüe de Mistral, colaboración con NVIDIA, Apache 2.0 | [Mistral AI](https://mistral.ai/news/mistral-nemo) |
| **Qwen2.5-14B** | Mejoras en seguimiento de instrucciones y JSON, 29+ idiomas | [Qwen](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct) |
| **Phi-3.5-mini** | Supera modelos 2x más grandes, contexto 128K | [Microsoft](https://huggingface.co/microsoft/Phi-3.5-mini-instruct) |
| **BioMistral-7B** | Pre-entrenado en PubMed, +18% vs Meditron, evaluado en español | [Paper](https://arxiv.org/abs/2402.10373) |

### URLs de Descarga (Hugging Face - GGUF Q4_K_M)

```bash
# Mistral-Nemo-12B (Mistral AI) - MEJOR CALIDAD
https://huggingface.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF/resolve/main/Mistral-Nemo-Instruct-2407-Q4_K_M.gguf

# Qwen2.5-14B (Alibaba)
https://huggingface.co/bartowski/Qwen2.5-14B-Instruct-GGUF/resolve/main/Qwen2.5-14B-Instruct-Q4_K_M.gguf

# Phi-3.5 mini (Microsoft) - MEJOR VELOCIDAD
https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf

# BioMistral-7B (Médico)
https://huggingface.co/BioMistral/BioMistral-7B-GGUF/resolve/main/ggml-model-Q4_K_M.gguf

# Gemma 2 9B (Google)
https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf
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

### Resultados de Anonimización Clínica (30 Nov 2025)

Evaluación de 7 modelos para anonimización de historiales clínicos en español.

#### Modelos Grandes (12B-14B)

| Modelo | TPS | Calidad | Resultado |
|--------|-----|---------|-----------|
| **Mistral-Nemo-12B** | 9.2 | ★★★★★ | **MEJOR** - Anonimizó TODO incluyendo doctores y enfermeros |
| **Qwen2.5-14B** | 6.5 | ★★★★☆ | Anonimizó encabezado, dejó nombres de médicos |

#### Modelos Medianos (3B-9B)

| Modelo | TPS | Calidad | Resultado |
|--------|-----|---------|-----------|
| **Phi-3.5-mini** | 16.8 | ★★★★★ | Excelente - Anonimizó todo correctamente |
| **BioMistral-7B** | 13.1 | ★★★★☆ | Buena - Anonimizó encabezado |
| **Gemma-2-9B** | 9.6 | ★★★☆☆ | Parcial - Dejó nombres de médicos |

### Recomendaciones

| Caso de Uso | Modelo Recomendado | Por qué |
|-------------|-------------------|---------|
| **Máxima calidad** | Mistral-Nemo-12B | Detecta TODOS los PHI incluyendo personal médico |
| **Balance velocidad/calidad** | Phi-3.5-mini | 16.8 TPS con excelente calidad, solo 2.3 GB |
| **Dominio médico** | BioMistral-7B | Especializado en PubMed, evaluado en español |

### Ejemplo: Mistral-Nemo-12B (Mejor resultado)

```
Entrada: Dr. Sanguinetti, Dras. Cristancho, Ramirez. AE. M. Brown, LE. J. Bremmerman
Salida:  Dr. [NOMBRE], Dras. [NOMBRE], [NOMBRE]. AE. [NOMBRE], LE. [NOMBRE]
```

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

![Stack Tecnológico](images/stack-tecnologico.jpeg)

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

- [bartowski/Phi-3.5-mini-instruct-GGUF](https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF) - Microsoft
- [BioMistral/BioMistral-7B-GGUF](https://huggingface.co/BioMistral/BioMistral-7B-GGUF) - CNRS
- [bartowski/gemma-2-9b-it-GGUF](https://huggingface.co/bartowski/gemma-2-9b-it-GGUF) - Google
- [bartowski/Meta-Llama-3.1-8B-Instruct-GGUF](https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF) - Meta
- [bartowski/Llama-3.2-3B-Instruct-GGUF](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF) - Meta

### Investigación

- [The LLM-Anonymizer - NEJM AI](https://ai.nejm.org/doi/full/10.1056/AIdbp2400537) - Benchmark de anonimización médica
- [BioMistral Paper](https://arxiv.org/abs/2402.10373) - Modelo médico multilingüe

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
