"""
Metrics module - Métricas de rendimiento y calidad para benchmark.
"""

from .performance_metrics import (
    InferenceMetrics,
    BenchmarkResult,
    calculate_tps,
    measure_latency_stats,
    get_system_resources,
    GPU_REFERENCE_BENCHMARKS,
    print_benchmark_summary
)

from .quality_metrics import (
    QualityMetrics,
    AnonymizationEvaluator,
    calculate_standard_metrics,
    calculate_alid,
    calculate_lr,
    calculate_lrdi,
    calculate_lrqi,
    levenshtein_distance,
    levenshtein_similarity,
    print_metrics_summary
)

__all__ = [
    # Performance
    "InferenceMetrics",
    "BenchmarkResult",
    "calculate_tps",
    "measure_latency_stats",
    "get_system_resources",
    "GPU_REFERENCE_BENCHMARKS",
    "print_benchmark_summary",
    # Quality
    "QualityMetrics",
    "AnonymizationEvaluator",
    "calculate_standard_metrics",
    "calculate_alid",
    "calculate_lr",
    "calculate_lrdi",
    "calculate_lrqi",
    "levenshtein_distance",
    "levenshtein_similarity",
    "print_metrics_summary"
]
