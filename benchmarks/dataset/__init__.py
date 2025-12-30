"""
Dataset module - Casos clínicos y categorías PHI para benchmark.
"""

from .casos_clinicos_spanish import (
    CASOS_CLINICOS,
    obtener_caso,
    listar_casos,
    obtener_todos_casos
)

from .phi_categories import (
    PHIType,
    PHICategoryUruguay,
    DIRECT_IDENTIFIERS,
    QUASI_IDENTIFIERS,
    PLACEHOLDERS,
    PHIEntity,
    PHIGroundTruth,
    is_direct_identifier,
    is_quasi_identifier,
    get_placeholder
)

__all__ = [
    # Casos clínicos
    "CASOS_CLINICOS",
    "obtener_caso",
    "listar_casos",
    "obtener_todos_casos",
    # PHI categories
    "PHIType",
    "PHICategoryUruguay",
    "DIRECT_IDENTIFIERS",
    "QUASI_IDENTIFIERS",
    "PLACEHOLDERS",
    "PHIEntity",
    "PHIGroundTruth",
    "is_direct_identifier",
    "is_quasi_identifier",
    "get_placeholder"
]
