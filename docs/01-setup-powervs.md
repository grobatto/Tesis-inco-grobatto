# 01 - Configuración Inicial de IBM Power Virtual Server

## Introducción

IBM Power Virtual Server (PowerVS) es una oferta de Infrastructure as a Service (IaaS) que permite ejecutar cargas de trabajo en procesadores IBM POWER en la nube de IBM.

## Pre-requisitos

1. Cuenta en IBM Cloud
2. Acceso a IBM Power Virtual Server
3. Par de claves SSH generado

## Paso 1: Crear una Instancia PowerVS

### 1.1 Acceder a IBM Cloud

1. Ir a [IBM Cloud](https://cloud.ibm.com)
2. Iniciar sesión con tu cuenta
3. Navegar a **Catalog** > **Power Virtual Server**

### 1.2 Configurar la Instancia

| Parámetro | Valor Recomendado |
|-----------|-------------------|
| **Nombre** | demo-power-ai |
| **Región** | Dallas (DAL) o la más cercana |
| **Tipo de Máquina** | s922 (POWER10) |
| **Procesadores** | 2-4 cores |
| **Memoria** | 28-32 GB |
| **Almacenamiento** | 120 GB SSD |
| **Sistema Operativo** | CentOS Stream 9 |

### 1.3 Configurar Red

1. Crear una subred pública
2. Asignar IP pública a la instancia
3. Configurar reglas de firewall para puertos 8080-8099

## Paso 2: Configurar Acceso SSH

### 2.1 Generar Par de Claves (si no tienes)

```bash
# En tu máquina local
ssh-keygen -t rsa -b 4096 -f ~/.ssh/powervs-key
```

### 2.2 Subir Clave Pública

1. En la consola de IBM Cloud, ir a **SSH Keys**
2. Agregar la clave pública (`~/.ssh/powervs-key.pub`)
3. Asociarla a la instancia

### 2.3 Conectar por Primera Vez

```bash
# Conectar a la instancia
ssh -i ~/.ssh/powervs-key root@<IP_PUBLICA>
```

## Paso 3: Verificar el Sistema

### 3.1 Verificar Arquitectura

```bash
# Verificar que sea POWER10
lscpu | grep -E "Architecture|Model name"
```

**Salida esperada:**
```
Architecture:          ppc64le
Model name:            POWER10 (architected), altivec supported
```

### 3.2 Verificar Recursos

```bash
# Memoria
free -h

# Disco
df -h

# CPUs
nproc
```

### 3.3 Verificar Conectividad

```bash
# Verificar conectividad a internet
ping -c 3 google.com

# Verificar DNS
nslookup huggingface.co
```

## Paso 4: Actualizar el Sistema

```bash
# Actualizar paquetes
dnf update -y

# Instalar herramientas útiles
dnf install -y wget curl vim htop
```

## Paso 5: Configurar Firewall

```bash
# Habilitar puertos para los modelos
firewall-cmd --permanent --add-port=8080-8099/tcp
firewall-cmd --reload

# Verificar
firewall-cmd --list-ports
```

## Verificación Final

```bash
# Verificar todo
echo "=== SISTEMA ==="
uname -a
echo ""
echo "=== CPU ==="
lscpu | head -20
echo ""
echo "=== MEMORIA ==="
free -h
echo ""
echo "=== DISCO ==="
df -h /
```

## Siguiente Paso

Una vez completada la configuración inicial, continúa con [02-docker-setup.md](02-docker-setup.md) para instalar Docker.
