# 02 - Instalación y Configuración de Docker

## Pre-requisitos

- Servidor PowerVS configurado ([01-setup-powervs.md](01-setup-powervs.md))
- Acceso root al servidor

## Paso 1: Instalar Docker

### 1.1 Agregar Repositorio de Docker

```bash
# Instalar dependencias
dnf install -y dnf-plugins-core

# Agregar repositorio Docker CE
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
```

### 1.2 Instalar Docker Engine

```bash
# Instalar Docker
dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verificar versión
docker --version
```

## Paso 2: Configurar Docker

### 2.1 Iniciar y Habilitar Docker

```bash
# Iniciar Docker
systemctl start docker

# Habilitar inicio automático
systemctl enable docker

# Verificar estado
systemctl status docker
```

### 2.2 Configurar Docker para ppc64le

Docker funciona de forma nativa en arquitectura `ppc64le`. No se requiere configuración adicional, pero puedes verificar:

```bash
docker info | grep -E "Architecture|Server Version"
```

**Salida esperada:**
```
 Server Version: 28.5.2
 Architecture: ppc64le
```

## Paso 3: Solución de Problemas Comunes

### 3.1 Error: ZONE_CONFLICT con docker0

Si Docker no inicia debido a un conflicto de firewall:

```bash
# Remover docker0 de la zona trusted
firewall-cmd --permanent --zone=trusted --remove-interface=docker0

# Agregar docker0 a la zona docker
firewall-cmd --permanent --zone=docker --add-interface=docker0

# Recargar firewall
firewall-cmd --reload

# Eliminar interfaz conflictiva
ip link delete docker0 2>/dev/null

# Reiniciar Docker
systemctl restart docker
```

### 3.2 Error: Cannot connect to Docker daemon

```bash
# Reset del servicio
systemctl reset-failed docker.service

# Reiniciar
systemctl start docker

# Verificar logs
journalctl -u docker.service -n 50
```

## Paso 4: Verificar Instalación

### 4.1 Ejecutar Hello World

```bash
docker run hello-world
```

### 4.2 Verificar Imágenes para ppc64le

```bash
# Verificar que la imagen llama.cpp-mma está disponible
docker pull quay.io/daniel_casali/llama.cpp-mma:v8

# Verificar arquitectura de la imagen
docker inspect quay.io/daniel_casali/llama.cpp-mma:v8 | grep Architecture
```

## Paso 5: Preparar Directorio de Modelos

```bash
# Crear directorio para modelos
mkdir -p ~/models

# Verificar permisos
ls -la ~/models
```

## Paso 6: Configuración de Red

### 6.1 Exponer Puertos

Los modelos se expondrán en los siguientes puertos:

| Modelo | Puerto |
|--------|--------|
| Mistral-7B | 8088 |
| Qwen2.5-7B | 8089 |
| Llama-3-8B | 8090 |

```bash
# Verificar que los puertos están disponibles
ss -tlnp | grep -E "8088|8089|8090"
```

## Verificación Final

```bash
# Verificar Docker
docker info

# Listar contenedores
docker ps -a

# Verificar directorio de modelos
ls -la ~/models
```

## Siguiente Paso

Continúa con [03-huggingface-models.md](03-huggingface-models.md) para aprender a descargar modelos de Hugging Face.
