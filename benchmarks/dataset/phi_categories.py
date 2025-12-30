#!/usr/bin/env python3
"""
phi_categories.py - Categorías de Protected Health Information (PHI)
Universidad de Montevideo - Tesis 2025

Basado en:
- i2b2 2014 De-identification Challenge (18 categorías PHI)
- HIPAA Safe Harbor (18 identificadores)
- Ley 18.331 de Uruguay (Datos Sensibles)
- arXiv:2412.10918 (LLMs-in-the-Loop Part 2)

Adaptado para el contexto uruguayo con identificadores locales.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

# =============================================================================
# CATEGORÍAS PHI SEGÚN i2b2 2014
# =============================================================================

class PHIType(Enum):
    """
    Tipos de PHI según i2b2 2014 De-identification Challenge.

    Referencia: Stubbs et al. (2015) - "Automated Systems for the
    De-identification of Longitudinal Clinical Narratives"
    """
    # === IDENTIFICADORES DIRECTOS (Critical) ===
    # Requieren LRDI = 100% (todo o nada)

    # Nombres
    PATIENT = "PATIENT"          # Nombre del paciente
    DOCTOR = "DOCTOR"            # Nombre del médico
    USERNAME = "USERNAME"        # Nombre de usuario del sistema

    # Identificadores numéricos
    MEDICALRECORD = "MEDICALRECORD"  # Número de historia clínica
    IDNUM = "IDNUM"              # Otros números de ID
    DEVICE = "DEVICE"            # Números de serie de dispositivos
    BIOID = "BIOID"              # Identificadores biométricos

    # Contacto
    PHONE = "PHONE"              # Números de teléfono
    FAX = "FAX"                  # Números de fax
    EMAIL = "EMAIL"              # Direcciones de email
    URL = "URL"                  # URLs personales
    IPADDR = "IPADDR"            # Direcciones IP

    # === CUASI-IDENTIFICADORES (Proportional) ===
    # Evaluados con LRQI proporcional

    # Ubicación
    STREET = "STREET"            # Dirección (calle, número)
    CITY = "CITY"                # Ciudad
    STATE = "STATE"              # Estado/Departamento
    COUNTRY = "COUNTRY"          # País
    ZIP = "ZIP"                  # Código postal
    LOCATION = "LOCATION"        # Ubicación genérica
    HOSPITAL = "HOSPITAL"        # Institución médica
    ORGANIZATION = "ORGANIZATION"  # Otra organización

    # Temporal
    DATE = "DATE"                # Fechas específicas
    AGE = "AGE"                  # Edad (>89 años es PHI según HIPAA)

    # Ocupación
    PROFESSION = "PROFESSION"    # Profesión/ocupación


# =============================================================================
# CATEGORÍAS ADAPTADAS A URUGUAY
# =============================================================================

class PHICategoryUruguay(Enum):
    """
    Categorías PHI adaptadas al contexto uruguayo según Ley 18.331.

    Mapeo desde i2b2 a identificadores locales.
    """
    # === IDENTIFICADORES DIRECTOS ===

    # Nombres de personas
    NAME_PATIENT = "NAME_PATIENT"       # Nombre paciente
    NAME_DOCTOR = "NAME_DOCTOR"         # Nombre médico (Dr., Dra.)
    NAME_NURSE = "NAME_NURSE"           # Nombre enfermero (LE., AE.)
    NAME_FAMILY = "NAME_FAMILY"         # Nombre familiar
    NAME_OTHER = "NAME_OTHER"           # Otros nombres

    # Documentos de identidad Uruguay
    ID_CI = "ID_CI"                     # Cédula de Identidad (x.xxx.xxx-x)
    ID_PASSPORT = "ID_PASSPORT"         # Pasaporte
    ID_MEDICAL_RECORD = "ID_MEDICAL_RECORD"  # Historia clínica
    ID_CARNE_SALUD = "ID_CARNE_SALUD"   # Carné de salud

    # Contacto
    CONTACT_PHONE_MOBILE = "CONTACT_PHONE_MOBILE"  # Celular (09x-xxx-xxx)
    CONTACT_PHONE_FIXED = "CONTACT_PHONE_FIXED"    # Fijo (xxxx-xxxx)
    CONTACT_EMAIL = "CONTACT_EMAIL"                 # Email
    CONTACT_FAX = "CONTACT_FAX"                     # Fax

    # === CUASI-IDENTIFICADORES ===

    # Ubicación Uruguay
    LOCATION_STREET = "LOCATION_STREET"         # Calle y número
    LOCATION_CITY = "LOCATION_CITY"             # Ciudad
    LOCATION_DEPARTMENT = "LOCATION_DEPARTMENT"  # Departamento (19)
    LOCATION_BARRIO = "LOCATION_BARRIO"         # Barrio
    LOCATION_HOSPITAL = "LOCATION_HOSPITAL"     # Hospital/Sanatorio
    LOCATION_MUTUALISTA = "LOCATION_MUTUALISTA" # Mutualista
    LOCATION_ORGANIZATION = "LOCATION_ORGANIZATION"  # Organización

    # Temporal
    DATE_ADMISSION = "DATE_ADMISSION"    # Fecha de ingreso
    DATE_DISCHARGE = "DATE_DISCHARGE"    # Fecha de alta
    DATE_BIRTH = "DATE_BIRTH"            # Fecha de nacimiento
    DATE_PROCEDURE = "DATE_PROCEDURE"    # Fecha de procedimiento
    DATE_DEATH = "DATE_DEATH"            # Fecha de fallecimiento

    # Otros
    AGE = "AGE"                          # Edad
    PROFESSION = "PROFESSION"            # Profesión


# =============================================================================
# PLACEHOLDERS DE REEMPLAZO
# =============================================================================

PLACEHOLDERS = {
    # Nombres
    "NAME_PATIENT": "[NOMBRE]",
    "NAME_DOCTOR": "[NOMBRE]",
    "NAME_NURSE": "[NOMBRE]",
    "NAME_FAMILY": "[NOMBRE]",
    "NAME_OTHER": "[NOMBRE]",
    "PATIENT": "[NOMBRE]",
    "DOCTOR": "[NOMBRE]",

    # IDs
    "ID_CI": "[CI]",
    "ID_PASSPORT": "[ID]",
    "ID_MEDICAL_RECORD": "[REGISTRO]",
    "ID_CARNE_SALUD": "[ID]",
    "MEDICALRECORD": "[REGISTRO]",
    "IDNUM": "[ID]",

    # Contacto
    "CONTACT_PHONE_MOBILE": "[TELEFONO]",
    "CONTACT_PHONE_FIXED": "[TELEFONO]",
    "CONTACT_EMAIL": "[EMAIL]",
    "CONTACT_FAX": "[FAX]",
    "PHONE": "[TELEFONO]",
    "EMAIL": "[EMAIL]",

    # Ubicación
    "LOCATION_STREET": "[DIRECCION]",
    "LOCATION_CITY": "[UBICACION]",
    "LOCATION_DEPARTMENT": "[UBICACION]",
    "LOCATION_BARRIO": "[UBICACION]",
    "LOCATION_HOSPITAL": "[UBICACION]",
    "LOCATION_MUTUALISTA": "[UBICACION]",
    "LOCATION_ORGANIZATION": "[UBICACION]",
    "STREET": "[DIRECCION]",
    "CITY": "[UBICACION]",
    "HOSPITAL": "[UBICACION]",
    "ORGANIZATION": "[UBICACION]",

    # Temporal
    "DATE_ADMISSION": "[FECHA]",
    "DATE_DISCHARGE": "[FECHA]",
    "DATE_BIRTH": "[FECHA]",
    "DATE_PROCEDURE": "[FECHA]",
    "DATE_DEATH": "[FECHA]",
    "DATE": "[FECHA]",

    # Otros
    "AGE": "[EDAD]",
    "PROFESSION": "[PROFESION]",
}


# =============================================================================
# CLASIFICACIÓN DIRECTO vs CUASI-IDENTIFICADOR
# =============================================================================

DIRECT_IDENTIFIERS = {
    # Nombres
    "NAME_PATIENT", "NAME_DOCTOR", "NAME_NURSE", "NAME_FAMILY", "NAME_OTHER",
    "PATIENT", "DOCTOR", "USERNAME",

    # IDs
    "ID_CI", "ID_PASSPORT", "ID_MEDICAL_RECORD", "ID_CARNE_SALUD",
    "MEDICALRECORD", "IDNUM", "DEVICE", "BIOID",

    # Contacto directo
    "CONTACT_PHONE_MOBILE", "CONTACT_PHONE_FIXED", "CONTACT_EMAIL", "CONTACT_FAX",
    "PHONE", "FAX", "EMAIL", "URL", "IPADDR",
}

QUASI_IDENTIFIERS = {
    # Ubicación
    "LOCATION_STREET", "LOCATION_CITY", "LOCATION_DEPARTMENT", "LOCATION_BARRIO",
    "LOCATION_HOSPITAL", "LOCATION_MUTUALISTA", "LOCATION_ORGANIZATION",
    "STREET", "CITY", "STATE", "COUNTRY", "ZIP", "LOCATION", "HOSPITAL", "ORGANIZATION",

    # Temporal
    "DATE_ADMISSION", "DATE_DISCHARGE", "DATE_BIRTH", "DATE_PROCEDURE", "DATE_DEATH",
    "DATE", "AGE",

    # Otros
    "PROFESSION",
}


# =============================================================================
# DATACLASSES PARA ENTIDADES
# =============================================================================

@dataclass
class PHIEntity:
    """Representa una entidad PHI detectada o anotada."""
    category: str           # Categoría PHI
    value: str              # Valor original
    start_pos: int          # Posición inicial en texto
    end_pos: int            # Posición final en texto
    context: str            # Contexto/descripción
    is_direct: bool         # True si es identificador directo
    placeholder: str = ""   # Placeholder de reemplazo

    def __post_init__(self):
        if not self.placeholder:
            self.placeholder = PLACEHOLDERS.get(self.category, "[PHI]")
        if self.category in DIRECT_IDENTIFIERS:
            self.is_direct = True
        elif self.category in QUASI_IDENTIFIERS:
            self.is_direct = False


@dataclass
class PHIGroundTruth:
    """Ground truth de un caso clínico con todas sus entidades."""
    case_id: str
    text: str
    entities: List[PHIEntity]

    @property
    def direct_entities(self) -> List[PHIEntity]:
        """Retorna solo identificadores directos."""
        return [e for e in self.entities if e.is_direct]

    @property
    def quasi_entities(self) -> List[PHIEntity]:
        """Retorna solo cuasi-identificadores."""
        return [e for e in self.entities if not e.is_direct]

    @property
    def total_count(self) -> int:
        return len(self.entities)

    @property
    def direct_count(self) -> int:
        return len(self.direct_entities)

    @property
    def quasi_count(self) -> int:
        return len(self.quasi_entities)


# =============================================================================
# PATRONES REGEX PARA URUGUAY
# =============================================================================

PATTERNS_URUGUAY = {
    # Cédula de Identidad: x.xxx.xxx-x
    "CI": r"\b\d{1,2}\.\d{3}\.\d{3}-\d\b",

    # Teléfono móvil: 09x-xxx-xxx o 09x xxx xxx
    "PHONE_MOBILE": r"\b09\d[\s-]?\d{3}[\s-]?\d{3}\b",

    # Teléfono fijo: xxxx-xxxx (4 dígitos guión 4 dígitos)
    "PHONE_FIXED": r"\b\d{4}[\s-]\d{4}\b",

    # Teléfono con característica: 2xxx-xxxx (Montevideo)
    "PHONE_MVD": r"\b2\d{3}[\s-]?\d{4}\b",

    # Teléfono interior: 4xx-xxxxx
    "PHONE_INTERIOR": r"\b4\d{2}[\s-]?\d{5}\b",

    # Email
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",

    # Fecha DD/MM/YYYY o DD-MM-YYYY
    "DATE": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",

    # Historia clínica: HC-YYYY-XXXXX o similar
    "HC": r"\b[A-Z]{2,4}[-]?\d{4}[-]?\d{3,6}\b",
}


# =============================================================================
# DEPARTAMENTOS DE URUGUAY
# =============================================================================

DEPARTAMENTOS_URUGUAY = [
    "Artigas", "Canelones", "Cerro Largo", "Colonia", "Durazno",
    "Flores", "Florida", "Lavalleja", "Maldonado", "Montevideo",
    "Paysandú", "Río Negro", "Rivera", "Rocha", "Salto",
    "San José", "Soriano", "Tacuarembó", "Treinta y Tres"
]

# Ciudades principales
CIUDADES_URUGUAY = [
    "Montevideo", "Salto", "Paysandú", "Las Piedras", "Rivera",
    "Maldonado", "Tacuarembó", "Melo", "Mercedes", "Artigas",
    "Minas", "San José de Mayo", "Durazno", "Florida", "Treinta y Tres",
    "Rocha", "Fray Bentos", "Trinidad", "Colonia del Sacramento",
    "Punta del Este", "Ciudad de la Costa"
]

# Mutualistas e instituciones de salud
INSTITUCIONES_SALUD_URUGUAY = [
    # Mutualistas
    "CASMU", "Médica Uruguaya", "Asociación Española",
    "Hospital Británico", "SMI", "COSEM", "Casa de Galicia",
    "Círculo Católico", "MUCAM", "COMTA", "CAMOC",

    # ASSE
    "ASSE", "Hospital de Clínicas", "Hospital Maciel", "Hospital Pasteur",
    "Hospital Pereira Rossell", "Hospital Vilardebó", "Hospital Español",
    "Centro Hospitalario del Norte", "Hospital de Rivera",

    # Privados
    "Sanatorio Americano", "Hospital Evangélico", "Sanatorio Cantegril",
    "Clínica Psiquiátrica del Sur", "Sanatorio CASMU", "MP"
]


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def is_direct_identifier(category: str) -> bool:
    """Verifica si una categoría es identificador directo."""
    return category in DIRECT_IDENTIFIERS


def is_quasi_identifier(category: str) -> bool:
    """Verifica si una categoría es cuasi-identificador."""
    return category in QUASI_IDENTIFIERS


def get_placeholder(category: str) -> str:
    """Obtiene el placeholder para una categoría."""
    return PLACEHOLDERS.get(category, "[PHI]")


def get_all_categories() -> List[str]:
    """Retorna todas las categorías PHI."""
    return list(PLACEHOLDERS.keys())


def get_direct_categories() -> List[str]:
    """Retorna categorías de identificadores directos."""
    return list(DIRECT_IDENTIFIERS)


def get_quasi_categories() -> List[str]:
    """Retorna categorías de cuasi-identificadores."""
    return list(QUASI_IDENTIFIERS)


def print_category_summary():
    """Imprime resumen de categorías PHI."""
    print("\n" + "=" * 70)
    print("  CATEGORÍAS PHI - Basado en i2b2 2014 + Ley 18.331 Uruguay")
    print("=" * 70)

    print("\n  IDENTIFICADORES DIRECTOS (LRDI - todo o nada):")
    print("  " + "-" * 66)
    for cat in sorted(DIRECT_IDENTIFIERS):
        placeholder = PLACEHOLDERS.get(cat, "[PHI]")
        print(f"    {cat:<35} -> {placeholder}")

    print("\n  CUASI-IDENTIFICADORES (LRQI - proporcional):")
    print("  " + "-" * 66)
    for cat in sorted(QUASI_IDENTIFIERS):
        placeholder = PLACEHOLDERS.get(cat, "[PHI]")
        print(f"    {cat:<35} -> {placeholder}")

    print("\n" + "=" * 70)
    print(f"  Total: {len(DIRECT_IDENTIFIERS)} directos + {len(QUASI_IDENTIFIERS)} cuasi = "
          f"{len(DIRECT_IDENTIFIERS) + len(QUASI_IDENTIFIERS)} categorías")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print_category_summary()

    print("\n  PATRONES REGEX PARA URUGUAY:")
    print("  " + "-" * 50)
    for name, pattern in PATTERNS_URUGUAY.items():
        print(f"    {name:<15}: {pattern}")

    print("\n  DEPARTAMENTOS DE URUGUAY:")
    print("  " + "-" * 50)
    print(f"    {', '.join(DEPARTAMENTOS_URUGUAY[:10])}...")

    print("\n  INSTITUCIONES DE SALUD:")
    print("  " + "-" * 50)
    print(f"    {', '.join(INSTITUCIONES_SALUD_URUGUAY[:10])}...")
