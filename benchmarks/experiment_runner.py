#!/usr/bin/env python3
"""
experiment_runner.py - Orquestador Principal de Experimentos
Universidad de Montevideo - Tesis 2025

Ejecuta los experimentos del benchmark de anonimización sobre IBM Power10 con MMA.

Objetivo Principal: Demostrar el valor de los aceleradores MMA para inferencia GenAI.
Caso de Uso: Anonimización de datos clínicos.

Experimentos:
1. Benchmark de Rendimiento MMA (TPS, latencia, throughput)
2. Comparativa de Prompts (8 estrategias)
3. Evaluación de Calidad (métricas de papers académicos)

Basado en:
- arXiv:2412.10918 - LLMs-in-the-Loop Part 2
- arXiv:2406.00062 - Unlocking LLMs for Clinical Text Anonymization
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import subprocess
import statistics

# Agregar path para imports locales
sys.path.insert(0, str(Path(__file__).parent))

from prompts_anonimizacion import PROMPTS, formatear_prompt
from dataset.casos_clinicos_spanish import CASOS_CLINICOS, obtener_caso, listar_casos
from dataset.phi_categories import DIRECT_IDENTIFIERS, QUASI_IDENTIFIERS
from metrics.performance_metrics import (
    InferenceMetrics, BenchmarkResult,
    calculate_tps, measure_latency_stats,
    get_system_resources, GPU_REFERENCE_BENCHMARKS
)
from metrics.quality_metrics import (
    QualityMetrics, AnonymizationEvaluator,
    calculate_standard_metrics, print_metrics_summary
)


# =============================================================================
# CONFIGURACIÓN DE MODELOS
# =============================================================================

MODELOS_CONFIG = {
    "phi-3.5-mini": {
        "nombre": "Phi-3.5 Mini Instruct",
        "puerto": 8093,
        "parametros": "3.5B",
        "cuantizacion": "Q4_K_M",
        "archivo": "phi-3.5-mini-instruct.Q4_K_M.gguf",
        "contexto": 4096
    },
    "mistral-nemo-12b": {
        "nombre": "Mistral Nemo 12B Instruct",
        "puerto": 8097,
        "parametros": "12B",
        "cuantizacion": "Q4_K_M",
        "archivo": "mistral-nemo-12b-instruct-2407.Q4_K_M.gguf",
        "contexto": 8192
    },
    "qwen2.5-7b": {
        "nombre": "Qwen 2.5 7B Instruct",
        "puerto": 8089,
        "parametros": "7B",
        "cuantizacion": "Q4_K_M",
        "archivo": "qwen2.5-7b-instruct.Q4_K_M.gguf",
        "contexto": 8192
    },
    "biomistral-7b": {
        "nombre": "BioMistral 7B",
        "puerto": 8092,
        "parametros": "7B",
        "cuantizacion": "Q4_K_M",
        "archivo": "biomistral-7b.Q4_K_M.gguf",
        "contexto": 4096
    },
    "llama-3.1-8b": {
        "nombre": "Llama 3.1 8B Instruct",
        "puerto": 8094,
        "parametros": "8B",
        "cuantizacion": "Q4_K_M",
        "archivo": "llama-3.1-8b-instruct.Q4_K_M.gguf",
        "contexto": 8192
    },
    "gemma-2-9b": {
        "nombre": "Gemma 2 9B Instruct",
        "puerto": 8095,
        "parametros": "9B",
        "cuantizacion": "Q4_K_M",
        "archivo": "gemma-2-9b-it.Q4_K_M.gguf",
        "contexto": 8192
    }
}


# =============================================================================
# CLIENTE LLAMA.CPP
# =============================================================================

@dataclass
class LlamaResponse:
    """Respuesta del servidor llama.cpp."""
    texto: str
    tokens_generados: int
    tokens_prompt: int
    tiempo_generacion_ms: float
    tiempo_prompt_ms: float
    tps_generacion: float
    tps_prompt: float
    exito: bool
    error: str = ""


def llamar_modelo(
    prompt: str,
    puerto: int,
    host: str = "localhost",
    temperatura: float = 0.1,
    max_tokens: int = 2048,
    timeout: int = 120
) -> LlamaResponse:
    """
    Llama al servidor llama.cpp con un prompt.

    Args:
        prompt: Texto del prompt
        puerto: Puerto del servidor
        host: Host del servidor
        temperatura: Temperatura de generación
        max_tokens: Máximo de tokens a generar
        timeout: Timeout en segundos

    Returns:
        LlamaResponse con resultados de la inferencia
    """
    url = f"http://{host}:{puerto}/completion"

    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": temperatura,
        "top_k": 40,
        "top_p": 0.95,
        "stop": ["</s>", "<|end|>", "<|eot_id|>", "<|im_end|>"],
        "stream": False
    }

    try:
        inicio = time.time()
        response = requests.post(url, json=payload, timeout=timeout)
        tiempo_total = (time.time() - inicio) * 1000  # ms

        if response.status_code == 200:
            data = response.json()

            # Extraer métricas de la respuesta
            tokens_gen = data.get("tokens_predicted", 0)
            tokens_prompt = data.get("tokens_evaluated", 0)
            tiempo_gen = data.get("timings", {}).get("predicted_ms", tiempo_total)
            tiempo_prompt = data.get("timings", {}).get("prompt_ms", 0)

            tps_gen = tokens_gen / (tiempo_gen / 1000) if tiempo_gen > 0 else 0
            tps_prompt = tokens_prompt / (tiempo_prompt / 1000) if tiempo_prompt > 0 else 0

            return LlamaResponse(
                texto=data.get("content", ""),
                tokens_generados=tokens_gen,
                tokens_prompt=tokens_prompt,
                tiempo_generacion_ms=tiempo_gen,
                tiempo_prompt_ms=tiempo_prompt,
                tps_generacion=tps_gen,
                tps_prompt=tps_prompt,
                exito=True
            )
        else:
            return LlamaResponse(
                texto="",
                tokens_generados=0,
                tokens_prompt=0,
                tiempo_generacion_ms=0,
                tiempo_prompt_ms=0,
                tps_generacion=0,
                tps_prompt=0,
                exito=False,
                error=f"HTTP {response.status_code}: {response.text[:200]}"
            )

    except requests.exceptions.Timeout:
        return LlamaResponse(
            texto="",
            tokens_generados=0,
            tokens_prompt=0,
            tiempo_generacion_ms=timeout * 1000,
            tiempo_prompt_ms=0,
            tps_generacion=0,
            tps_prompt=0,
            exito=False,
            error=f"Timeout después de {timeout}s"
        )
    except Exception as e:
        return LlamaResponse(
            texto="",
            tokens_generados=0,
            tokens_prompt=0,
            tiempo_generacion_ms=0,
            tiempo_prompt_ms=0,
            tps_generacion=0,
            tps_prompt=0,
            exito=False,
            error=str(e)
        )


def verificar_modelo_disponible(puerto: int, host: str = "localhost") -> bool:
    """Verifica si el modelo está disponible en el puerto especificado."""
    try:
        response = requests.get(f"http://{host}:{puerto}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# =============================================================================
# EXPERIMENTO 1: BENCHMARK DE RENDIMIENTO MMA
# =============================================================================

def ejecutar_benchmark_rendimiento(
    modelos: List[str],
    casos: List[str],
    prompt_id: str = "detailed",
    iteraciones: int = 3,
    host: str = "localhost",
    output_dir: str = "results"
) -> Dict:
    """
    Ejecuta benchmark de rendimiento para medir TPS, latencia y throughput.

    Objetivo: Cuantificar el rendimiento de MMA en IBM Power10.

    Args:
        modelos: Lista de IDs de modelos a evaluar
        casos: Lista de IDs de casos clínicos
        prompt_id: Estrategia de prompting a usar
        iteraciones: Número de repeticiones por caso
        host: Host del servidor
        output_dir: Directorio para resultados

    Returns:
        Diccionario con resultados del benchmark
    """
    print("\n" + "=" * 80)
    print("  EXPERIMENTO 1: BENCHMARK DE RENDIMIENTO MMA")
    print("=" * 80)
    print(f"  Modelos: {len(modelos)} | Casos: {len(casos)} | Iteraciones: {iteraciones}")
    print(f"  Prompt: {prompt_id}")
    print("=" * 80 + "\n")

    resultados = {
        "experimento": "benchmark_rendimiento",
        "timestamp": datetime.now().isoformat(),
        "configuracion": {
            "modelos": modelos,
            "casos": casos,
            "prompt_id": prompt_id,
            "iteraciones": iteraciones
        },
        "resultados_por_modelo": {}
    }

    for modelo_id in modelos:
        if modelo_id not in MODELOS_CONFIG:
            print(f"  [SKIP] Modelo {modelo_id} no configurado")
            continue

        config = MODELOS_CONFIG[modelo_id]
        puerto = config["puerto"]

        print(f"\n  [{modelo_id}] {config['nombre']}")
        print(f"    Puerto: {puerto} | Parámetros: {config['parametros']}")

        # Verificar disponibilidad
        if not verificar_modelo_disponible(puerto, host):
            print(f"    [ERROR] Modelo no disponible en puerto {puerto}")
            resultados["resultados_por_modelo"][modelo_id] = {
                "estado": "no_disponible",
                "error": f"No responde en puerto {puerto}"
            }
            continue

        metricas_modelo = []

        for caso_id in casos:
            caso = obtener_caso(caso_id)
            if not caso:
                continue

            texto = caso["texto"]
            prompt_completo = formatear_prompt(prompt_id, texto)

            print(f"    Caso {caso_id}: ", end="", flush=True)

            tps_valores = []
            latencias = []

            for i in range(iteraciones):
                response = llamar_modelo(prompt_completo, puerto, host)

                if response.exito:
                    tps_valores.append(response.tps_generacion)
                    latencias.append(response.tiempo_generacion_ms)
                    print(".", end="", flush=True)
                else:
                    print("x", end="", flush=True)

            if tps_valores:
                metricas_modelo.append({
                    "caso_id": caso_id,
                    "tps_promedio": statistics.mean(tps_valores),
                    "tps_std": statistics.stdev(tps_valores) if len(tps_valores) > 1 else 0,
                    "latencia_promedio_ms": statistics.mean(latencias),
                    "latencia_p95_ms": sorted(latencias)[int(len(latencias) * 0.95)] if latencias else 0,
                    "iteraciones_exitosas": len(tps_valores)
                })
                print(f" TPS: {statistics.mean(tps_valores):.2f}")
            else:
                print(" [FAILED]")

        # Calcular métricas agregadas del modelo
        if metricas_modelo:
            tps_todos = [m["tps_promedio"] for m in metricas_modelo]
            lat_todos = [m["latencia_promedio_ms"] for m in metricas_modelo]

            resultados["resultados_por_modelo"][modelo_id] = {
                "estado": "completado",
                "configuracion": config,
                "metricas_agregadas": {
                    "tps_promedio_global": statistics.mean(tps_todos),
                    "tps_std_global": statistics.stdev(tps_todos) if len(tps_todos) > 1 else 0,
                    "latencia_promedio_global_ms": statistics.mean(lat_todos),
                    "casos_evaluados": len(metricas_modelo)
                },
                "metricas_por_caso": metricas_modelo
            }

    # Guardar resultados
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"benchmark_rendimiento_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: {output_file}")
    return resultados


# =============================================================================
# EXPERIMENTO 2: COMPARATIVA DE PROMPTS
# =============================================================================

def ejecutar_comparativa_prompts(
    modelo_id: str,
    prompts: List[str],
    casos: List[str],
    host: str = "localhost",
    output_dir: str = "results"
) -> Dict:
    """
    Compara diferentes estrategias de prompting.

    Args:
        modelo_id: ID del modelo a usar
        prompts: Lista de IDs de prompts a evaluar
        casos: Lista de IDs de casos clínicos
        host: Host del servidor
        output_dir: Directorio para resultados

    Returns:
        Diccionario con resultados comparativos
    """
    print("\n" + "=" * 80)
    print("  EXPERIMENTO 2: COMPARATIVA DE ESTRATEGIAS DE PROMPTING")
    print("=" * 80)
    print(f"  Modelo: {modelo_id} | Prompts: {len(prompts)} | Casos: {len(casos)}")
    print("=" * 80 + "\n")

    if modelo_id not in MODELOS_CONFIG:
        print(f"  [ERROR] Modelo {modelo_id} no configurado")
        return {}

    config = MODELOS_CONFIG[modelo_id]
    puerto = config["puerto"]

    if not verificar_modelo_disponible(puerto, host):
        print(f"  [ERROR] Modelo no disponible en puerto {puerto}")
        return {}

    resultados = {
        "experimento": "comparativa_prompts",
        "timestamp": datetime.now().isoformat(),
        "modelo": modelo_id,
        "resultados_por_prompt": {}
    }

    evaluator = AnonymizationEvaluator()

    for prompt_id in prompts:
        if prompt_id not in PROMPTS:
            print(f"  [SKIP] Prompt {prompt_id} no encontrado")
            continue

        prompt_config = PROMPTS[prompt_id]
        print(f"\n  [{prompt_id}] {prompt_config['nombre']}")

        metricas_prompt = []

        for caso_id in casos:
            caso = obtener_caso(caso_id)
            if not caso:
                continue

            texto = caso["texto"]
            entities = caso.get("entidades", [])
            prompt_completo = formatear_prompt(prompt_id, texto)

            print(f"    Caso {caso_id}: ", end="", flush=True)

            response = llamar_modelo(prompt_completo, puerto, host)

            if response.exito:
                # Evaluar calidad
                quality = evaluator.evaluate(
                    original_text=texto,
                    anonymized_text=response.texto,
                    ground_truth_entities=entities,
                    case_id=caso_id
                )

                metricas_prompt.append({
                    "caso_id": caso_id,
                    "tps": response.tps_generacion,
                    "latencia_ms": response.tiempo_generacion_ms,
                    "tokens_generados": response.tokens_generados,
                    "precision": quality.precision,
                    "recall": quality.recall,
                    "f1_micro": quality.f1_micro,
                    "lrdi": quality.lrdi,
                    "lrqi": quality.lrqi,
                    "directos_escapados": len(quality.direct_identifiers_escaped)
                })
                print(f"F1: {quality.f1_micro:.3f} | LRDI: {quality.lrdi:.0f}%")
            else:
                print(f"[ERROR] {response.error[:50]}")

        # Agregar métricas del prompt
        if metricas_prompt:
            resultados["resultados_por_prompt"][prompt_id] = {
                "configuracion": prompt_config,
                "metricas_agregadas": {
                    "f1_promedio": statistics.mean([m["f1_micro"] for m in metricas_prompt]),
                    "recall_promedio": statistics.mean([m["recall"] for m in metricas_prompt]),
                    "lrdi_promedio": statistics.mean([m["lrdi"] for m in metricas_prompt]),
                    "tps_promedio": statistics.mean([m["tps"] for m in metricas_prompt]),
                    "casos_evaluados": len(metricas_prompt)
                },
                "metricas_por_caso": metricas_prompt
            }

    # Guardar resultados
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"comparativa_prompts_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: {output_file}")
    return resultados


# =============================================================================
# EXPERIMENTO 3: EVALUACIÓN DE CALIDAD COMPLETA
# =============================================================================

def ejecutar_evaluacion_calidad(
    modelos: List[str],
    prompts: List[str],
    casos: List[str],
    iteraciones: int = 3,
    host: str = "localhost",
    output_dir: str = "results"
) -> Dict:
    """
    Evaluación completa de calidad con métricas de papers académicos.

    Métricas:
    - Precision, Recall, F1-micro, F1-macro (paper arXiv:2412.10918)
    - ALID, LR, LRDI, LRQI (paper arXiv:2406.00062)

    Args:
        modelos: Lista de IDs de modelos
        prompts: Lista de IDs de prompts
        casos: Lista de IDs de casos
        iteraciones: Repeticiones por combinación
        host: Host del servidor
        output_dir: Directorio para resultados

    Returns:
        Diccionario con resultados completos
    """
    print("\n" + "=" * 80)
    print("  EXPERIMENTO 3: EVALUACIÓN DE CALIDAD (MÉTRICAS PAPERS)")
    print("=" * 80)
    print(f"  Modelos: {len(modelos)} | Prompts: {len(prompts)} | Casos: {len(casos)}")
    print(f"  Iteraciones: {iteraciones}")
    print("=" * 80 + "\n")

    resultados = {
        "experimento": "evaluacion_calidad",
        "timestamp": datetime.now().isoformat(),
        "referencias": [
            "arXiv:2412.10918 - LLMs-in-the-Loop Part 2",
            "arXiv:2406.00062 - Unlocking LLMs for Clinical Text Anonymization"
        ],
        "resultados": []
    }

    total_combinaciones = len(modelos) * len(prompts) * len(casos) * iteraciones
    combinacion_actual = 0

    for modelo_id in modelos:
        if modelo_id not in MODELOS_CONFIG:
            continue

        config = MODELOS_CONFIG[modelo_id]
        puerto = config["puerto"]

        if not verificar_modelo_disponible(puerto, host):
            print(f"  [SKIP] {modelo_id} no disponible")
            continue

        print(f"\n  === {config['nombre']} ===")

        for prompt_id in prompts:
            if prompt_id not in PROMPTS:
                continue

            evaluator = AnonymizationEvaluator()

            for caso_id in casos:
                caso = obtener_caso(caso_id)
                if not caso:
                    continue

                texto = caso["texto"]
                entities = caso.get("entidades", [])

                for iteracion in range(iteraciones):
                    combinacion_actual += 1
                    progreso = (combinacion_actual / total_combinaciones) * 100

                    print(f"\r    [{progreso:5.1f}%] {modelo_id} + {prompt_id} + {caso_id} (iter {iteracion+1})", end="")

                    prompt_completo = formatear_prompt(prompt_id, texto)
                    response = llamar_modelo(prompt_completo, puerto, host)

                    if response.exito:
                        quality = evaluator.evaluate(
                            original_text=texto,
                            anonymized_text=response.texto,
                            ground_truth_entities=entities,
                            case_id=f"{caso_id}_iter{iteracion}"
                        )

                        resultados["resultados"].append({
                            "modelo": modelo_id,
                            "prompt": prompt_id,
                            "caso": caso_id,
                            "iteracion": iteracion + 1,
                            "rendimiento": {
                                "tps_generacion": response.tps_generacion,
                                "tps_prompt": response.tps_prompt,
                                "latencia_total_ms": response.tiempo_generacion_ms + response.tiempo_prompt_ms,
                                "tokens_generados": response.tokens_generados
                            },
                            "calidad": {
                                "precision": quality.precision,
                                "recall": quality.recall,
                                "f1_micro": quality.f1_micro,
                                "f1_macro": quality.f1_macro,
                                "alid": quality.alid,
                                "lr": quality.lr,
                                "lrdi": quality.lrdi,
                                "lrqi": quality.lrqi
                            },
                            "entidades": {
                                "total_esperadas": len(entities),
                                "true_positives": quality.true_positives,
                                "false_negatives": quality.false_negatives,
                                "directos_escapados": len(quality.direct_identifiers_escaped)
                            }
                        })

    print("\n")

    # Calcular estadísticas agregadas
    if resultados["resultados"]:
        # Agrupar por modelo
        por_modelo = {}
        for r in resultados["resultados"]:
            m = r["modelo"]
            if m not in por_modelo:
                por_modelo[m] = []
            por_modelo[m].append(r)

        resultados["estadisticas_por_modelo"] = {}
        for modelo, datos in por_modelo.items():
            f1_values = [d["calidad"]["f1_micro"] for d in datos]
            recall_values = [d["calidad"]["recall"] for d in datos]
            lrdi_values = [d["calidad"]["lrdi"] for d in datos]
            tps_values = [d["rendimiento"]["tps_generacion"] for d in datos]

            resultados["estadisticas_por_modelo"][modelo] = {
                "f1_micro": {
                    "promedio": statistics.mean(f1_values),
                    "std": statistics.stdev(f1_values) if len(f1_values) > 1 else 0,
                    "min": min(f1_values),
                    "max": max(f1_values)
                },
                "recall": {
                    "promedio": statistics.mean(recall_values),
                    "std": statistics.stdev(recall_values) if len(recall_values) > 1 else 0
                },
                "lrdi": {
                    "promedio": statistics.mean(lrdi_values),
                    "casos_100_pct": sum(1 for v in lrdi_values if v == 100.0)
                },
                "tps": {
                    "promedio": statistics.mean(tps_values),
                    "std": statistics.stdev(tps_values) if len(tps_values) > 1 else 0
                },
                "muestras": len(datos)
            }

    # Guardar resultados
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"evaluacion_calidad_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"  Resultados guardados en: {output_file}")
    return resultados


# =============================================================================
# EJECUCIÓN COMPLETA DE TODOS LOS EXPERIMENTOS
# =============================================================================

def ejecutar_todos_experimentos(
    host: str = "localhost",
    output_dir: str = "results"
) -> Dict:
    """
    Ejecuta todos los experimentos del protocolo v3.0.

    Returns:
        Diccionario con todos los resultados
    """
    print("\n")
    print("=" * 80)
    print("  PROTOCOLO DE EXPERIMENTACIÓN v3.0")
    print("  Validación de Aceleradores MMA en IBM Power10")
    print("=" * 80)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Host: {host}")
    print(f"  Output: {output_dir}")
    print("=" * 80)

    # Configuración de experimentos
    todos_modelos = list(MODELOS_CONFIG.keys())
    todos_prompts = list(PROMPTS.keys())
    todos_casos = list(CASOS_CLINICOS.keys())

    resultados_completos = {
        "protocolo_version": "3.0",
        "timestamp_inicio": datetime.now().isoformat(),
        "experimentos": {}
    }

    # Experimento 1: Rendimiento
    print("\n\n  INICIANDO EXPERIMENTO 1...")
    resultados_completos["experimentos"]["rendimiento"] = ejecutar_benchmark_rendimiento(
        modelos=todos_modelos,
        casos=todos_casos[:5],  # Primeros 5 casos para rapidez
        prompt_id="detailed",
        iteraciones=3,
        host=host,
        output_dir=output_dir
    )

    # Experimento 2: Comparativa de Prompts
    print("\n\n  INICIANDO EXPERIMENTO 2...")
    # Usar el modelo con mejor disponibilidad
    modelo_para_prompts = "mistral-nemo-12b"  # O detectar automáticamente
    resultados_completos["experimentos"]["prompts"] = ejecutar_comparativa_prompts(
        modelo_id=modelo_para_prompts,
        prompts=todos_prompts,
        casos=todos_casos[:5],
        host=host,
        output_dir=output_dir
    )

    # Experimento 3: Calidad Completa
    print("\n\n  INICIANDO EXPERIMENTO 3...")
    # Top 3 modelos y top 3 prompts
    top_modelos = ["mistral-nemo-12b", "phi-3.5-mini", "qwen2.5-7b"]
    top_prompts = ["detailed", "few_shot", "hybrid"]
    resultados_completos["experimentos"]["calidad"] = ejecutar_evaluacion_calidad(
        modelos=top_modelos,
        prompts=top_prompts,
        casos=todos_casos,
        iteraciones=3,
        host=host,
        output_dir=output_dir
    )

    resultados_completos["timestamp_fin"] = datetime.now().isoformat()

    # Guardar resultados completos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"experimentos_completos_{timestamp}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resultados_completos, f, indent=2, ensure_ascii=False)

    print("\n\n" + "=" * 80)
    print("  EXPERIMENTOS COMPLETADOS")
    print("=" * 80)
    print(f"  Resultados guardados en: {output_file}")
    print("=" * 80 + "\n")

    return resultados_completos


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Orquestador de Experimentos - Benchmark MMA Power10",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Ejecutar todos los experimentos
  python experiment_runner.py --all

  # Solo benchmark de rendimiento
  python experiment_runner.py --rendimiento --modelos phi-3.5-mini mistral-nemo-12b

  # Comparativa de prompts con un modelo específico
  python experiment_runner.py --prompts --modelo mistral-nemo-12b

  # Evaluación de calidad completa
  python experiment_runner.py --calidad --iteraciones 5
        """
    )

    parser.add_argument("--all", action="store_true",
                        help="Ejecutar todos los experimentos")
    parser.add_argument("--rendimiento", action="store_true",
                        help="Ejecutar benchmark de rendimiento")
    parser.add_argument("--prompts", action="store_true",
                        help="Ejecutar comparativa de prompts")
    parser.add_argument("--calidad", action="store_true",
                        help="Ejecutar evaluación de calidad")

    parser.add_argument("--modelos", nargs="+", default=None,
                        help="Modelos a evaluar")
    parser.add_argument("--modelo", type=str, default="mistral-nemo-12b",
                        help="Modelo para comparativa de prompts")
    parser.add_argument("--casos", nargs="+", default=None,
                        help="Casos a evaluar")
    parser.add_argument("--iteraciones", type=int, default=3,
                        help="Número de iteraciones")

    parser.add_argument("--host", type=str, default="localhost",
                        help="Host del servidor llama.cpp")
    parser.add_argument("--output", type=str, default="results",
                        help="Directorio de salida")

    parser.add_argument("--listar-modelos", action="store_true",
                        help="Listar modelos disponibles")
    parser.add_argument("--listar-prompts", action="store_true",
                        help="Listar prompts disponibles")
    parser.add_argument("--listar-casos", action="store_true",
                        help="Listar casos clínicos")

    args = parser.parse_args()

    # Listar opciones
    if args.listar_modelos:
        print("\n  MODELOS DISPONIBLES:")
        for mid, config in MODELOS_CONFIG.items():
            print(f"    [{mid}] {config['nombre']} ({config['parametros']}) - Puerto {config['puerto']}")
        return

    if args.listar_prompts:
        from prompts_anonimizacion import listar_prompts
        listar_prompts()
        return

    if args.listar_casos:
        listar_casos()
        return

    # Configurar modelos y casos
    modelos = args.modelos or list(MODELOS_CONFIG.keys())
    casos = args.casos or list(CASOS_CLINICOS.keys())

    # Ejecutar experimentos
    if args.all:
        ejecutar_todos_experimentos(host=args.host, output_dir=args.output)

    elif args.rendimiento:
        ejecutar_benchmark_rendimiento(
            modelos=modelos,
            casos=casos,
            iteraciones=args.iteraciones,
            host=args.host,
            output_dir=args.output
        )

    elif args.prompts:
        ejecutar_comparativa_prompts(
            modelo_id=args.modelo,
            prompts=list(PROMPTS.keys()),
            casos=casos,
            host=args.host,
            output_dir=args.output
        )

    elif args.calidad:
        ejecutar_evaluacion_calidad(
            modelos=modelos[:3],  # Top 3
            prompts=["detailed", "few_shot", "hybrid"],
            casos=casos,
            iteraciones=args.iteraciones,
            host=args.host,
            output_dir=args.output
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
