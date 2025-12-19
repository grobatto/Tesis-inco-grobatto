#!/usr/bin/env python3
"""
benchmark_prompts.py - Comparativa de estrategias de prompting
Universidad de Montevideo - Tesis 2025

Ejecuta benchmarks para comparar todas las estrategias de prompting
usando un caso de prueba fijo, generando una tabla comparativa.

Uso:
    python benchmark_prompts.py                    # Usa caso_a por defecto
    python benchmark_prompts.py --caso caso_olaf  # Usa caso completo CTI
    python benchmark_prompts.py --port 8088       # Usar otro modelo
    python benchmark_prompts.py --export csv      # Exportar a CSV

Requisitos:
    pip install requests tabulate
"""

import requests
import time
import json
import statistics
import argparse
import csv
from datetime import datetime
from typing import List, Dict

from casos_sinteticos import CASOS, obtener_caso
from prompts_anonimizacion import PROMPTS, obtener_prompt, obtener_todos_los_prompts


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

DEFAULT_PORT = 8089
DEFAULT_CASO = "caso_a"  # Caso más simple para comparar prompts
DEFAULT_ITERATIONS = 3


# =============================================================================
# FUNCIONES DE BENCHMARK
# =============================================================================

def run_single_test(port: int, texto: str, prompt_template: str, timeout: int = 300) -> dict:
    """Ejecuta una única prueba de anonimización."""
    url = f"http://localhost:{port}/completion"
    prompt = prompt_template.format(text=texto)

    payload = {
        "prompt": prompt,
        "n_predict": 2000,
        "temperature": 0.3,
        "top_k": 40,
        "top_p": 0.9,
        "stop": ["```", "---END---"]
    }

    start_time = time.time()
    response = requests.post(url, json=payload, timeout=timeout)
    elapsed_ms = (time.time() - start_time) * 1000

    response.raise_for_status()
    result = response.json()

    content = result.get("content", "")
    timings = result.get("timings", {})
    tokens = timings.get("predicted_n", 0)

    if tokens == 0:
        tokens = len(content) // 4

    tps = (tokens / elapsed_ms) * 1000 if elapsed_ms > 0 else 0

    return {
        "content": content,
        "tokens": tokens,
        "time_ms": elapsed_ms,
        "tps": tps
    }


def evaluar_resultado(texto_anonimizado: str, entidades: list) -> dict:
    """Evalúa la calidad de la anonimización."""
    tp = 0
    fn = 0
    escapadas = []

    for entidad in entidades:
        valor = entidad["valor"]
        if valor in texto_anonimizado:
            fn += 1
            escapadas.append(valor)
        else:
            tp += 1

    total = len(entidades)
    precision = (tp / total * 100) if total > 0 else 0

    return {
        "total": total,
        "tp": tp,
        "fn": fn,
        "precision": precision,
        "escapadas": escapadas
    }


def benchmark_prompt(port: int, caso: dict, prompt: dict, iterations: int) -> dict:
    """Ejecuta benchmark para un prompt específico."""
    results = []
    contenidos = []

    for i in range(iterations):
        try:
            result = run_single_test(port, caso['texto'], prompt['template'])
            results.append(result)
            contenidos.append(result['content'])
        except Exception as e:
            print(f"    Error en iteración {i+1}: {e}")
            return None

    # Calcular estadísticas de rendimiento
    tps_values = [r['tps'] for r in results]
    time_values = [r['time_ms'] for r in results]

    # Evaluar calidad usando la primera respuesta
    eval_result = evaluar_resultado(contenidos[0], caso['entidades'])

    return {
        "prompt_id": prompt['id'],
        "prompt_nombre": prompt['nombre'],
        "tps_avg": statistics.mean(tps_values),
        "tps_std": statistics.stdev(tps_values) if len(tps_values) > 1 else 0,
        "time_avg_ms": statistics.mean(time_values),
        "precision": eval_result['precision'],
        "tp": eval_result['tp'],
        "fn": eval_result['fn'],
        "total": eval_result['total'],
        "escapadas": eval_result['escapadas'],
        "respuesta_ejemplo": contenidos[0][:500]
    }


def run_prompt_comparison(port: int, caso: dict, iterations: int) -> List[dict]:
    """Ejecuta benchmark comparativo de todos los prompts."""
    resultados = []
    prompts = obtener_todos_los_prompts()

    print(f"\n{'='*70}")
    print(f"  COMPARATIVA DE ESTRATEGIAS DE PROMPTING")
    print(f"{'='*70}")
    print(f"  Puerto:      {port}")
    print(f"  Caso:        {caso['nombre']}")
    print(f"  Entidades:   {caso['num_entidades']} PHI a detectar")
    print(f"  Iteraciones: {iterations} por prompt")
    print(f"  Prompts:     {len(prompts)} estrategias")
    print(f"{'='*70}\n")

    for prompt_id, prompt in prompts.items():
        print(f"  Probando [{prompt_id}] {prompt['nombre']}...", end=" ", flush=True)

        resultado = benchmark_prompt(port, caso, prompt, iterations)

        if resultado:
            resultados.append(resultado)
            print(f"OK - {resultado['tps_avg']:.1f} TPS, {resultado['precision']:.0f}% precision")
        else:
            print("FALLO")

        time.sleep(1)  # Pausa entre prompts

    return resultados


def print_comparison_table(resultados: List[dict]):
    """Imprime tabla comparativa de resultados."""
    if not resultados:
        print("\nNo hay resultados para mostrar.")
        return

    # Ordenar por precision (descendente), luego por TPS (descendente)
    resultados_sorted = sorted(resultados, key=lambda x: (-x['precision'], -x['tps_avg']))

    print(f"\n{'='*90}")
    print(f"  RESULTADOS COMPARATIVOS")
    print(f"{'='*90}")
    print(f"\n  {'#':<3} {'Prompt':<25} {'TPS':>8} {'Tiempo':>10} {'TP/Total':>10} {'Precision':>10}")
    print(f"  {'-'*3} {'-'*25} {'-'*8} {'-'*10} {'-'*10} {'-'*10}")

    for i, r in enumerate(resultados_sorted, 1):
        indicador = "★" if i == 1 else " "
        print(f"  {indicador}{i:<2} {r['prompt_nombre']:<25} {r['tps_avg']:>7.1f} "
              f"{r['time_avg_ms']:>9.0f}ms {r['tp']}/{r['total']:>7} {r['precision']:>9.1f}%")

    print(f"\n{'='*90}")

    # Mostrar el mejor prompt
    mejor = resultados_sorted[0]
    print(f"\n  ★ MEJOR PROMPT: {mejor['prompt_nombre']}")
    print(f"    - Precision: {mejor['precision']:.1f}%")
    print(f"    - TPS: {mejor['tps_avg']:.1f} tokens/seg")
    print(f"    - Entidades detectadas: {mejor['tp']}/{mejor['total']}")

    if mejor['fn'] > 0:
        print(f"    - Escapadas ({mejor['fn']}): {', '.join(mejor['escapadas'][:5])}")
        if len(mejor['escapadas']) > 5:
            print(f"      ... y {len(mejor['escapadas']) - 5} más")

    print(f"\n{'='*90}\n")


def export_to_csv(resultados: List[dict], filename: str):
    """Exporta resultados a CSV."""
    if not resultados:
        return

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Prompt ID', 'Prompt Nombre', 'TPS Promedio', 'TPS StdDev',
            'Tiempo Promedio (ms)', 'True Positives', 'False Negatives',
            'Total Entidades', 'Precision (%)'
        ])

        for r in resultados:
            writer.writerow([
                r['prompt_id'],
                r['prompt_nombre'],
                f"{r['tps_avg']:.2f}",
                f"{r['tps_std']:.2f}",
                f"{r['time_avg_ms']:.0f}",
                r['tp'],
                r['fn'],
                r['total'],
                f"{r['precision']:.1f}"
            ])

    print(f"Resultados exportados a: {filename}")


def export_to_json(resultados: List[dict], filename: str):
    """Exporta resultados a JSON."""
    if not resultados:
        return

    export_data = {
        "timestamp": datetime.now().isoformat(),
        "total_prompts": len(resultados),
        "resultados": resultados
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"Resultados exportados a: {filename}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Comparativa de estrategias de prompting para anonimización clínica",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python benchmark_prompts.py                    # Comparar prompts con caso_a
  python benchmark_prompts.py --caso caso_olaf  # Usar caso completo
  python benchmark_prompts.py --export csv      # Exportar a CSV
  python benchmark_prompts.py --export json     # Exportar a JSON
        """
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Puerto del servidor LLM (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--caso", "-c",
        type=str,
        default=DEFAULT_CASO,
        choices=list(CASOS.keys()),
        help=f"Caso de prueba a usar (default: {DEFAULT_CASO})"
    )
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Número de iteraciones por prompt (default: {DEFAULT_ITERATIONS})"
    )
    parser.add_argument(
        "--export", "-e",
        type=str,
        choices=['csv', 'json', 'both'],
        help="Formato de exportación de resultados"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="results",
        help="Directorio para archivos de salida (default: results)"
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("  BENCHMARK DE ESTRATEGIAS DE PROMPTING - IBM POWER10")
    print("  Universidad de Montevideo - Tesis 2025")
    print("="*70)

    # Obtener caso de prueba
    caso = obtener_caso(args.caso)
    print(f"\n  Caso seleccionado: {caso['nombre']}")
    print(f"  Texto: {len(caso['texto'])} caracteres")
    print(f"  Entidades PHI: {caso['num_entidades']}")

    # Ejecutar comparación
    resultados = run_prompt_comparison(args.port, caso, args.iterations)

    # Mostrar tabla
    print_comparison_table(resultados)

    # Exportar si se solicita
    if args.export and resultados:
        import os
        os.makedirs(args.output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if args.export in ['csv', 'both']:
            csv_file = f"{args.output_dir}/prompt_comparison_{args.caso}_{timestamp}.csv"
            export_to_csv(resultados, csv_file)

        if args.export in ['json', 'both']:
            json_file = f"{args.output_dir}/prompt_comparison_{args.caso}_{timestamp}.json"
            export_to_json(resultados, json_file)
