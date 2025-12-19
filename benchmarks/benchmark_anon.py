#!/usr/bin/env python3
"""
benchmark_anon.py - Benchmark de Anonimización de Historiales Clínicos
Universidad de Montevideo - Tesis 2025

Ejecuta benchmarks de anonimización de datos clínicos usando LLMs en IBM Power10.
Soporta múltiples casos de prueba y estrategias de prompting.

Uso:
    python benchmark_anon.py                              # Caso Olaf, prompt detailed
    python benchmark_anon.py --caso caso_a                # Caso Emergencia
    python benchmark_anon.py --caso caso_b --prompt few_shot  # Caso Oncología con few-shot
    python benchmark_anon.py --caso todos --prompt todos  # Todos los casos y prompts
    python benchmark_anon.py --port 8088 --iterations 3   # Configuración personalizada

Requisitos:
    pip install requests
"""

import requests
import time
import json
import statistics
import argparse
from datetime import datetime

# Importar casos y prompts desde módulos locales
from casos_sinteticos import CASOS, obtener_caso, obtener_todos_los_casos
from prompts_anonimizacion import PROMPTS, obtener_prompt, formatear_prompt, obtener_todos_los_prompts


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

DEFAULT_PORT = 8089
DEFAULT_ITERATIONS = 5
DEFAULT_CASO = "caso_olaf"
DEFAULT_PROMPT = "detailed"


# =============================================================================
# FUNCIONES DE EVALUACIÓN
# =============================================================================

def evaluar_anonimizacion(texto_anonimizado: str, entidades: list) -> dict:
    """
    Evalúa la calidad de la anonimización comparando con ground truth.

    Args:
        texto_anonimizado: Texto devuelto por el modelo
        entidades: Lista de entidades PHI esperadas

    Returns:
        dict con métricas: tp, fn, precision, recall, entidades_escapadas
    """
    tp = 0  # True Positives: entidades correctamente anonimizadas
    fn = 0  # False Negatives: entidades que se escaparon
    entidades_escapadas = []

    for entidad in entidades:
        valor = entidad["valor"]
        # Verificar si el valor original sigue presente en el texto
        if valor in texto_anonimizado:
            fn += 1
            entidades_escapadas.append({
                "tipo": entidad["tipo"],
                "valor": valor,
                "contexto": entidad.get("contexto", "")
            })
        else:
            tp += 1

    total = len(entidades)
    precision = (tp / total * 100) if total > 0 else 0
    recall = (tp / total * 100) if total > 0 else 0  # En este caso precision == recall

    return {
        "total_entidades": total,
        "true_positives": tp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "entidades_escapadas": entidades_escapadas
    }


def print_evaluacion(evaluacion: dict):
    """Imprime el reporte de evaluación de anonimización."""
    print(f"\n{'='*60}")
    print(f"  MÉTRICAS DE ANONIMIZACIÓN")
    print(f"{'='*60}")
    print(f"  Entidades PHI totales:    {evaluacion['total_entidades']}")
    print(f"  True Positives (TP):      {evaluacion['true_positives']}")
    print(f"  False Negatives (FN):     {evaluacion['false_negatives']}")
    print(f"  Precision:                {evaluacion['precision']:.1f}%")
    print(f"  Recall:                   {evaluacion['recall']:.1f}%")

    if evaluacion['entidades_escapadas']:
        print(f"\n  ⚠️  ENTIDADES QUE SE ESCAPARON:")
        for e in evaluacion['entidades_escapadas']:
            print(f"      [{e['tipo']}] \"{e['valor']}\" ({e['contexto']})")
    else:
        print(f"\n  ✅ TODAS las entidades fueron anonimizadas correctamente")

    print(f"{'='*60}")


# =============================================================================
# FUNCIONES DE BENCHMARK
# =============================================================================

def run_anonymization(port: int, texto: str, prompt_template: str) -> dict:
    """
    Ejecuta una solicitud de anonimización al modelo.

    Args:
        port: Puerto del servidor LLM
        texto: Texto clínico a anonimizar
        prompt_template: Template del prompt a usar

    Returns:
        dict con 'content', 'tokens', 'time_ms', 'tps'
    """
    url = f"http://localhost:{port}/completion"

    # Formatear el prompt con el texto
    prompt = prompt_template.format(text=texto)

    payload = {
        "prompt": prompt,
        "n_predict": 2000,  # Suficiente para el texto completo
        "temperature": 0.3,  # Baja temperatura para consistencia
        "top_k": 40,
        "top_p": 0.9,
        "stop": ["```", "---END---"]
    }

    start_time = time.time()
    response = requests.post(url, json=payload, timeout=300)
    elapsed_ms = (time.time() - start_time) * 1000

    response.raise_for_status()
    result = response.json()

    content = result.get("content", "")

    # Obtener tokens generados
    timings = result.get("timings", {})
    tokens = timings.get("predicted_n", 0)

    # Si no hay tokens reportados, estimar
    if tokens == 0:
        tokens = len(content) // 4  # Estimación ~4 chars/token

    # Calcular TPS
    tps = (tokens / elapsed_ms) * 1000 if elapsed_ms > 0 else 0

    return {
        "content": content,
        "tokens": tokens,
        "time_ms": elapsed_ms,
        "tps": tps,
        "timings": timings
    }


def run_benchmark(port: int, caso: dict, prompt: dict, iterations: int) -> dict:
    """
    Ejecuta el benchmark para un caso y prompt específico.

    Args:
        port: Puerto del servidor LLM
        caso: Diccionario con datos del caso de prueba
        prompt: Diccionario con datos del prompt
        iterations: Número de iteraciones

    Returns:
        dict con estadísticas del benchmark
    """
    print(f"\n{'='*60}")
    print(f"  BENCHMARK DE ANONIMIZACIÓN CLÍNICA")
    print(f"{'='*60}")
    print(f"  Puerto:     {port}")
    print(f"  Caso:       {caso['nombre']}")
    print(f"  Prompt:     {prompt['nombre']}")
    print(f"  Iteraciones: {iterations}")
    print(f"{'='*60}\n")

    results = []
    first_response = None

    for i in range(iterations):
        print(f"Iteración {i+1}/{iterations}...", end=" ", flush=True)

        try:
            result = run_anonymization(port, caso['texto'], prompt['template'])
            results.append(result)

            if first_response is None:
                first_response = result["content"]

            print(f"OK - {result['tokens']} tokens en {result['time_ms']:.0f}ms "
                  f"({result['tps']:.2f} TPS)")

        except requests.exceptions.ConnectionError:
            print(f"ERROR - No se puede conectar al servidor en puerto {port}")
            return None
        except Exception as e:
            print(f"ERROR - {e}")
            return None

        # Pequeña pausa entre iteraciones
        if i < iterations - 1:
            time.sleep(1)

    # Calcular estadísticas
    tps_values = [r["tps"] for r in results]
    time_values = [r["time_ms"] for r in results]
    token_values = [r["tokens"] for r in results]

    # Evaluar calidad de anonimización
    evaluacion = evaluar_anonimizacion(first_response, caso['entidades'])

    stats = {
        "port": port,
        "caso_id": caso['id'],
        "caso_nombre": caso['nombre'],
        "prompt_id": prompt['id'],
        "prompt_nombre": prompt['nombre'],
        "iterations": iterations,
        "timestamp": datetime.now().isoformat(),
        # Métricas de rendimiento
        "tps_avg": statistics.mean(tps_values),
        "tps_std": statistics.stdev(tps_values) if len(tps_values) > 1 else 0,
        "tps_min": min(tps_values),
        "tps_max": max(tps_values),
        "time_avg_ms": statistics.mean(time_values),
        "tokens_avg": statistics.mean(token_values),
        # Métricas de calidad
        "evaluacion": evaluacion,
        # Respuesta
        "first_response": first_response,
        "raw_results": results
    }

    return stats


def print_results(stats: dict):
    """Imprime los resultados del benchmark."""
    if stats is None:
        print("\nNo hay resultados para mostrar.")
        return

    print(f"\n{'='*60}")
    print(f"  RESULTADOS DEL BENCHMARK")
    print(f"{'='*60}")
    print(f"  Puerto:              {stats['port']}")
    print(f"  Caso:                {stats['caso_nombre']}")
    print(f"  Prompt:              {stats['prompt_nombre']}")
    print(f"  Iteraciones:         {stats['iterations']}")
    print(f"  Timestamp:           {stats['timestamp']}")
    print(f"{'='*60}")
    print(f"  TPS Promedio:        {stats['tps_avg']:.2f} tokens/seg")
    print(f"  TPS Desv. Estándar:  {stats['tps_std']:.2f}")
    print(f"  TPS Mínimo:          {stats['tps_min']:.2f}")
    print(f"  TPS Máximo:          {stats['tps_max']:.2f}")
    print(f"  Tiempo Promedio:     {stats['time_avg_ms']:.0f} ms")
    print(f"  Tokens Promedio:     {stats['tokens_avg']:.0f}")
    print(f"{'='*60}")

    # Imprimir evaluación
    print_evaluacion(stats['evaluacion'])

    print(f"\n{'='*60}")
    print(f"  PRIMERA RESPUESTA (preview)")
    print(f"{'='*60}")
    preview = stats["first_response"][:1500] if stats["first_response"] else "Sin respuesta"
    print(preview)
    if len(stats["first_response"]) > 1500:
        print(f"\n... ({len(stats['first_response']) - 1500} caracteres más)")
    print(f"{'='*60}\n")


def save_results(stats: dict, filename: str = None):
    """Guarda los resultados en un archivo JSON."""
    if stats is None:
        return

    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"results/benchmark_{stats['caso_id']}_{stats['prompt_id']}_{timestamp}.json"

    # Preparar datos para guardar
    save_stats = {k: v for k, v in stats.items() if k != "first_response"}
    save_stats["first_response_preview"] = stats["first_response"][:500] if stats["first_response"] else ""

    # Crear directorio si no existe
    import os
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else "results", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(save_stats, f, indent=2, ensure_ascii=False)

    print(f"Resultados guardados en: {filename}")
    return filename


def run_benchmark_matrix(port: int, casos: list, prompts: list, iterations: int, save: bool) -> list:
    """
    Ejecuta benchmarks para todas las combinaciones de casos y prompts.

    Args:
        port: Puerto del servidor LLM
        casos: Lista de IDs de casos a probar
        prompts: Lista de IDs de prompts a probar
        iterations: Número de iteraciones por combinación
        save: Si guardar resultados en archivos

    Returns:
        Lista de resultados de todos los benchmarks
    """
    all_results = []

    print(f"\n{'#'*60}")
    print(f"  BENCHMARK MATRIX")
    print(f"  Casos: {len(casos)} | Prompts: {len(prompts)}")
    print(f"  Total de combinaciones: {len(casos) * len(prompts)}")
    print(f"{'#'*60}")

    for caso_id in casos:
        caso = obtener_caso(caso_id)
        for prompt_id in prompts:
            prompt = obtener_prompt(prompt_id)

            stats = run_benchmark(port, caso, prompt, iterations)

            if stats:
                all_results.append(stats)
                print_results(stats)

                if save:
                    save_results(stats)

    # Imprimir resumen comparativo
    print_resumen_matrix(all_results)

    return all_results


def print_resumen_matrix(results: list):
    """Imprime un resumen comparativo de todos los benchmarks."""
    if not results:
        return

    print(f"\n{'#'*70}")
    print(f"  RESUMEN COMPARATIVO")
    print(f"{'#'*70}")
    print(f"\n  {'Caso':<25} {'Prompt':<20} {'TPS':>8} {'Precision':>10} {'Recall':>8}")
    print(f"  {'-'*25} {'-'*20} {'-'*8} {'-'*10} {'-'*8}")

    for r in results:
        print(f"  {r['caso_nombre']:<25} {r['prompt_nombre']:<20} "
              f"{r['tps_avg']:>8.2f} {r['evaluacion']['precision']:>9.1f}% "
              f"{r['evaluacion']['recall']:>7.1f}%")

    print(f"\n{'#'*70}\n")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark de anonimización clínica en IBM Power10",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python benchmark_anon.py                              # Caso Olaf, prompt detailed
  python benchmark_anon.py --caso caso_a               # Caso Emergencia Cardiología
  python benchmark_anon.py --caso caso_b --prompt few_shot
  python benchmark_anon.py --caso todos --prompt todos  # Todas las combinaciones
  python benchmark_anon.py --list-casos                # Listar casos disponibles
  python benchmark_anon.py --list-prompts              # Listar prompts disponibles
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
        help=f"Caso de prueba: caso_a, caso_b, caso_olaf, o 'todos' (default: {DEFAULT_CASO})"
    )
    parser.add_argument(
        "--prompt", "-r",
        type=str,
        default=DEFAULT_PROMPT,
        help=f"Estrategia de prompt: baseline, detailed, few_shot, chain_of_thought, master_tutor, medico, o 'todos' (default: {DEFAULT_PROMPT})"
    )
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Número de iteraciones (default: {DEFAULT_ITERATIONS})"
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Guardar resultados en archivo JSON"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Nombre del archivo de salida (default: auto-generado)"
    )
    parser.add_argument(
        "--list-casos",
        action="store_true",
        help="Listar todos los casos de prueba disponibles"
    )
    parser.add_argument(
        "--list-prompts",
        action="store_true",
        help="Listar todas las estrategias de prompting disponibles"
    )

    args = parser.parse_args()

    # Listar casos si se solicita
    if args.list_casos:
        from casos_sinteticos import listar_casos
        listar_casos()
        exit(0)

    # Listar prompts si se solicita
    if args.list_prompts:
        from prompts_anonimizacion import listar_prompts
        listar_prompts()
        exit(0)

    print("\n" + "="*60)
    print("  BENCHMARK DE ANONIMIZACIÓN CLÍNICA - IBM POWER10")
    print("  Universidad de Montevideo - Tesis 2025")
    print("="*60)

    # Determinar casos a ejecutar
    if args.caso == "todos":
        casos_ids = list(obtener_todos_los_casos().keys())
    else:
        if args.caso not in CASOS:
            print(f"\nError: Caso '{args.caso}' no encontrado.")
            print(f"Disponibles: {list(CASOS.keys())} o 'todos'")
            exit(1)
        casos_ids = [args.caso]

    # Determinar prompts a ejecutar
    if args.prompt == "todos":
        prompts_ids = list(obtener_todos_los_prompts().keys())
    else:
        if args.prompt not in PROMPTS:
            print(f"\nError: Prompt '{args.prompt}' no encontrado.")
            print(f"Disponibles: {list(PROMPTS.keys())} o 'todos'")
            exit(1)
        prompts_ids = [args.prompt]

    # Ejecutar benchmarks
    if len(casos_ids) > 1 or len(prompts_ids) > 1:
        # Ejecutar matriz de benchmarks
        results = run_benchmark_matrix(args.port, casos_ids, prompts_ids, args.iterations, args.save)
    else:
        # Ejecutar benchmark único
        caso = obtener_caso(casos_ids[0])
        prompt = obtener_prompt(prompts_ids[0])

        print(f"\nTexto clínico: {len(caso['texto'])} caracteres")
        print(f"Entidades PHI a detectar: {caso['num_entidades']}")

        stats = run_benchmark(args.port, caso, prompt, args.iterations)
        print_results(stats)

        if args.save and stats:
            save_results(stats, args.output)
