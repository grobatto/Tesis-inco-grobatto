#!/usr/bin/env python3
"""
results_analyzer.py - Analizador de Resultados y Generador de Reportes
Universidad de Montevideo - Tesis 2025

Analiza los resultados de los experimentos y genera:
- Tablas comparativas (estilo paper académico)
- Gráficos de rendimiento y calidad
- Reportes en formato Markdown
- Estadísticas agregadas

Para la tesis: Demostración del valor de MMA en IBM Power10.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import statistics

# Para gráficos (opcional - se generan si matplotlib está disponible)
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("  [WARN] matplotlib no disponible - gráficos deshabilitados")


# =============================================================================
# CARGA DE RESULTADOS
# =============================================================================

def cargar_resultados_json(filepath: str) -> Dict:
    """Carga resultados de un archivo JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def buscar_archivos_resultados(directory: str, patron: str = "*.json") -> List[str]:
    """Busca archivos de resultados en un directorio."""
    path = Path(directory)
    return sorted([str(f) for f in path.glob(patron)])


def cargar_ultimo_resultado(directory: str, tipo: str) -> Optional[Dict]:
    """Carga el resultado más reciente de un tipo de experimento."""
    archivos = buscar_archivos_resultados(directory, f"{tipo}_*.json")
    if archivos:
        return cargar_resultados_json(archivos[-1])  # Último por orden alfabético/fecha
    return None


# =============================================================================
# ANÁLISIS DE RENDIMIENTO
# =============================================================================

@dataclass
class RendimientoModelo:
    """Métricas de rendimiento de un modelo."""
    modelo_id: str
    nombre: str
    parametros: str
    tps_promedio: float
    tps_std: float
    latencia_promedio_ms: float
    casos_evaluados: int


def analizar_benchmark_rendimiento(resultados: Dict) -> List[RendimientoModelo]:
    """Analiza resultados del benchmark de rendimiento."""
    analisis = []

    for modelo_id, datos in resultados.get("resultados_por_modelo", {}).items():
        if datos.get("estado") != "completado":
            continue

        config = datos.get("configuracion", {})
        metricas = datos.get("metricas_agregadas", {})

        analisis.append(RendimientoModelo(
            modelo_id=modelo_id,
            nombre=config.get("nombre", modelo_id),
            parametros=config.get("parametros", "?B"),
            tps_promedio=metricas.get("tps_promedio_global", 0),
            tps_std=metricas.get("tps_std_global", 0),
            latencia_promedio_ms=metricas.get("latencia_promedio_global_ms", 0),
            casos_evaluados=metricas.get("casos_evaluados", 0)
        ))

    # Ordenar por TPS descendente
    analisis.sort(key=lambda x: x.tps_promedio, reverse=True)
    return analisis


def generar_tabla_rendimiento(analisis: List[RendimientoModelo]) -> str:
    """Genera tabla de rendimiento en formato Markdown."""
    lines = []
    lines.append("## Tabla de Rendimiento - Benchmark MMA Power10\n")
    lines.append("| Modelo | Parámetros | TPS (gen) | Std Dev | Latencia (ms) | Casos |")
    lines.append("|--------|------------|-----------|---------|---------------|-------|")

    for m in analisis:
        lines.append(
            f"| {m.nombre} | {m.parametros} | "
            f"{m.tps_promedio:.2f} | ±{m.tps_std:.2f} | "
            f"{m.latencia_promedio_ms:.0f} | {m.casos_evaluados} |"
        )

    # Agregar comparativa GPU teórica
    lines.append("\n### Comparativa con GPU (Referencias)")
    lines.append("| Plataforma | TPS Estimado | Speedup vs Power10 | Costo/hora | Privacidad |")
    lines.append("|------------|--------------|-------------------|------------|------------|")
    lines.append("| **IBM Power10 (MMA)** | 13-17 | 1.0x (baseline) | $0 on-prem | ✅ Total |")
    lines.append("| Nvidia T4 (AWS g4dn) | 20-25 | ~1.5x | $0.526 | ⚠️ Cloud |")
    lines.append("| Nvidia A10G (AWS g5) | 40-50 | ~3x | $1.212 | ⚠️ Cloud |")
    lines.append("| Nvidia A100 (GCP a2) | 80-120 | ~7x | $3.67 | ⚠️ Cloud |")
    lines.append("| RTX 4090 (Local) | 100-150 | ~10x | CapEx $1600 | ✅ Local |")

    return "\n".join(lines)


# =============================================================================
# ANÁLISIS DE CALIDAD
# =============================================================================

@dataclass
class CalidadModelo:
    """Métricas de calidad de un modelo."""
    modelo_id: str
    f1_micro_promedio: float
    f1_micro_std: float
    recall_promedio: float
    lrdi_promedio: float
    lrdi_100_pct: int
    tps_promedio: float
    muestras: int


def analizar_evaluacion_calidad(resultados: Dict) -> List[CalidadModelo]:
    """Analiza resultados de evaluación de calidad."""
    analisis = []

    for modelo_id, stats in resultados.get("estadisticas_por_modelo", {}).items():
        analisis.append(CalidadModelo(
            modelo_id=modelo_id,
            f1_micro_promedio=stats.get("f1_micro", {}).get("promedio", 0),
            f1_micro_std=stats.get("f1_micro", {}).get("std", 0),
            recall_promedio=stats.get("recall", {}).get("promedio", 0),
            lrdi_promedio=stats.get("lrdi", {}).get("promedio", 0),
            lrdi_100_pct=stats.get("lrdi", {}).get("casos_100_pct", 0),
            tps_promedio=stats.get("tps", {}).get("promedio", 0),
            muestras=stats.get("muestras", 0)
        ))

    # Ordenar por F1-micro descendente
    analisis.sort(key=lambda x: x.f1_micro_promedio, reverse=True)
    return analisis


def generar_tabla_calidad(analisis: List[CalidadModelo]) -> str:
    """Genera tabla de calidad en formato Markdown (estilo paper)."""
    lines = []
    lines.append("## Métricas de Calidad - Evaluación de Anonimización\n")
    lines.append("*Basado en métricas de arXiv:2412.10918 y arXiv:2406.00062*\n")
    lines.append("| Modelo | F1-micro | Std | Recall | LRDI (%) | LRDI=100% | TPS |")
    lines.append("|--------|----------|-----|--------|----------|-----------|-----|")

    for m in analisis:
        # Marcar el mejor con negrita
        f1_str = f"**{m.f1_micro_promedio:.4f}**" if m == analisis[0] else f"{m.f1_micro_promedio:.4f}"
        lrdi_warning = "⚠️" if m.lrdi_promedio < 100 else "✅"

        lines.append(
            f"| {m.modelo_id} | {f1_str} | ±{m.f1_micro_std:.4f} | "
            f"{m.recall_promedio:.4f} | {m.lrdi_promedio:.1f} {lrdi_warning} | "
            f"{m.lrdi_100_pct}/{m.muestras} | {m.tps_promedio:.1f} |"
        )

    lines.append("\n**Leyenda:**")
    lines.append("- F1-micro: Métrica global de precisión/recall")
    lines.append("- Recall: Proporción de PHI detectado (crítico para privacidad)")
    lines.append("- LRDI: Levenshtein Recall para Identificadores Directos (debe ser 100%)")
    lines.append("- LRDI=100%: Casos donde TODOS los identificadores directos fueron anonimizados")

    return "\n".join(lines)


# =============================================================================
# ANÁLISIS DE PROMPTS
# =============================================================================

def analizar_comparativa_prompts(resultados: Dict) -> Dict:
    """Analiza resultados de comparativa de prompts."""
    analisis = {
        "modelo": resultados.get("modelo", "unknown"),
        "prompts": []
    }

    for prompt_id, datos in resultados.get("resultados_por_prompt", {}).items():
        metricas = datos.get("metricas_agregadas", {})
        analisis["prompts"].append({
            "id": prompt_id,
            "nombre": datos.get("configuracion", {}).get("nombre", prompt_id),
            "f1_promedio": metricas.get("f1_promedio", 0),
            "recall_promedio": metricas.get("recall_promedio", 0),
            "lrdi_promedio": metricas.get("lrdi_promedio", 0),
            "tps_promedio": metricas.get("tps_promedio", 0),
            "casos": metricas.get("casos_evaluados", 0)
        })

    # Ordenar por F1
    analisis["prompts"].sort(key=lambda x: x["f1_promedio"], reverse=True)
    return analisis


def generar_tabla_prompts(analisis: Dict) -> str:
    """Genera tabla comparativa de prompts."""
    lines = []
    lines.append(f"## Comparativa de Estrategias de Prompting\n")
    lines.append(f"*Modelo utilizado: {analisis['modelo']}*\n")
    lines.append("| Prompt | F1 | Recall | LRDI (%) | TPS | Trade-off |")
    lines.append("|--------|-----|--------|----------|-----|-----------|")

    for p in analisis["prompts"]:
        # Determinar trade-off
        if p["f1_promedio"] > 0.9 and p["tps_promedio"] > 10:
            tradeoff = "✅ Óptimo"
        elif p["f1_promedio"] > 0.85:
            tradeoff = "Buena calidad"
        elif p["tps_promedio"] > 15:
            tradeoff = "Rápido"
        else:
            tradeoff = "Baseline"

        lines.append(
            f"| {p['nombre']} | {p['f1_promedio']:.3f} | "
            f"{p['recall_promedio']:.3f} | {p['lrdi_promedio']:.0f} | "
            f"{p['tps_promedio']:.1f} | {tradeoff} |"
        )

    return "\n".join(lines)


# =============================================================================
# GENERACIÓN DE GRÁFICOS
# =============================================================================

def generar_grafico_tps_por_modelo(analisis: List[RendimientoModelo], output_path: str):
    """Genera gráfico de barras de TPS por modelo."""
    if not MATPLOTLIB_AVAILABLE:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    modelos = [m.nombre for m in analisis]
    tps_values = [m.tps_promedio for m in analisis]
    tps_std = [m.tps_std for m in analisis]

    colors = plt.cm.Blues([0.3 + 0.7 * (i / len(modelos)) for i in range(len(modelos))])

    bars = ax.bar(modelos, tps_values, yerr=tps_std, capsize=5, color=colors, edgecolor='black')

    ax.set_ylabel('Tokens por Segundo (TPS)', fontsize=12)
    ax.set_xlabel('Modelo', fontsize=12)
    ax.set_title('Rendimiento de Inferencia - IBM Power10 con MMA', fontsize=14, fontweight='bold')

    # Línea de referencia GPU
    ax.axhline(y=25, color='red', linestyle='--', label='GPU T4 (referencia)')
    ax.legend()

    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Gráfico guardado: {output_path}")


def generar_grafico_calidad_vs_velocidad(calidad: List[CalidadModelo], output_path: str):
    """Genera gráfico scatter de calidad vs velocidad."""
    if not MATPLOTLIB_AVAILABLE:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    for m in calidad:
        color = 'green' if m.lrdi_promedio == 100 else 'orange'
        ax.scatter(m.tps_promedio, m.f1_micro_promedio, s=200, c=color, alpha=0.7, edgecolor='black')
        ax.annotate(m.modelo_id, (m.tps_promedio, m.f1_micro_promedio),
                    textcoords="offset points", xytext=(5, 5), fontsize=9)

    ax.set_xlabel('Tokens por Segundo (TPS)', fontsize=12)
    ax.set_ylabel('F1-micro Score', fontsize=12)
    ax.set_title('Trade-off Calidad vs Velocidad - Anonimización Clínica', fontsize=14, fontweight='bold')

    # Leyenda
    green_patch = mpatches.Patch(color='green', label='LRDI = 100%')
    orange_patch = mpatches.Patch(color='orange', label='LRDI < 100%')
    ax.legend(handles=[green_patch, orange_patch])

    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  Gráfico guardado: {output_path}")


# =============================================================================
# GENERACIÓN DE REPORTE COMPLETO
# =============================================================================

def generar_reporte_completo(
    results_dir: str,
    output_dir: str
) -> str:
    """
    Genera reporte completo en Markdown con todos los análisis.

    Returns:
        Path al archivo de reporte generado
    """
    print("\n" + "=" * 70)
    print("  GENERANDO REPORTE DE RESULTADOS")
    print("=" * 70)

    os.makedirs(output_dir, exist_ok=True)

    lines = []
    lines.append("# Resultados de Experimentos - Benchmark MMA Power10\n")
    lines.append(f"**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append("**Tesis:** Universidad de Montevideo 2025\n")
    lines.append("---\n")

    # Cargar y analizar rendimiento
    rendimiento = cargar_ultimo_resultado(results_dir, "benchmark_rendimiento")
    if rendimiento:
        print("  Analizando benchmark de rendimiento...")
        analisis_rend = analizar_benchmark_rendimiento(rendimiento)
        lines.append(generar_tabla_rendimiento(analisis_rend))
        lines.append("\n---\n")

        # Generar gráfico
        if MATPLOTLIB_AVAILABLE:
            generar_grafico_tps_por_modelo(
                analisis_rend,
                os.path.join(output_dir, "grafico_tps_modelos.png")
            )
            lines.append("![Rendimiento TPS](grafico_tps_modelos.png)\n")

    # Cargar y analizar calidad
    calidad = cargar_ultimo_resultado(results_dir, "evaluacion_calidad")
    if calidad:
        print("  Analizando evaluación de calidad...")
        analisis_cal = analizar_evaluacion_calidad(calidad)
        lines.append(generar_tabla_calidad(analisis_cal))
        lines.append("\n---\n")

        # Generar gráfico
        if MATPLOTLIB_AVAILABLE:
            generar_grafico_calidad_vs_velocidad(
                analisis_cal,
                os.path.join(output_dir, "grafico_calidad_velocidad.png")
            )
            lines.append("![Calidad vs Velocidad](grafico_calidad_velocidad.png)\n")

    # Cargar y analizar prompts
    prompts = cargar_ultimo_resultado(results_dir, "comparativa_prompts")
    if prompts:
        print("  Analizando comparativa de prompts...")
        analisis_prompts = analizar_comparativa_prompts(prompts)
        lines.append(generar_tabla_prompts(analisis_prompts))
        lines.append("\n---\n")

    # Conclusiones
    lines.append("## Conclusiones\n")
    lines.append("### Hallazgos Principales\n")

    if rendimiento and analisis_rend:
        mejor_modelo = analisis_rend[0]
        lines.append(f"1. **Rendimiento MMA:** El modelo más rápido fue {mejor_modelo.nombre} "
                     f"con {mejor_modelo.tps_promedio:.2f} TPS (±{mejor_modelo.tps_std:.2f}).\n")

    if calidad and analisis_cal:
        mejor_calidad = analisis_cal[0]
        lines.append(f"2. **Calidad:** El modelo con mejor F1-micro fue {mejor_calidad.modelo_id} "
                     f"con {mejor_calidad.f1_micro_promedio:.4f}.\n")

        modelos_lrdi_100 = [m for m in analisis_cal if m.lrdi_promedio == 100]
        if modelos_lrdi_100:
            lines.append(f"3. **Privacidad (LRDI=100%):** {len(modelos_lrdi_100)} modelo(s) lograron "
                         f"anonimizar el 100% de identificadores directos.\n")
        else:
            lines.append("3. **Privacidad:** Ningún modelo logró LRDI=100% en todos los casos. "
                         "Se requiere revisión humana.\n")

    lines.append("\n### Argumento 'Best Fit'\n")
    lines.append("> IBM Power10 con aceleradores MMA proporciona rendimiento suficiente (13-17 TPS) "
                 "para procesamiento batch de anonimización clínica, eliminando completamente el "
                 "riesgo de fuga de PHI a la nube y garantizando cumplimiento con Ley 18.331 de Uruguay.\n")

    lines.append("\n### Referencias Académicas\n")
    lines.append("- arXiv:2412.10918 - LLMs-in-the-Loop Part 2 (Metodología F1-micro/macro)\n")
    lines.append("- arXiv:2406.00062 - Unlocking LLMs for Clinical Text Anonymization (ALID, LR, LRDI, LRQI)\n")
    lines.append("- i2b2 2014 De-identification Challenge (18 categorías PHI)\n")

    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(output_dir, f"reporte_resultados_{timestamp}.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n  Reporte guardado: {report_path}")
    return report_path


# =============================================================================
# RESUMEN RÁPIDO EN CONSOLA
# =============================================================================

def imprimir_resumen_rapido(results_dir: str):
    """Imprime resumen rápido de resultados en consola."""
    print("\n" + "=" * 70)
    print("  RESUMEN RÁPIDO DE RESULTADOS")
    print("=" * 70)

    # Rendimiento
    rendimiento = cargar_ultimo_resultado(results_dir, "benchmark_rendimiento")
    if rendimiento:
        analisis = analizar_benchmark_rendimiento(rendimiento)
        print("\n  RENDIMIENTO (TPS por modelo):")
        print("  " + "-" * 50)
        for m in analisis[:5]:  # Top 5
            print(f"    {m.nombre:<30} {m.tps_promedio:>8.2f} TPS")

    # Calidad
    calidad = cargar_ultimo_resultado(results_dir, "evaluacion_calidad")
    if calidad:
        analisis = analizar_evaluacion_calidad(calidad)
        print("\n  CALIDAD (F1-micro por modelo):")
        print("  " + "-" * 50)
        for m in analisis[:5]:
            lrdi_mark = "✓" if m.lrdi_promedio == 100 else "✗"
            print(f"    {m.modelo_id:<30} F1={m.f1_micro_promedio:.4f} LRDI={m.lrdi_promedio:.0f}% {lrdi_mark}")

    # Prompts
    prompts = cargar_ultimo_resultado(results_dir, "comparativa_prompts")
    if prompts:
        analisis = analizar_comparativa_prompts(prompts)
        print(f"\n  PROMPTS (usando {analisis['modelo']}):")
        print("  " + "-" * 50)
        for p in analisis["prompts"][:5]:
            print(f"    {p['nombre']:<30} F1={p['f1_promedio']:.3f} TPS={p['tps_promedio']:.1f}")

    print("\n" + "=" * 70)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analizador de Resultados - Benchmark MMA Power10"
    )

    parser.add_argument("--results-dir", type=str, default="results",
                        help="Directorio con resultados JSON")
    parser.add_argument("--output-dir", type=str, default="reports",
                        help="Directorio para reportes")

    parser.add_argument("--reporte", action="store_true",
                        help="Generar reporte completo en Markdown")
    parser.add_argument("--resumen", action="store_true",
                        help="Imprimir resumen rápido en consola")
    parser.add_argument("--graficos", action="store_true",
                        help="Generar solo gráficos")

    args = parser.parse_args()

    if args.resumen:
        imprimir_resumen_rapido(args.results_dir)

    if args.reporte:
        generar_reporte_completo(args.results_dir, args.output_dir)

    if args.graficos:
        if not MATPLOTLIB_AVAILABLE:
            print("  [ERROR] matplotlib no disponible para generar gráficos")
            return

        os.makedirs(args.output_dir, exist_ok=True)

        rendimiento = cargar_ultimo_resultado(args.results_dir, "benchmark_rendimiento")
        if rendimiento:
            analisis = analizar_benchmark_rendimiento(rendimiento)
            generar_grafico_tps_por_modelo(
                analisis,
                os.path.join(args.output_dir, "grafico_tps_modelos.png")
            )

        calidad = cargar_ultimo_resultado(args.results_dir, "evaluacion_calidad")
        if calidad:
            analisis = analizar_evaluacion_calidad(calidad)
            generar_grafico_calidad_vs_velocidad(
                analisis,
                os.path.join(args.output_dir, "grafico_calidad_velocidad.png")
            )

    if not (args.reporte or args.resumen or args.graficos):
        parser.print_help()


if __name__ == "__main__":
    main()
