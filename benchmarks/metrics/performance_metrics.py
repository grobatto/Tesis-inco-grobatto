#!/usr/bin/env python3
"""
performance_metrics.py - Métricas de rendimiento para validación de MMA
Universidad de Montevideo - Tesis 2025

Objetivo principal de la tesis:
Demostrar que los aceleradores MMA de IBM Power10 proporcionan ganancia
de rendimiento cuantificable para inferencia de IA Generativa on-premise.

Métricas implementadas:
- TPS (Tokens Per Second) - generación y evaluación
- Latencia (time to first token, total)
- Throughput (queries per second)
- Utilización de recursos (CPU, RAM)
- Estabilidad (desviación estándar, tasa de errores)
"""

import time
import statistics
import subprocess
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# =============================================================================
# DATACLASSES PARA MÉTRICAS
# =============================================================================

@dataclass
class InferenceMetrics:
    """Métricas de una única inferencia."""
    # Identificación
    timestamp: str = ""
    model: str = ""
    prompt_strategy: str = ""
    case_id: str = ""

    # Velocidad de inferencia
    tps_generation: float = 0.0        # Tokens/segundo en generación
    tps_prompt_eval: float = 0.0       # Tokens/segundo en evaluación de prompt

    # Tokens
    tokens_prompt: int = 0             # Tokens en el prompt
    tokens_generated: int = 0          # Tokens generados

    # Latencia
    latency_prompt_ms: float = 0.0     # Tiempo evaluación prompt (ms)
    latency_generation_ms: float = 0.0 # Tiempo generación (ms)
    latency_total_ms: float = 0.0      # Tiempo total (ms)
    time_to_first_token_ms: float = 0.0  # Tiempo hasta primer token

    # Estado
    success: bool = True
    error_message: str = ""


@dataclass
class BenchmarkResult:
    """Resultado agregado de múltiples iteraciones."""
    # Identificación
    model: str = ""
    prompt_strategy: str = ""
    case_id: str = ""
    iterations: int = 0
    timestamp: str = ""

    # Hardware
    platform: str = "IBM Power10"
    mma_enabled: bool = True
    cores: int = 0
    ram_gb: float = 0.0

    # Estadísticas TPS
    tps_avg: float = 0.0
    tps_std: float = 0.0
    tps_min: float = 0.0
    tps_max: float = 0.0
    tps_median: float = 0.0

    # Estadísticas latencia
    latency_avg_ms: float = 0.0
    latency_std_ms: float = 0.0
    latency_min_ms: float = 0.0
    latency_max_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0

    # Tokens
    tokens_avg: float = 0.0
    tokens_total: int = 0

    # Estabilidad
    success_rate: float = 100.0
    error_count: int = 0

    # Datos crudos
    raw_metrics: List[InferenceMetrics] = field(default_factory=list)


@dataclass
class SystemResources:
    """Métricas de utilización de recursos del sistema."""
    timestamp: str = ""
    cpu_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_total_gb: float = 0.0
    memory_percent: float = 0.0
    load_avg_1min: float = 0.0
    load_avg_5min: float = 0.0
    load_avg_15min: float = 0.0


# =============================================================================
# FUNCIONES DE CÁLCULO DE MÉTRICAS
# =============================================================================

def parse_llama_cpp_timings(timings: dict) -> InferenceMetrics:
    """
    Parsea el objeto 'timings' de llama.cpp y extrae métricas.

    Ejemplo de timings de llama.cpp:
    {
        "prompt_n": 350,
        "prompt_ms": 1250.5,
        "prompt_per_token_ms": 3.57,
        "prompt_per_second": 280.0,
        "predicted_n": 450,
        "predicted_ms": 35000.0,
        "predicted_per_token_ms": 77.78,
        "predicted_per_second": 12.86
    }
    """
    metrics = InferenceMetrics()
    metrics.timestamp = datetime.now().isoformat()

    if not timings:
        return metrics

    # Tokens
    metrics.tokens_prompt = timings.get("prompt_n", 0)
    metrics.tokens_generated = timings.get("predicted_n", 0)

    # Latencia
    metrics.latency_prompt_ms = timings.get("prompt_ms", 0.0)
    metrics.latency_generation_ms = timings.get("predicted_ms", 0.0)
    metrics.latency_total_ms = metrics.latency_prompt_ms + metrics.latency_generation_ms

    # TPS
    metrics.tps_prompt_eval = timings.get("prompt_per_second", 0.0)
    metrics.tps_generation = timings.get("predicted_per_second", 0.0)

    # Time to first token (aproximación)
    if metrics.tokens_prompt > 0:
        metrics.time_to_first_token_ms = metrics.latency_prompt_ms

    return metrics


def calculate_benchmark_stats(metrics_list: List[InferenceMetrics]) -> BenchmarkResult:
    """
    Calcula estadísticas agregadas de una lista de métricas.

    Args:
        metrics_list: Lista de métricas individuales

    Returns:
        BenchmarkResult con estadísticas calculadas
    """
    result = BenchmarkResult()
    result.timestamp = datetime.now().isoformat()
    result.iterations = len(metrics_list)
    result.raw_metrics = metrics_list

    if not metrics_list:
        return result

    # Filtrar métricas exitosas
    successful = [m for m in metrics_list if m.success]
    failed = [m for m in metrics_list if not m.success]

    result.error_count = len(failed)
    result.success_rate = (len(successful) / len(metrics_list)) * 100

    if not successful:
        return result

    # Extraer valores para estadísticas
    tps_values = [m.tps_generation for m in successful if m.tps_generation > 0]
    latency_values = [m.latency_total_ms for m in successful if m.latency_total_ms > 0]
    token_values = [m.tokens_generated for m in successful]

    # Estadísticas TPS
    if tps_values:
        result.tps_avg = statistics.mean(tps_values)
        result.tps_std = statistics.stdev(tps_values) if len(tps_values) > 1 else 0.0
        result.tps_min = min(tps_values)
        result.tps_max = max(tps_values)
        result.tps_median = statistics.median(tps_values)

    # Estadísticas latencia
    if latency_values:
        result.latency_avg_ms = statistics.mean(latency_values)
        result.latency_std_ms = statistics.stdev(latency_values) if len(latency_values) > 1 else 0.0
        result.latency_min_ms = min(latency_values)
        result.latency_max_ms = max(latency_values)

        # Percentiles
        sorted_latencies = sorted(latency_values)
        n = len(sorted_latencies)
        result.latency_p95_ms = sorted_latencies[int(n * 0.95)] if n >= 20 else result.latency_max_ms
        result.latency_p99_ms = sorted_latencies[int(n * 0.99)] if n >= 100 else result.latency_max_ms

    # Tokens
    if token_values:
        result.tokens_avg = statistics.mean(token_values)
        result.tokens_total = sum(token_values)

    # Copiar identificadores del primer resultado
    if successful:
        result.model = successful[0].model
        result.prompt_strategy = successful[0].prompt_strategy
        result.case_id = successful[0].case_id

    return result


def calculate_speedup(tps_mma: float, tps_baseline: float) -> float:
    """
    Calcula el speedup de MMA vs baseline.

    Speedup = TPS_MMA / TPS_Baseline

    Args:
        tps_mma: TPS con MMA habilitado
        tps_baseline: TPS sin MMA (o baseline)

    Returns:
        Factor de speedup (>1.0 significa mejora)
    """
    if tps_baseline <= 0:
        return 0.0
    return tps_mma / tps_baseline


def calculate_throughput_qps(total_queries: int, total_time_seconds: float) -> float:
    """
    Calcula queries per second (QPS).

    Args:
        total_queries: Número total de consultas
        total_time_seconds: Tiempo total en segundos

    Returns:
        QPS (queries per second)
    """
    if total_time_seconds <= 0:
        return 0.0
    return total_queries / total_time_seconds


# =============================================================================
# FUNCIONES DE RECURSOS DEL SISTEMA
# =============================================================================

def get_system_resources() -> SystemResources:
    """
    Obtiene métricas de recursos del sistema.

    Funciona en Linux/Power, usa comandos del sistema.
    """
    resources = SystemResources()
    resources.timestamp = datetime.now().isoformat()

    try:
        # CPU y Load average
        with open('/proc/loadavg', 'r') as f:
            load_parts = f.read().split()
            resources.load_avg_1min = float(load_parts[0])
            resources.load_avg_5min = float(load_parts[1])
            resources.load_avg_15min = float(load_parts[2])

        # Memoria
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split()[0]
                    meminfo[key] = int(value)

            total_kb = meminfo.get('MemTotal', 0)
            available_kb = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))

            resources.memory_total_gb = total_kb / (1024 * 1024)
            resources.memory_used_gb = (total_kb - available_kb) / (1024 * 1024)
            resources.memory_percent = (resources.memory_used_gb / resources.memory_total_gb) * 100 if resources.memory_total_gb > 0 else 0

    except Exception as e:
        # Fallback para sistemas no-Linux
        resources.memory_total_gb = 28.0  # Default para Power10 de prueba
        resources.memory_used_gb = 0.0
        resources.cpu_percent = 0.0

    return resources


def check_mma_enabled() -> Tuple[bool, str]:
    """
    Verifica si MMA está habilitado en el sistema Power.

    Returns:
        Tuple de (bool: MMA habilitado, str: mensaje de información)
    """
    try:
        # Intentar verificar via lscpu
        result = subprocess.run(
            ['lscpu'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if 'mma' in result.stdout.lower() or 'matrix' in result.stdout.lower():
            return True, "MMA detectado via lscpu"

        # Intentar via ppc64_cpu
        result = subprocess.run(
            ['ppc64_cpu', '--info'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if 'mma' in result.stdout.lower():
            return True, "MMA detectado via ppc64_cpu"

        return False, "MMA no detectado (puede no estar disponible o no ser Power10+)"

    except Exception as e:
        return False, f"No se pudo verificar MMA: {str(e)}"


def get_cpu_info() -> dict:
    """Obtiene información del CPU."""
    info = {
        "architecture": "unknown",
        "model": "unknown",
        "cores": 0,
        "threads": 0
    }

    try:
        result = subprocess.run(['lscpu'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if 'architecture' in key:
                    info['architecture'] = value
                elif 'model name' in key or 'model' in key:
                    info['model'] = value
                elif 'cpu(s)' in key and 'on-line' not in key and 'numa' not in key:
                    try:
                        info['threads'] = int(value)
                    except:
                        pass
                elif 'core(s) per socket' in key:
                    try:
                        info['cores'] = int(value)
                    except:
                        pass

    except Exception:
        pass

    return info


# =============================================================================
# FORMATEO Y REPORTING
# =============================================================================

def format_benchmark_report(result: BenchmarkResult) -> str:
    """Formatea un reporte de benchmark para consola."""
    lines = [
        "",
        "=" * 70,
        "  RESULTADOS DE BENCHMARK - RENDIMIENTO MMA",
        "=" * 70,
        f"  Modelo:          {result.model}",
        f"  Prompt:          {result.prompt_strategy}",
        f"  Caso:            {result.case_id}",
        f"  Iteraciones:     {result.iterations}",
        f"  Plataforma:      {result.platform}",
        f"  MMA Habilitado:  {'Sí' if result.mma_enabled else 'No'}",
        "=" * 70,
        "",
        "  MÉTRICAS DE VELOCIDAD (TPS)",
        "  " + "-" * 40,
        f"  Promedio:        {result.tps_avg:.2f} tokens/seg",
        f"  Mediana:         {result.tps_median:.2f} tokens/seg",
        f"  Desv. Estándar:  {result.tps_std:.2f}",
        f"  Mínimo:          {result.tps_min:.2f} tokens/seg",
        f"  Máximo:          {result.tps_max:.2f} tokens/seg",
        "",
        "  MÉTRICAS DE LATENCIA",
        "  " + "-" * 40,
        f"  Promedio:        {result.latency_avg_ms:.0f} ms",
        f"  Desv. Estándar:  {result.latency_std_ms:.0f} ms",
        f"  Mínimo:          {result.latency_min_ms:.0f} ms",
        f"  Máximo:          {result.latency_max_ms:.0f} ms",
        f"  P95:             {result.latency_p95_ms:.0f} ms",
        f"  P99:             {result.latency_p99_ms:.0f} ms",
        "",
        "  TOKENS Y ESTABILIDAD",
        "  " + "-" * 40,
        f"  Tokens promedio: {result.tokens_avg:.0f}",
        f"  Tokens total:    {result.tokens_total}",
        f"  Tasa de éxito:   {result.success_rate:.1f}%",
        f"  Errores:         {result.error_count}",
        "",
        "=" * 70,
    ]

    return "\n".join(lines)


def to_json(result: BenchmarkResult) -> dict:
    """Convierte BenchmarkResult a diccionario para JSON."""
    return {
        "metadata": {
            "model": result.model,
            "prompt_strategy": result.prompt_strategy,
            "case_id": result.case_id,
            "iterations": result.iterations,
            "timestamp": result.timestamp,
            "platform": result.platform,
            "mma_enabled": result.mma_enabled,
            "cores": result.cores,
            "ram_gb": result.ram_gb,
        },
        "performance": {
            "tps": {
                "avg": round(result.tps_avg, 2),
                "std": round(result.tps_std, 2),
                "min": round(result.tps_min, 2),
                "max": round(result.tps_max, 2),
                "median": round(result.tps_median, 2),
            },
            "latency_ms": {
                "avg": round(result.latency_avg_ms, 1),
                "std": round(result.latency_std_ms, 1),
                "min": round(result.latency_min_ms, 1),
                "max": round(result.latency_max_ms, 1),
                "p95": round(result.latency_p95_ms, 1),
                "p99": round(result.latency_p99_ms, 1),
            },
            "tokens": {
                "avg": round(result.tokens_avg, 0),
                "total": result.tokens_total,
            },
        },
        "stability": {
            "success_rate": round(result.success_rate, 1),
            "error_count": result.error_count,
        },
    }


# =============================================================================
# COMPARATIVA GPU (DATOS DE REFERENCIA)
# =============================================================================

GPU_REFERENCE_DATA = {
    "IBM_Power10_MMA": {
        "tps_range": (13, 17),
        "cost_per_hour": 0.0,  # On-premise
        "privacy": "total",
        "source": "Este trabajo"
    },
    "Nvidia_T4_AWS": {
        "tps_range": (20, 25),
        "cost_per_hour": 0.526,
        "privacy": "cloud",
        "source": "AWS g4dn pricing"
    },
    "Nvidia_A10G_AWS": {
        "tps_range": (40, 50),
        "cost_per_hour": 1.212,
        "privacy": "cloud",
        "source": "AWS g5 pricing"
    },
    "Nvidia_A100_GCP": {
        "tps_range": (80, 120),
        "cost_per_hour": 3.67,
        "privacy": "cloud",
        "source": "GCP a2 pricing"
    },
    "RTX_4090_Local": {
        "tps_range": (100, 150),
        "cost_per_hour": 0.0,  # CapEx ~$1600
        "privacy": "local",
        "source": "llama.cpp benchmarks"
    }
}


def calculate_speedup_vs_gpu(power10_tps: float, gpu_name: str) -> Optional[float]:
    """Calcula speedup comparativo con GPU de referencia."""
    if gpu_name not in GPU_REFERENCE_DATA:
        return None

    gpu_tps_avg = sum(GPU_REFERENCE_DATA[gpu_name]["tps_range"]) / 2
    return gpu_tps_avg / power10_tps if power10_tps > 0 else None


def format_gpu_comparison_table(power10_tps: float) -> str:
    """Genera tabla comparativa con GPUs."""
    lines = [
        "",
        "=" * 80,
        "  COMPARATIVA IBM POWER10 vs GPUs",
        "=" * 80,
        "",
        f"  {'Plataforma':<25} {'TPS':<15} {'Speedup':<12} {'$/hora':<10} {'Privacidad':<10}",
        f"  {'-'*25} {'-'*15} {'-'*12} {'-'*10} {'-'*10}",
    ]

    for name, data in GPU_REFERENCE_DATA.items():
        tps_str = f"{data['tps_range'][0]}-{data['tps_range'][1]}"
        gpu_tps_avg = sum(data['tps_range']) / 2
        speedup = gpu_tps_avg / power10_tps if power10_tps > 0 else 0

        if "Power10" in name:
            speedup_str = "1.0x (base)"
        else:
            speedup_str = f"~{speedup:.1f}x"

        cost_str = f"${data['cost_per_hour']:.2f}" if data['cost_per_hour'] > 0 else "On-prem"
        privacy_str = data['privacy']

        name_display = name.replace("_", " ")
        lines.append(f"  {name_display:<25} {tps_str:<15} {speedup_str:<12} {cost_str:<10} {privacy_str:<10}")

    lines.extend([
        "",
        "  Nota: GPUs cloud son más rápidas pero Power10 on-premise elimina",
        "  riesgo de fuga de datos PHI y cumple automáticamente con Ley 18.331.",
        "",
        "=" * 80,
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    # Demo de métricas
    print("\n" + "=" * 70)
    print("  PERFORMANCE METRICS - Demo")
    print("=" * 70)

    # Verificar MMA
    mma_enabled, mma_msg = check_mma_enabled()
    print(f"\n  MMA Status: {mma_msg}")

    # Info CPU
    cpu_info = get_cpu_info()
    print(f"\n  CPU Info:")
    print(f"    Architecture: {cpu_info['architecture']}")
    print(f"    Model: {cpu_info['model']}")
    print(f"    Cores: {cpu_info['cores']}")
    print(f"    Threads: {cpu_info['threads']}")

    # Recursos del sistema
    resources = get_system_resources()
    print(f"\n  System Resources:")
    print(f"    Memory: {resources.memory_used_gb:.1f}/{resources.memory_total_gb:.1f} GB ({resources.memory_percent:.1f}%)")
    print(f"    Load Avg: {resources.load_avg_1min:.2f} / {resources.load_avg_5min:.2f} / {resources.load_avg_15min:.2f}")

    # Comparativa GPU
    print(format_gpu_comparison_table(15.0))
