#!/usr/bin/env python3
"""
quality_metrics.py - Métricas de Calidad para Evaluación de Anonimización
Universidad de Montevideo - Tesis 2025

Implementa métricas basadas en:
- arXiv:2406.00062 - "Unlocking the Potential of LLMs for Clinical Text Anonymization"
  - ALID (Average Levenshtein Index of Dissimilarity)
  - LR (Levenshtein Recall)
  - LRDI (LR para Identificadores Directos)
  - LRQI (LR para Cuasi-Identificadores)

- arXiv:2412.10918 - "LLMs-in-the-Loop Part 2"
  - Precision, Recall, F1-micro, F1-macro
  - Evaluación por categoría PHI

Métricas para caso de uso de anonimización clínica.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict
import re
import json

# Importar categorías PHI
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from dataset.phi_categories import (
        DIRECT_IDENTIFIERS, QUASI_IDENTIFIERS, PLACEHOLDERS,
        PHIEntity, is_direct_identifier, is_quasi_identifier
    )
except ImportError:
    # Fallback si no se puede importar
    DIRECT_IDENTIFIERS = set()
    QUASI_IDENTIFIERS = set()
    PLACEHOLDERS = {}


# =============================================================================
# DISTANCIA DE LEVENSHTEIN
# =============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcula la distancia de Levenshtein entre dos strings.

    La distancia de Levenshtein es el número mínimo de operaciones
    (inserción, eliminación, sustitución) para transformar s1 en s2.

    Args:
        s1: Primer string
        s2: Segundo string

    Returns:
        Distancia de Levenshtein (entero)
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Calcula la similitud de Levenshtein normalizada entre dos strings.

    Fórmula: 1 - (distancia / max(len(s1), len(s2)))

    Returns:
        Valor entre 0 (completamente diferentes) y 1 (idénticos)
    """
    if len(s1) == 0 and len(s2) == 0:
        return 1.0

    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))

    return 1 - (distance / max_len)


# =============================================================================
# MÉTRICAS BASADAS EN PAPER arXiv:2406.00062
# =============================================================================

def calculate_alid(original_value: str, anonymized_value: str) -> float:
    """
    Calcula ALID (Average Levenshtein Index of Dissimilarity).

    Mide qué tan diferente es el valor anonimizado del original.

    ALID = 1 - similitud_levenshtein

    Un ALID alto indica mejor anonimización (el valor cambió significativamente).

    Args:
        original_value: Valor PHI original
        anonymized_value: Valor después de anonimización

    Returns:
        ALID entre 0 (sin cambio) y 1 (completamente diferente)
    """
    similarity = levenshtein_similarity(original_value, anonymized_value)
    return 1 - similarity


def calculate_lr(original_value: str, anonymized_value: str, threshold: float = 0.85) -> float:
    """
    Calcula LR (Levenshtein Recall) - Detección binaria basada en threshold.

    Paper arXiv:2406.00062: "LR measures the proportion of PHI entities
    that have been sufficiently anonymized based on a similarity threshold."

    Args:
        original_value: Valor PHI original
        anonymized_value: Valor después de anonimización
        threshold: Umbral de disimilitud requerido (default 0.85)

    Returns:
        1.0 si ALID >= threshold, 0.0 en caso contrario
    """
    alid = calculate_alid(original_value, anonymized_value)
    return 1.0 if alid >= threshold else 0.0


def calculate_lrdi(entities: List[Dict], anonymized_text: str) -> float:
    """
    Calcula LRDI (Levenshtein Recall for Direct Identifiers).

    Paper: "For direct identifiers, we use an all-or-nothing approach.
    LRDI = 100% only if ALL direct identifiers are completely anonymized."

    Identificadores directos: nombres, CI, teléfonos, emails, IDs

    Args:
        entities: Lista de entidades con 'category', 'value', 'is_direct'
        anonymized_text: Texto después de anonimización

    Returns:
        100.0 si todos los identificadores directos fueron anonimizados
        0.0 si alguno escapó
    """
    direct_entities = [e for e in entities if e.get('is_direct', False) or
                       e.get('category', '') in DIRECT_IDENTIFIERS]

    if not direct_entities:
        return 100.0  # No hay identificadores directos

    for entity in direct_entities:
        original_value = entity.get('value', '')
        # Buscar si el valor original aparece en el texto anonimizado
        if original_value and original_value in anonymized_text:
            return 0.0  # Un identificador directo escapó

    return 100.0


def calculate_lrqi(entities: List[Dict], anonymized_text: str,
                   threshold: float = 0.85) -> float:
    """
    Calcula LRQI (Levenshtein Recall for Quasi-Identifiers).

    Paper: "For quasi-identifiers, we use a proportional approach.
    Partial anonymization still counts proportionally."

    Cuasi-identificadores: fechas, ubicaciones, profesiones, edades

    Args:
        entities: Lista de entidades con 'category', 'value'
        anonymized_text: Texto después de anonimización
        threshold: Umbral de similitud (default 0.85)

    Returns:
        Porcentaje de cuasi-identificadores anonimizados (0-100)
    """
    quasi_entities = [e for e in entities if not e.get('is_direct', True) or
                      e.get('category', '') in QUASI_IDENTIFIERS]

    if not quasi_entities:
        return 100.0  # No hay cuasi-identificadores

    anonymized_count = 0
    for entity in quasi_entities:
        original_value = entity.get('value', '')
        if original_value:
            # Buscar el valor o algo similar en el texto
            if original_value not in anonymized_text:
                anonymized_count += 1
            else:
                # Verificar si fue parcialmente anonimizado
                # (esto es una simplificación - en implementación real se usaría
                # matching más sofisticado)
                pass

    return (anonymized_count / len(quasi_entities)) * 100


# =============================================================================
# MÉTRICAS ESTÁNDAR (Precision, Recall, F1)
# =============================================================================

@dataclass
class EntityMatch:
    """Representa un match entre entidad ground truth y predicción."""
    ground_truth: Optional[Dict] = None
    prediction: Optional[Dict] = None
    is_true_positive: bool = False
    is_false_positive: bool = False
    is_false_negative: bool = False
    category: str = ""


@dataclass
class QualityMetrics:
    """Métricas de calidad de anonimización."""
    # Conteos básicos
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    # Métricas estándar
    precision: float = 0.0
    recall: float = 0.0
    f1_micro: float = 0.0
    f1_macro: float = 0.0

    # Métricas por categoría
    precision_per_category: Dict[str, float] = field(default_factory=dict)
    recall_per_category: Dict[str, float] = field(default_factory=dict)
    f1_per_category: Dict[str, float] = field(default_factory=dict)

    # Métricas Levenshtein (paper 2406.00062)
    alid: float = 0.0  # Average ALID
    lr: float = 0.0    # Levenshtein Recall global
    lrdi: float = 0.0  # LR para identificadores directos
    lrqi: float = 0.0  # LR para cuasi-identificadores

    # Conteos de entidades
    total_ground_truth: int = 0
    total_predictions: int = 0
    direct_identifiers_escaped: List[Dict] = field(default_factory=list)
    quasi_identifiers_escaped: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convierte a diccionario para JSON."""
        return {
            "conteos": {
                "true_positives": self.true_positives,
                "false_positives": self.false_positives,
                "false_negatives": self.false_negatives,
                "total_ground_truth": self.total_ground_truth,
                "total_predictions": self.total_predictions
            },
            "metricas_estandar": {
                "precision": round(self.precision, 4),
                "recall": round(self.recall, 4),
                "f1_micro": round(self.f1_micro, 4),
                "f1_macro": round(self.f1_macro, 4)
            },
            "metricas_levenshtein": {
                "alid": round(self.alid, 2),
                "lr": round(self.lr, 2),
                "lrdi": round(self.lrdi, 2),
                "lrqi": round(self.lrqi, 2)
            },
            "por_categoria": {
                "precision": {k: round(v, 4) for k, v in self.precision_per_category.items()},
                "recall": {k: round(v, 4) for k, v in self.recall_per_category.items()},
                "f1": {k: round(v, 4) for k, v in self.f1_per_category.items()}
            },
            "entidades_escapadas": {
                "directos": len(self.direct_identifiers_escaped),
                "cuasi": len(self.quasi_identifiers_escaped),
                "detalle_directos": self.direct_identifiers_escaped
            }
        }


def extract_placeholders_from_text(text: str) -> List[Dict]:
    """
    Extrae placeholders del texto anonimizado.

    Detecta patrones como [NOMBRE], [CI], [DIRECCION], etc.

    Returns:
        Lista de diccionarios con 'placeholder', 'start', 'end'
    """
    # Patrón para detectar placeholders
    pattern = r'\[([A-ZÁÉÍÓÚÑ_]+)\]'

    placeholders = []
    for match in re.finditer(pattern, text):
        placeholders.append({
            'placeholder': match.group(0),
            'category': match.group(1),
            'start': match.start(),
            'end': match.end()
        })

    return placeholders


def calculate_standard_metrics(
    ground_truth_entities: List[Dict],
    anonymized_text: str,
    original_text: str
) -> QualityMetrics:
    """
    Calcula métricas estándar de evaluación.

    Basado en paper arXiv:2412.10918 - F1-micro/macro.

    Args:
        ground_truth_entities: Lista de entidades PHI esperadas
        anonymized_text: Texto después de anonimización
        original_text: Texto original

    Returns:
        QualityMetrics con todas las métricas calculadas
    """
    metrics = QualityMetrics()
    metrics.total_ground_truth = len(ground_truth_entities)

    # Contadores por categoría
    tp_per_cat = defaultdict(int)
    fp_per_cat = defaultdict(int)
    fn_per_cat = defaultdict(int)

    # Para cada entidad ground truth, verificar si fue anonimizada
    alid_values = []
    lr_values = []

    for entity in ground_truth_entities:
        original_value = entity.get('value', '')
        category = entity.get('category', 'UNKNOWN')
        is_direct = entity.get('is_direct', category in DIRECT_IDENTIFIERS)

        if original_value:
            # Verificar si el valor original aparece en el texto anonimizado
            if original_value not in anonymized_text:
                # TRUE POSITIVE: fue anonimizado
                metrics.true_positives += 1
                tp_per_cat[category] += 1

                # Calcular ALID (asumimos placeholder como reemplazo)
                placeholder = PLACEHOLDERS.get(category, '[PHI]')
                alid = calculate_alid(original_value, placeholder)
                alid_values.append(alid)
                lr_values.append(1.0)
            else:
                # FALSE NEGATIVE: no fue anonimizado (escapó)
                metrics.false_negatives += 1
                fn_per_cat[category] += 1

                alid_values.append(0.0)
                lr_values.append(0.0)

                # Registrar entidad escapada
                if is_direct:
                    metrics.direct_identifiers_escaped.append({
                        'category': category,
                        'value': original_value,
                        'context': entity.get('context', '')
                    })
                else:
                    metrics.quasi_identifiers_escaped.append({
                        'category': category,
                        'value': original_value
                    })

    # Extraer placeholders del texto anonimizado
    placeholders_found = extract_placeholders_from_text(anonymized_text)
    metrics.total_predictions = len(placeholders_found)

    # FALSE POSITIVES: placeholders sin entidad correspondiente
    # (simplificación: asumimos que cada placeholder corresponde a una entidad)
    expected_placeholders = metrics.true_positives
    if len(placeholders_found) > expected_placeholders:
        metrics.false_positives = len(placeholders_found) - expected_placeholders

    # Calcular Precision, Recall, F1
    if metrics.true_positives + metrics.false_positives > 0:
        metrics.precision = metrics.true_positives / (metrics.true_positives + metrics.false_positives)

    if metrics.true_positives + metrics.false_negatives > 0:
        metrics.recall = metrics.true_positives / (metrics.true_positives + metrics.false_negatives)

    if metrics.precision + metrics.recall > 0:
        metrics.f1_micro = 2 * (metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)

    # F1 por categoría y F1-macro
    all_categories = set(tp_per_cat.keys()) | set(fn_per_cat.keys())
    f1_values = []

    for cat in all_categories:
        tp = tp_per_cat.get(cat, 0)
        fn = fn_per_cat.get(cat, 0)
        fp = fp_per_cat.get(cat, 0)

        # Precision y Recall por categoría
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        metrics.precision_per_category[cat] = prec
        metrics.recall_per_category[cat] = rec
        metrics.f1_per_category[cat] = f1
        f1_values.append(f1)

    # F1-macro (promedio de F1 por categoría)
    if f1_values:
        metrics.f1_macro = sum(f1_values) / len(f1_values)

    # Métricas Levenshtein
    if alid_values:
        metrics.alid = (sum(alid_values) / len(alid_values)) * 100
    if lr_values:
        metrics.lr = (sum(lr_values) / len(lr_values)) * 100

    # LRDI y LRQI
    metrics.lrdi = calculate_lrdi(ground_truth_entities, anonymized_text)
    metrics.lrqi = calculate_lrqi(ground_truth_entities, anonymized_text)

    return metrics


# =============================================================================
# EVALUADOR COMPLETO
# =============================================================================

class AnonymizationEvaluator:
    """
    Evaluador completo de anonimización basado en papers académicos.

    Combina métricas de:
    - Paper arXiv:2412.10918 (F1-micro, F1-macro)
    - Paper arXiv:2406.00062 (ALID, LR, LRDI, LRQI)
    """

    def __init__(self, strict_mode: bool = True, lr_threshold: float = 0.85):
        """
        Args:
            strict_mode: Si True, LRDI requiere 100% de anonimización
            lr_threshold: Umbral para LR (default 0.85 del paper)
        """
        self.strict_mode = strict_mode
        self.lr_threshold = lr_threshold
        self.results_history = []

    def evaluate(
        self,
        original_text: str,
        anonymized_text: str,
        ground_truth_entities: List[Dict],
        case_id: str = ""
    ) -> QualityMetrics:
        """
        Evalúa la calidad de anonimización.

        Args:
            original_text: Texto original con PHI
            anonymized_text: Texto anonimizado
            ground_truth_entities: Lista de entidades PHI esperadas
            case_id: Identificador del caso

        Returns:
            QualityMetrics con todas las métricas
        """
        metrics = calculate_standard_metrics(
            ground_truth_entities,
            anonymized_text,
            original_text
        )

        # Guardar en historial
        self.results_history.append({
            'case_id': case_id,
            'metrics': metrics.to_dict()
        })

        return metrics

    def evaluate_batch(
        self,
        cases: List[Dict]
    ) -> Dict:
        """
        Evalúa múltiples casos y calcula métricas agregadas.

        Args:
            cases: Lista de casos con 'original', 'anonymized', 'entities', 'id'

        Returns:
            Diccionario con métricas individuales y agregadas
        """
        all_metrics = []

        for case in cases:
            metrics = self.evaluate(
                original_text=case.get('original', ''),
                anonymized_text=case.get('anonymized', ''),
                ground_truth_entities=case.get('entities', []),
                case_id=case.get('id', '')
            )
            all_metrics.append(metrics)

        # Calcular promedios
        if all_metrics:
            avg_precision = sum(m.precision for m in all_metrics) / len(all_metrics)
            avg_recall = sum(m.recall for m in all_metrics) / len(all_metrics)
            avg_f1_micro = sum(m.f1_micro for m in all_metrics) / len(all_metrics)
            avg_f1_macro = sum(m.f1_macro for m in all_metrics) / len(all_metrics)
            avg_alid = sum(m.alid for m in all_metrics) / len(all_metrics)
            avg_lr = sum(m.lr for m in all_metrics) / len(all_metrics)
            avg_lrdi = sum(m.lrdi for m in all_metrics) / len(all_metrics)
            avg_lrqi = sum(m.lrqi for m in all_metrics) / len(all_metrics)

            total_escaped_direct = sum(len(m.direct_identifiers_escaped) for m in all_metrics)
        else:
            avg_precision = avg_recall = avg_f1_micro = avg_f1_macro = 0.0
            avg_alid = avg_lr = avg_lrdi = avg_lrqi = 0.0
            total_escaped_direct = 0

        return {
            "casos_evaluados": len(cases),
            "metricas_promedio": {
                "precision": round(avg_precision, 4),
                "recall": round(avg_recall, 4),
                "f1_micro": round(avg_f1_micro, 4),
                "f1_macro": round(avg_f1_macro, 4),
                "alid": round(avg_alid, 2),
                "lr": round(avg_lr, 2),
                "lrdi": round(avg_lrdi, 2),
                "lrqi": round(avg_lrqi, 2)
            },
            "resumen_privacidad": {
                "total_directos_escapados": total_escaped_direct,
                "riesgo_privacidad": "ALTO" if total_escaped_direct > 0 else "BAJO"
            },
            "resultados_individuales": self.results_history
        }

    def get_summary_table(self) -> str:
        """Genera tabla resumen en formato texto."""
        if not self.results_history:
            return "No hay resultados evaluados."

        lines = []
        lines.append("=" * 80)
        lines.append("  RESUMEN DE EVALUACIÓN - Métricas de Calidad")
        lines.append("=" * 80)
        lines.append(f"\n  {'Caso':<10} {'Precision':<12} {'Recall':<12} {'F1-micro':<12} {'LRDI':<10} {'LRQI':<10}")
        lines.append("  " + "-" * 66)

        for result in self.results_history:
            m = result['metrics']['metricas_estandar']
            l = result['metrics']['metricas_levenshtein']
            lines.append(
                f"  {result['case_id']:<10} "
                f"{m['precision']:<12.4f} "
                f"{m['recall']:<12.4f} "
                f"{m['f1_micro']:<12.4f} "
                f"{l['lrdi']:<10.1f} "
                f"{l['lrqi']:<10.1f}"
            )

        lines.append("=" * 80)
        return "\n".join(lines)


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def compare_models_quality(results: List[Dict]) -> Dict:
    """
    Compara métricas de calidad entre múltiples modelos.

    Args:
        results: Lista con resultados por modelo

    Returns:
        Ranking de modelos por métrica
    """
    rankings = {
        "por_f1_micro": [],
        "por_recall": [],
        "por_lrdi": [],
        "mejor_general": None
    }

    for r in results:
        model = r.get('model', 'unknown')
        metrics = r.get('metrics', {})

        rankings["por_f1_micro"].append({
            "model": model,
            "f1_micro": metrics.get('f1_micro', 0)
        })
        rankings["por_recall"].append({
            "model": model,
            "recall": metrics.get('recall', 0)
        })
        rankings["por_lrdi"].append({
            "model": model,
            "lrdi": metrics.get('lrdi', 0)
        })

    # Ordenar rankings
    rankings["por_f1_micro"].sort(key=lambda x: x["f1_micro"], reverse=True)
    rankings["por_recall"].sort(key=lambda x: x["recall"], reverse=True)
    rankings["por_lrdi"].sort(key=lambda x: x["lrdi"], reverse=True)

    # Mejor general (prioridad: LRDI = 100, luego F1)
    perfect_lrdi = [r for r in rankings["por_lrdi"] if r["lrdi"] == 100.0]
    if perfect_lrdi:
        rankings["mejor_general"] = max(
            perfect_lrdi,
            key=lambda x: next(
                (m["f1_micro"] for m in rankings["por_f1_micro"] if m["model"] == x["model"]),
                0
            )
        )["model"]
    else:
        rankings["mejor_general"] = rankings["por_f1_micro"][0]["model"] if rankings["por_f1_micro"] else None

    return rankings


def print_metrics_summary(metrics: QualityMetrics):
    """Imprime resumen de métricas en consola."""
    print("\n" + "=" * 70)
    print("  MÉTRICAS DE CALIDAD - Evaluación de Anonimización")
    print("=" * 70)

    print("\n  MÉTRICAS ESTÁNDAR (Paper arXiv:2412.10918):")
    print("  " + "-" * 50)
    print(f"    Precision:    {metrics.precision:.4f}")
    print(f"    Recall:       {metrics.recall:.4f}")
    print(f"    F1-micro:     {metrics.f1_micro:.4f}")
    print(f"    F1-macro:     {metrics.f1_macro:.4f}")

    print("\n  MÉTRICAS LEVENSHTEIN (Paper arXiv:2406.00062):")
    print("  " + "-" * 50)
    print(f"    ALID:         {metrics.alid:.2f}%")
    print(f"    LR:           {metrics.lr:.2f}%")
    print(f"    LRDI:         {metrics.lrdi:.2f}%  {'✓' if metrics.lrdi == 100 else '✗ ALERTA'}")
    print(f"    LRQI:         {metrics.lrqi:.2f}%")

    print("\n  CONTEOS:")
    print("  " + "-" * 50)
    print(f"    True Positives:   {metrics.true_positives}")
    print(f"    False Negatives:  {metrics.false_negatives}")
    print(f"    False Positives:  {metrics.false_positives}")

    if metrics.direct_identifiers_escaped:
        print("\n  ⚠️  IDENTIFICADORES DIRECTOS ESCAPADOS:")
        for escaped in metrics.direct_identifiers_escaped[:5]:  # Máximo 5
            print(f"      - [{escaped['category']}] {escaped['value']}")

    print("\n" + "=" * 70)


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Ejemplo de evaluación
    print("=" * 70)
    print("  DEMO: Métricas de Calidad para Anonimización")
    print("=" * 70)

    # Texto original con PHI
    original = """
    El paciente Juan Pérez, CI 1.234.567-8, ingresó el 15/03/2024.
    Reside en Av. Italia 2345, Montevideo. Tel: 099-123-456.
    Atendido por Dr. García en Hospital Maciel.
    """

    # Texto anonimizado (simulado)
    anonymized = """
    El paciente [NOMBRE], CI [CI], ingresó el [FECHA].
    Reside en [DIRECCION], [UBICACION]. Tel: [TELEFONO].
    Atendido por Dr. [NOMBRE] en [UBICACION].
    """

    # Ground truth de entidades
    entities = [
        {"category": "NAME_PATIENT", "value": "Juan Pérez", "is_direct": True},
        {"category": "ID_CI", "value": "1.234.567-8", "is_direct": True},
        {"category": "DATE_ADMISSION", "value": "15/03/2024", "is_direct": False},
        {"category": "LOCATION_STREET", "value": "Av. Italia 2345", "is_direct": False},
        {"category": "LOCATION_CITY", "value": "Montevideo", "is_direct": False},
        {"category": "CONTACT_PHONE_MOBILE", "value": "099-123-456", "is_direct": True},
        {"category": "NAME_DOCTOR", "value": "García", "is_direct": True},
        {"category": "LOCATION_HOSPITAL", "value": "Hospital Maciel", "is_direct": False},
    ]

    # Evaluar
    evaluator = AnonymizationEvaluator()
    metrics = evaluator.evaluate(original, anonymized, entities, case_id="demo_01")

    print_metrics_summary(metrics)

    # Test con un caso donde escapa un identificador
    print("\n\n" + "=" * 70)
    print("  TEST: Caso con identificador directo escapado")
    print("=" * 70)

    anonymized_with_escape = """
    El paciente [NOMBRE], CI 1.234.567-8, ingresó el [FECHA].
    Reside en [DIRECCION], [UBICACION]. Tel: [TELEFONO].
    Atendido por Dr. [NOMBRE] en [UBICACION].
    """

    metrics_escaped = evaluator.evaluate(
        original, anonymized_with_escape, entities, case_id="demo_02_escaped"
    )
    print_metrics_summary(metrics_escaped)
