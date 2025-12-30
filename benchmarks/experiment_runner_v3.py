#!/usr/bin/env python3
"""
experiment_runner_v3.py - Protocolo de Experimentación v3.0
Universidad de Montevideo - Tesis 2025

Framework de benchmark basado en papers académicos:
- arXiv:2412.10918 (LLMs-in-the-Loop Part 2)
- arXiv:2406.00062 (Unlocking LLMs for Clinical Text Anonymization)

Ejecuta 3 experimentos:
1. Benchmark de Rendimiento MMA
2. Comparativa de Prompts
3. Evaluación de Calidad con métricas académicas
"""

import urllib.request
import json
import time
import statistics
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8080
DEFAULT_TIMEOUT = 180
N_PREDICT = 500

# =============================================================================
# 8 ESTRATEGIAS DE PROMPTING (Protocolo v3.0)
# =============================================================================

PROMPT_STRATEGIES = {
    "baseline": {
        "nombre": "Zero-Shot Simple",
        "descripcion": "Instrucción mínima",
        "template": """Anonimiza el siguiente texto clínico reemplazando datos personales por placeholders.
Usa: [NOMBRE], [CI], [DIRECCION], [UBICACION], [TELEFONO], [FECHA], [EMAIL], [REGISTRO].
Solo devuelve el texto anonimizado:

{text}"""
    },

    "detailed": {
        "nombre": "Zero-Shot Detallado",
        "descripcion": "8 reglas + categorías PHI",
        "template": """Eres un asistente especializado en anonimización de datos clínicos.

REGLAS DE ANONIMIZACIÓN:
1. Nombres de personas (pacientes, médicos, enfermeros, familiares) → [NOMBRE]
2. Cédulas de identidad (formato x.xxx.xxx-x) → [CI]
3. Direcciones (calles, avenidas, números) → [DIRECCION]
4. Ciudades, departamentos, hospitales → [UBICACION]
5. Teléfonos (fijos y móviles) → [TELEFONO]
6. Fechas (admisión, alta, procedimientos, nacimiento) → [FECHA]
7. Emails → [EMAIL]
8. Números de historia clínica, registros médicos → [REGISTRO]

IMPORTANTE:
- Conserva diagnósticos, tratamientos, valores de laboratorio y terminología médica.
- No modifiques la estructura del documento.
- Solo reemplaza datos personales identificables (PHI).

Anonimiza el siguiente texto y devuelve SOLO el texto anonimizado:

{text}"""
    },

    "few_shot": {
        "nombre": "Few-Shot (3 ejemplos)",
        "descripcion": "Ejemplos input/output",
        "template": """Ejemplos de anonimización de textos clínicos:

EJEMPLO 1:
Input: "El paciente Juan Pérez, CI 1.234.567-8, ingresó el 15/03/2024 al Hospital Maciel."
Output: "El paciente [NOMBRE], CI [CI], ingresó el [FECHA] al [UBICACION]."

EJEMPLO 2:
Input: "Dra. María García atendió la consulta. Tel de contacto: 099-123-456."
Output: "Dra. [NOMBRE] atendió la consulta. Tel de contacto: [TELEFONO]."

EJEMPLO 3:
Input: "Domicilio: Av. Italia 2345, Montevideo. Email: jpérez@gmail.com"
Output: "Domicilio: [DIRECCION], [UBICACION]. Email: [EMAIL]"

Ahora anonimiza el siguiente texto clínico:

{text}"""
    },

    "chain_of_thought": {
        "nombre": "Chain of Thought",
        "descripcion": "Razonamiento paso a paso",
        "template": """Analiza el siguiente texto clínico paso a paso para identificar y anonimizar datos personales.

PASOS:
1. Identificar todos los nombres de personas
2. Identificar números de documento (CI)
3. Identificar direcciones y ubicaciones
4. Identificar teléfonos y emails
5. Identificar fechas
6. Reemplazar cada elemento identificado por su placeholder correspondiente

Placeholders: [NOMBRE], [CI], [DIRECCION], [UBICACION], [TELEFONO], [EMAIL], [FECHA], [REGISTRO]

Texto a anonimizar:
{text}

Primero identifica los elementos PHI, luego devuelve el texto anonimizado completo."""
    },

    "master_tutor": {
        "nombre": "Master Tutor",
        "descripcion": "Protocolo experto",
        "template": """Actúa como un experto en privacidad de datos de salud.

Tu tarea es anonimizar texto clínico reemplazando toda información personal identificable (PHI) por placeholders estandarizados.

Categorías PHI a detectar:
- Identificadores directos: nombres, CI, teléfonos, emails
- Cuasi-identificadores: direcciones, fechas, instituciones

Devuelve ÚNICAMENTE el texto anonimizado sin explicaciones adicionales.

{text}"""
    },

    "medico": {
        "nombre": "Médico Especializado",
        "descripcion": "Enfoque Ley 18.331 Uruguay",
        "template": """Como oficial de cumplimiento de la Ley 18.331 de Protección de Datos Personales de Uruguay, debes anonimizar el siguiente registro clínico.

REQUISITOS LEGALES:
- Eliminar TODO dato que permita identificar directa o indirectamente al paciente
- Preservar la utilidad clínica del documento
- Cumplir con estándares de habeas data

DATOS A ANONIMIZAR:
- Nombres completos → [NOMBRE]
- Cédula de identidad uruguaya → [CI]
- Direcciones y domicilios → [DIRECCION]
- Instituciones de salud (hospitales, mutualistas) → [UBICACION]
- Teléfonos (099, 094, 2xxx) → [TELEFONO]
- Correos electrónicos → [EMAIL]
- Fechas específicas → [FECHA]
- Números de historia clínica → [REGISTRO]

Texto clínico:
{text}

Devuelve el texto anonimizado:"""
    },

    "structured_output": {
        "nombre": "Structured Output",
        "descripcion": "Categorías PHI explícitas",
        "template": """Anonimiza el texto clínico usando EXACTAMENTE estos placeholders según la categoría:

| Categoría | Placeholder |
|-----------|-------------|
| Nombre paciente | [NOMBRE] |
| Nombre médico | [NOMBRE] |
| Nombre enfermero | [NOMBRE] |
| Nombre familiar | [NOMBRE] |
| Cédula identidad | [CI] |
| Historia clínica | [REGISTRO] |
| Teléfono | [TELEFONO] |
| Email | [EMAIL] |
| Dirección/calle | [DIRECCION] |
| Ciudad | [UBICACION] |
| Hospital/sanatorio | [UBICACION] |
| Fecha | [FECHA] |

TEXTO A ANONIMIZAR:
{text}

TEXTO ANONIMIZADO:"""
    },

    "hybrid": {
        "nombre": "Hybrid (Few-Shot + CoT)",
        "descripcion": "Combina ejemplos + razonamiento",
        "template": """Tarea: Anonimizar texto clínico identificando y reemplazando datos PHI.

EJEMPLO DE PROCESO:
Texto: "Juan Pérez (CI 1.234.567-8) vive en Av. Italia 123, Montevideo."
Análisis:
- "Juan Pérez" → nombre de persona → [NOMBRE]
- "1.234.567-8" → cédula uruguaya → [CI]
- "Av. Italia 123" → dirección → [DIRECCION]
- "Montevideo" → ciudad → [UBICACION]
Resultado: "[NOMBRE] (CI [CI]) vive en [DIRECCION], [UBICACION]."

EJEMPLO 2:
Texto: "Dra. García (tel 099-111-222) atendió el 15/03/2024 en Hospital Maciel."
Análisis:
- "García" → nombre médico → [NOMBRE]
- "099-111-222" → teléfono móvil → [TELEFONO]
- "15/03/2024" → fecha → [FECHA]
- "Hospital Maciel" → institución → [UBICACION]
Resultado: "Dra. [NOMBRE] (tel [TELEFONO]) atendió el [FECHA] en [UBICACION]."

Ahora aplica el mismo proceso al siguiente texto:

{text}

Devuelve SOLO el texto anonimizado final:"""
    }
}

# =============================================================================
# CATEGORÍAS PHI (i2b2 2014 adaptado a Uruguay)
# =============================================================================

DIRECT_IDENTIFIERS = {
    "NAME_PATIENT", "NAME_DOCTOR", "NAME_NURSE", "NAME_FAMILY",
    "ID_CI", "ID_MEDICAL_RECORD",
    "CONTACT_PHONE", "CONTACT_EMAIL"
}

QUASI_IDENTIFIERS = {
    "LOCATION_STREET", "LOCATION_CITY", "LOCATION_DEPARTMENT",
    "LOCATION_HOSPITAL", "LOCATION_ORGANIZATION",
    "DATE_ADMISSION", "DATE_DISCHARGE", "DATE_BIRTH", "DATE_PROCEDURE",
    "PROFESSION", "AGE"
}

PLACEHOLDERS = {
    "NAME_PATIENT": "[NOMBRE]",
    "NAME_DOCTOR": "[NOMBRE]",
    "NAME_NURSE": "[NOMBRE]",
    "NAME_FAMILY": "[NOMBRE]",
    "ID_CI": "[CI]",
    "ID_MEDICAL_RECORD": "[REGISTRO]",
    "CONTACT_PHONE": "[TELEFONO]",
    "CONTACT_EMAIL": "[EMAIL]",
    "LOCATION_STREET": "[DIRECCION]",
    "LOCATION_CITY": "[UBICACION]",
    "LOCATION_DEPARTMENT": "[UBICACION]",
    "LOCATION_HOSPITAL": "[UBICACION]",
    "LOCATION_ORGANIZATION": "[UBICACION]",
    "DATE_ADMISSION": "[FECHA]",
    "DATE_DISCHARGE": "[FECHA]",
    "DATE_BIRTH": "[FECHA]",
    "DATE_PROCEDURE": "[FECHA]",
    "PROFESSION": "[PROFESION]",
    "AGE": "[EDAD]"
}

# =============================================================================
# CASOS CLÍNICOS SINTÉTICOS (10 casos del protocolo)
# =============================================================================

CASOS_CLINICOS = {
    "A1": {
        "id": "A1",
        "nombre": "Emergencia Cardiología",
        "texto": """HOSPITAL DE CLÍNICAS - SERVICIO DE EMERGENCIA
Fecha de ingreso: 15/11/2024 - Hora: 03:47

DATOS DEL PACIENTE:
Nombre: Roberto Carlos Méndez Aguilar
Documento: 3.847.291-6
Edad: 58 años
Domicilio: Bulevar Artigas 2847, apto 302
Ciudad: Montevideo
Teléfono: 099 847 231
Historia Clínica N°: HC-2024-48721

MOTIVO DE CONSULTA:
Dolor precordial opresivo de 2 horas de evolución.

CONDUCTA:
1. AAS 300mg VO
2. Contacto con Hemodinamia - Dra. María Fernanda Sosa

Responsable: Dr. Alejandro Martínez Vidal
CI 1.892.445-3""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Roberto Carlos Méndez Aguilar", "is_direct": True},
            {"category": "ID_CI", "value": "3.847.291-6", "is_direct": True},
            {"category": "LOCATION_STREET", "value": "Bulevar Artigas 2847, apto 302", "is_direct": False},
            {"category": "LOCATION_CITY", "value": "Montevideo", "is_direct": False},
            {"category": "CONTACT_PHONE", "value": "099 847 231", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "HC-2024-48721", "is_direct": True},
            {"category": "DATE_ADMISSION", "value": "15/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL DE CLÍNICAS", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "María Fernanda Sosa", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Alejandro Martínez Vidal", "is_direct": True},
            {"category": "ID_CI", "value": "1.892.445-3", "is_direct": True},
        ]
    },

    "A2": {
        "id": "A2",
        "nombre": "Consulta Oncología",
        "texto": """ASOCIACIÓN ESPAÑOLA - SERVICIO DE ONCOLOGÍA
Fecha: 20/10/2024

PACIENTE: Ana María Rodríguez Ferreira
CI: 2.156.873-4
Procedencia: Salto
Domicilio: Calle Uruguay 456
Teléfono: 473-25890
HC: ON-2024-1234

DIAGNÓSTICO: Carcinoma Ductal Infiltrante mama izquierda.

FAMILIAR: Juan Carlos Rodríguez (esposo)
Cel: 099-888-777

Médico: Dra. Valentina Gutiérrez Oreggioni""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Ana María Rodríguez Ferreira", "is_direct": True},
            {"category": "ID_CI", "value": "2.156.873-4", "is_direct": True},
            {"category": "LOCATION_CITY", "value": "Salto", "is_direct": False},
            {"category": "LOCATION_STREET", "value": "Calle Uruguay 456", "is_direct": False},
            {"category": "CONTACT_PHONE", "value": "473-25890", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "ON-2024-1234", "is_direct": True},
            {"category": "DATE_PROCEDURE", "value": "20/10/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "ASOCIACIÓN ESPAÑOLA", "is_direct": False},
            {"category": "NAME_FAMILY", "value": "Juan Carlos Rodríguez", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "099-888-777", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Valentina Gutiérrez Oreggioni", "is_direct": True},
        ]
    },

    "A3": {
        "id": "A3",
        "nombre": "Evolución CTI",
        "texto": """CTI - HOSPITAL MACIEL
Fecha: 22/11/2024

PACIENTE: Fernando José Acosta Píriz
CI: 1.987.654-2
HC: 2024-CTI-789

DIAGNÓSTICOS:
1. Neumonía grave
2. SDRA moderado

Interconsulta con Dr. Martín Fernández (Neumología).
Familiar: Carmen Díaz (esposa), tel 094-567-890.

Responsable: Dra. Lucía Gómez Pereira
Enfermería: LE. Patricia Núñez
Domicilio: Av. 8 de Octubre 3456, Montevideo""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Fernando José Acosta Píriz", "is_direct": True},
            {"category": "ID_CI", "value": "1.987.654-2", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "2024-CTI-789", "is_direct": True},
            {"category": "DATE_PROCEDURE", "value": "22/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL MACIEL", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "Martín Fernández", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Carmen Díaz", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "094-567-890", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Lucía Gómez Pereira", "is_direct": True},
            {"category": "NAME_NURSE", "value": "Patricia Núñez", "is_direct": True},
            {"category": "LOCATION_STREET", "value": "Av. 8 de Octubre 3456", "is_direct": False},
            {"category": "LOCATION_CITY", "value": "Montevideo", "is_direct": False},
        ]
    },

    "A4": {
        "id": "A4",
        "nombre": "Alta Cirugía",
        "texto": """SANATORIO AMERICANO - CIRUGÍA GENERAL
EPICRISIS

Paciente: María Elena Suárez Bentancor
CI: 4.321.098-7
Domicilio: Rbla. Rep. Argentina 1234
Ciudad: Punta del Este
Departamento: Maldonado
Tel: 042-445566
Email: mesuarez@gmail.com
HC: CG-2024-5678

FECHA INGRESO: 18/11/2024
FECHA ALTA: 24/11/2024

PROCEDIMIENTO (19/11/2024): Colecistectomía laparoscópica.
Cirujano: Dr. Carlos Pérez Aguirre

FAMILIAR: Laura Fernández Suárez (hija)
Tel: 099-123-456""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "María Elena Suárez Bentancor", "is_direct": True},
            {"category": "ID_CI", "value": "4.321.098-7", "is_direct": True},
            {"category": "LOCATION_STREET", "value": "Rbla. Rep. Argentina 1234", "is_direct": False},
            {"category": "LOCATION_CITY", "value": "Punta del Este", "is_direct": False},
            {"category": "LOCATION_DEPARTMENT", "value": "Maldonado", "is_direct": False},
            {"category": "CONTACT_PHONE", "value": "042-445566", "is_direct": True},
            {"category": "CONTACT_EMAIL", "value": "mesuarez@gmail.com", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "CG-2024-5678", "is_direct": True},
            {"category": "DATE_ADMISSION", "value": "18/11/2024", "is_direct": False},
            {"category": "DATE_DISCHARGE", "value": "24/11/2024", "is_direct": False},
            {"category": "DATE_PROCEDURE", "value": "19/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "SANATORIO AMERICANO", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "Carlos Pérez Aguirre", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Laura Fernández Suárez", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "099-123-456", "is_direct": True},
        ]
    },

    "A5": {
        "id": "A5",
        "nombre": "Interconsulta Neurología",
        "texto": """MÉDICA URUGUAYA - NEUROLOGÍA
Fecha: 25/11/2024
Solicitante: Dra. Carolina Méndez

PACIENTE: Jorge Luis Fernández Castro
CI: 3.654.987-1
Procedencia: Flores
HC: MU-2024-9876

MOTIVO: Cuadro confusional de 48hs.

ANTECEDENTES: HTA, FA crónica, ACV en 2019.

Dr. Mauricio Rodríguez Brum
Neurólogo
Email: mrodriguez@medicauruguaya.com.uy""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Jorge Luis Fernández Castro", "is_direct": True},
            {"category": "ID_CI", "value": "3.654.987-1", "is_direct": True},
            {"category": "LOCATION_CITY", "value": "Flores", "is_direct": False},
            {"category": "ID_MEDICAL_RECORD", "value": "MU-2024-9876", "is_direct": True},
            {"category": "DATE_PROCEDURE", "value": "25/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "MÉDICA URUGUAYA", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "Carolina Méndez", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Mauricio Rodríguez Brum", "is_direct": True},
            {"category": "CONTACT_EMAIL", "value": "mrodriguez@medicauruguaya.com.uy", "is_direct": True},
        ]
    },

    "B1": {
        "id": "B1",
        "nombre": "Epicrisis Medicina Interna",
        "texto": """HOSPITAL PASTEUR - MEDICINA INTERNA
EPICRISIS

Paciente: Ricardo Daniel Olivera Techera
CI: 2.789.456-3
Fecha nacimiento: 15/03/1955
Domicilio: Camino Maldonado 5678
Ciudad: Montevideo
Teléfonos: 2601-5678, Cel 091-234-567
HC: HP-2024-12345

Ingreso: 10/11/2024 | Alta: 28/11/2024

DIAGNÓSTICOS:
1. IC descompensada
2. DM2
3. ERC 3b

Cardiólogo: Dr. Fernando González
Nefróloga: Dra. Mónica Pérez

FAMILIAR: Marta Lucía Rodríguez (esposa)
Tel: 099-876-543

Médico: Dr. Pablo Martín Sánchez Aguiar""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Ricardo Daniel Olivera Techera", "is_direct": True},
            {"category": "ID_CI", "value": "2.789.456-3", "is_direct": True},
            {"category": "DATE_BIRTH", "value": "15/03/1955", "is_direct": False},
            {"category": "LOCATION_STREET", "value": "Camino Maldonado 5678", "is_direct": False},
            {"category": "LOCATION_CITY", "value": "Montevideo", "is_direct": False},
            {"category": "CONTACT_PHONE", "value": "2601-5678", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "091-234-567", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "HP-2024-12345", "is_direct": True},
            {"category": "DATE_ADMISSION", "value": "10/11/2024", "is_direct": False},
            {"category": "DATE_DISCHARGE", "value": "28/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL PASTEUR", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "Fernando González", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Mónica Pérez", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Marta Lucía Rodríguez", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "099-876-543", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Pablo Martín Sánchez Aguiar", "is_direct": True},
        ]
    },

    "B2": {
        "id": "B2",
        "nombre": "Resumen Pediatría",
        "texto": """HOSPITAL PEREIRA ROSSELL - PEDIATRÍA

Paciente: Sofía Valentina Hernández Correa
CI: 5.987.321-0
Fecha nacimiento: 12/08/2020
Domicilio: Av. Italia 3456, Buceo
Tel madre: 099-555-333
HC: PR-2024-7890

MADRE: Lorena Correa Martínez, CI 3.456.123-8

Ingreso: 20/11/2024 | Alta: 23/11/2024

DIAGNÓSTICO: Bronquiolitis por VRS

Pediatra: Dra. María José López
Médico: Dr. Andrés Fernández Olivera""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Sofía Valentina Hernández Correa", "is_direct": True},
            {"category": "ID_CI", "value": "5.987.321-0", "is_direct": True},
            {"category": "DATE_BIRTH", "value": "12/08/2020", "is_direct": False},
            {"category": "LOCATION_STREET", "value": "Av. Italia 3456, Buceo", "is_direct": False},
            {"category": "CONTACT_PHONE", "value": "099-555-333", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "PR-2024-7890", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Lorena Correa Martínez", "is_direct": True},
            {"category": "ID_CI", "value": "3.456.123-8", "is_direct": True},
            {"category": "DATE_ADMISSION", "value": "20/11/2024", "is_direct": False},
            {"category": "DATE_DISCHARGE", "value": "23/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL PEREIRA ROSSELL", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "María José López", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Andrés Fernández Olivera", "is_direct": True},
        ]
    },

    "B3": {
        "id": "B3",
        "nombre": "Nota Operatoria Traumatología",
        "texto": """HOSPITAL DE CLÍNICAS - TRAUMATOLOGÍA
PROTOCOLO OPERATORIO
Fecha: 26/11/2024

Paciente: Miguel Ángel Rodríguez Techera
CI: 1.234.567-8
Domicilio: Calle Durazno 1234, Ciudad Vieja
Tel: 2916-7890
Email: marodriguez@hotmail.com
HC: TRAU-2024-4567

PROCEDIMIENTO: Osteosíntesis fémur izquierdo

EQUIPO:
- Dr. Martín González Etchegoyen (cirujano)
- Dr. Federico Álvarez Pérez (ayudante)
- Dra. Gabriela Suárez Núñez (anestesióloga)
- LE. Marcela Fernández (instrumentista)

FAMILIAR: Claudia Martínez (esposa), tel 099-777-888""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Miguel Ángel Rodríguez Techera", "is_direct": True},
            {"category": "ID_CI", "value": "1.234.567-8", "is_direct": True},
            {"category": "LOCATION_STREET", "value": "Calle Durazno 1234, Ciudad Vieja", "is_direct": False},
            {"category": "CONTACT_PHONE", "value": "2916-7890", "is_direct": True},
            {"category": "CONTACT_EMAIL", "value": "marodriguez@hotmail.com", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "TRAU-2024-4567", "is_direct": True},
            {"category": "DATE_PROCEDURE", "value": "26/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL DE CLÍNICAS", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "Martín González Etchegoyen", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Federico Álvarez Pérez", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Gabriela Suárez Núñez", "is_direct": True},
            {"category": "NAME_NURSE", "value": "Marcela Fernández", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Claudia Martínez", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "099-777-888", "is_direct": True},
        ]
    },

    "C1": {
        "id": "C1",
        "nombre": "Historia Psiquiatría",
        "texto": """HOSPITAL VILARDEBÓ - PSIQUIATRÍA

Paciente: Eduardo Sebastián Pérez Rodríguez
CI: 3.876.543-2
Fecha nacimiento: 05/07/1985
Ocupación: Contador
Domicilio: Av. Rivera 4567, Pocitos, Montevideo
Tel: 2709-8765
Cel: 094-321-654
Email: espearez@gmail.com
HC: PSI-2024-3456

MADRE: Rosa María Rodríguez de Pérez
CI madre: 1.234.098-7
Tel: 099-654-321
Domicilio madre: Calle Soriano 789, Centro

Fecha ingreso: 15/11/2024

Psiquiatra previo: Dr. Martín Fernández Brum
Psicóloga: Lic. Ana Laura Gómez

Médica actual: Dra. Victoria González Silveira""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "Eduardo Sebastián Pérez Rodríguez", "is_direct": True},
            {"category": "ID_CI", "value": "3.876.543-2", "is_direct": True},
            {"category": "DATE_BIRTH", "value": "05/07/1985", "is_direct": False},
            {"category": "PROFESSION", "value": "Contador", "is_direct": False},
            {"category": "LOCATION_STREET", "value": "Av. Rivera 4567, Pocitos", "is_direct": False},
            {"category": "LOCATION_CITY", "value": "Montevideo", "is_direct": False},
            {"category": "CONTACT_PHONE", "value": "2709-8765", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "094-321-654", "is_direct": True},
            {"category": "CONTACT_EMAIL", "value": "espearez@gmail.com", "is_direct": True},
            {"category": "ID_MEDICAL_RECORD", "value": "PSI-2024-3456", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Rosa María Rodríguez de Pérez", "is_direct": True},
            {"category": "ID_CI", "value": "1.234.098-7", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "099-654-321", "is_direct": True},
            {"category": "LOCATION_STREET", "value": "Calle Soriano 789, Centro", "is_direct": False},
            {"category": "DATE_ADMISSION", "value": "15/11/2024", "is_direct": False},
            {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL VILARDEBÓ", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "Martín Fernández Brum", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Ana Laura Gómez", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Victoria González Silveira", "is_direct": True},
        ]
    },

    "C2": {
        "id": "C2",
        "nombre": "Multi-Evolución CTI",
        "texto": """HOSPITAL MACIEL - CTI
EVOLUCIONES MÚLTIPLES

Paciente: OSCAR DANIEL MARTÍNEZ FERNÁNDEZ
CI: 2.345.678-9
Domicilio: Av. Gral. Flores 7890, La Teja, Montevideo
HC: CTI-2024-8901

--- EVOLUCIÓN 27/11/2024 ---
Dr. Santiago García Núñez
Dra. María Belén Fernández
LE. Carolina Suárez

Cirujano consultor: Dr. Rodríguez Pérez
Gastroenteróloga: Dra. Patricia López
Infectólogo: Dr. Mauricio Álvarez
Nefróloga: Dra. Valeria González

Esposa: Laura Martínez, tel 099-111-222
Hijo: Martín Martínez
Hermano: Jorge Martínez

--- EVOLUCIÓN 28/11/2024 ---
Enfermería: LE. Patricia Núñez Olivera
Médico certificador: Dr. Santiago García Núñez
CI médico: 2.567.890-1""",
        "entidades": [
            {"category": "NAME_PATIENT", "value": "OSCAR DANIEL MARTÍNEZ FERNÁNDEZ", "is_direct": True},
            {"category": "ID_CI", "value": "2.345.678-9", "is_direct": True},
            {"category": "LOCATION_STREET", "value": "Av. Gral. Flores 7890, La Teja", "is_direct": False},
            {"category": "LOCATION_CITY", "value": "Montevideo", "is_direct": False},
            {"category": "ID_MEDICAL_RECORD", "value": "CTI-2024-8901", "is_direct": True},
            {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL MACIEL", "is_direct": False},
            {"category": "DATE_PROCEDURE", "value": "27/11/2024", "is_direct": False},
            {"category": "DATE_PROCEDURE", "value": "28/11/2024", "is_direct": False},
            {"category": "NAME_DOCTOR", "value": "Santiago García Núñez", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "María Belén Fernández", "is_direct": True},
            {"category": "NAME_NURSE", "value": "Carolina Suárez", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Rodríguez Pérez", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Patricia López", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Mauricio Álvarez", "is_direct": True},
            {"category": "NAME_DOCTOR", "value": "Valeria González", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Laura Martínez", "is_direct": True},
            {"category": "CONTACT_PHONE", "value": "099-111-222", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Martín Martínez", "is_direct": True},
            {"category": "NAME_FAMILY", "value": "Jorge Martínez", "is_direct": True},
            {"category": "NAME_NURSE", "value": "Patricia Núñez Olivera", "is_direct": True},
            {"category": "ID_CI", "value": "2.567.890-1", "is_direct": True},
        ]
    }
}


# =============================================================================
# FUNCIONES DE MÉTRICAS
# =============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Distancia de Levenshtein entre dos strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Similitud de Levenshtein normalizada (0-1)."""
    if len(s1) == 0 and len(s2) == 0:
        return 1.0
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - (distance / max_len)


def calculate_alid(original: str, anonymized: str) -> float:
    """ALID - Average Levenshtein Index of Dissimilarity."""
    return 1 - levenshtein_similarity(original, anonymized)


def calculate_quality_metrics(anonymized_text: str, entities: List[Dict]) -> Dict:
    """
    Calcula métricas de calidad según papers académicos.

    Returns:
        Dict con precision, recall, f1, lrdi, lrqi, etc.
    """
    tp = 0  # True positives (entidad anonimizada)
    fn = 0  # False negatives (entidad escapada)
    direct_escaped = []
    quasi_escaped = []

    for entity in entities:
        value = entity.get("value", "")
        is_direct = entity.get("is_direct", False)
        category = entity.get("category", "")

        if value and value in anonymized_text:
            # Entidad NO fue anonimizada (escapó)
            fn += 1
            if is_direct:
                direct_escaped.append({"category": category, "value": value})
            else:
                quasi_escaped.append({"category": category, "value": value})
        else:
            # Entidad fue anonimizada correctamente
            tp += 1

    # Contar placeholders en texto anonimizado
    placeholder_pattern = r'\[([A-ZÁÉÍÓÚÑ_]+)\]'
    placeholders_found = len(re.findall(placeholder_pattern, anonymized_text))

    # Métricas estándar
    total = tp + fn
    precision = tp / placeholders_found if placeholders_found > 0 else 0
    recall = tp / total if total > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # LRDI: 100% solo si TODOS los identificadores directos fueron anonimizados
    direct_entities = [e for e in entities if e.get("is_direct", False)]
    lrdi = 100.0 if len(direct_escaped) == 0 else 0.0

    # LRQI: porcentaje de cuasi-identificadores anonimizados
    quasi_entities = [e for e in entities if not e.get("is_direct", False)]
    quasi_anonymized = len(quasi_entities) - len(quasi_escaped)
    lrqi = (quasi_anonymized / len(quasi_entities) * 100) if quasi_entities else 100.0

    return {
        "true_positives": tp,
        "false_negatives": fn,
        "total_entities": total,
        "placeholders_found": placeholders_found,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_micro": round(f1, 4),
        "lrdi": round(lrdi, 2),
        "lrqi": round(lrqi, 2),
        "direct_escaped": direct_escaped,
        "quasi_escaped": quasi_escaped
    }


# =============================================================================
# LLAMADA AL MODELO
# =============================================================================

def call_model(prompt: str, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
               timeout: int = DEFAULT_TIMEOUT) -> Dict:
    """Llama al servidor llama.cpp y retorna métricas."""
    payload = {
        "prompt": prompt,
        "n_predict": N_PREDICT,
        "temperature": 0.1,
        "top_k": 40,
        "top_p": 0.95,
        "stream": False
    }

    url = f"http://{host}:{port}/completion"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        total_time = time.time() - start_time

        tokens_gen = result.get("tokens_predicted", 0)
        tokens_prompt = result.get("tokens_evaluated", 0)
        time_gen_ms = result.get("timings", {}).get("predicted_ms", total_time * 1000)
        time_prompt_ms = result.get("timings", {}).get("prompt_ms", 0)

        tps_gen = tokens_gen / (time_gen_ms / 1000) if time_gen_ms > 0 else 0
        tps_prompt = tokens_prompt / (time_prompt_ms / 1000) if time_prompt_ms > 0 else 0

        return {
            "success": True,
            "text": result.get("content", ""),
            "tokens_generated": tokens_gen,
            "tokens_prompt": tokens_prompt,
            "time_generation_ms": time_gen_ms,
            "time_prompt_ms": time_prompt_ms,
            "tps_generation": round(tps_gen, 2),
            "tps_prompt": round(tps_prompt, 2),
            "total_time_s": round(total_time, 2)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "tokens_generated": 0,
            "tps_generation": 0
        }


# =============================================================================
# EXPERIMENTO 1: BENCHMARK DE RENDIMIENTO
# =============================================================================

def run_performance_benchmark(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                              iterations: int = 1, cases: List[str] = None) -> Dict:
    """
    Experimento 1: Benchmark de rendimiento MMA.

    Mide TPS, latencia y throughput para cada caso.
    """
    print("\n" + "=" * 70)
    print("  EXPERIMENTO 1: Benchmark de Rendimiento MMA")
    print("=" * 70)

    if cases is None:
        cases = list(CASOS_CLINICOS.keys())

    results = []
    all_tps = []

    # Usar prompt baseline para rendimiento puro
    prompt_template = PROMPT_STRATEGIES["baseline"]["template"]

    for iteration in range(1, iterations + 1):
        print(f"\n  --- Iteración {iteration}/{iterations} ---")

        for caso_id in cases:
            caso = CASOS_CLINICOS[caso_id]
            prompt = prompt_template.format(text=caso["texto"])

            print(f"    {caso_id} ({caso['nombre']}): ", end="", flush=True)

            result = call_model(prompt, host, port)

            if result["success"]:
                results.append({
                    "iteration": iteration,
                    "case_id": caso_id,
                    "case_name": caso["nombre"],
                    "tps_generation": result["tps_generation"],
                    "tps_prompt": result["tps_prompt"],
                    "tokens_generated": result["tokens_generated"],
                    "total_time_s": result["total_time_s"]
                })
                all_tps.append(result["tps_generation"])
                print(f"TPS: {result['tps_generation']:.2f}")
            else:
                print(f"ERROR: {result['error']}")

    # Calcular estadísticas
    summary = {}
    if all_tps:
        summary = {
            "tps_mean": round(statistics.mean(all_tps), 2),
            "tps_std": round(statistics.stdev(all_tps), 2) if len(all_tps) > 1 else 0,
            "tps_min": round(min(all_tps), 2),
            "tps_max": round(max(all_tps), 2),
            "total_tests": len(results)
        }

        print("\n  RESUMEN:")
        print(f"    TPS promedio: {summary['tps_mean']}")
        print(f"    TPS std: {summary['tps_std']}")
        print(f"    TPS min/max: {summary['tps_min']} / {summary['tps_max']}")

    return {
        "experiment": "performance_benchmark",
        "results": results,
        "summary": summary
    }


# =============================================================================
# EXPERIMENTO 2: COMPARATIVA DE PROMPTS
# =============================================================================

def run_prompt_comparison(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                          cases: List[str] = None) -> Dict:
    """
    Experimento 2: Comparativa de 8 estrategias de prompting.

    Evalúa calidad y velocidad de cada estrategia.
    """
    print("\n" + "=" * 70)
    print("  EXPERIMENTO 2: Comparativa de Prompts")
    print("=" * 70)

    if cases is None:
        cases = ["A1", "A2", "A3"]  # Casos representativos

    results = []

    for prompt_id, prompt_info in PROMPT_STRATEGIES.items():
        print(f"\n  === Prompt: {prompt_id} ({prompt_info['nombre']}) ===")

        prompt_results = []

        for caso_id in cases:
            caso = CASOS_CLINICOS[caso_id]
            prompt = prompt_info["template"].format(text=caso["texto"])

            print(f"    {caso_id}: ", end="", flush=True)

            result = call_model(prompt, host, port)

            if result["success"]:
                # Evaluar calidad
                quality = calculate_quality_metrics(result["text"], caso["entidades"])

                prompt_results.append({
                    "case_id": caso_id,
                    "tps": result["tps_generation"],
                    "quality": quality,
                    "anonymized_text": result["text"][:200] + "..."
                })

                print(f"TPS: {result['tps_generation']:.2f} | "
                      f"Recall: {quality['recall']:.2f} | "
                      f"LRDI: {quality['lrdi']:.0f}%")
            else:
                print(f"ERROR: {result['error']}")

        if prompt_results:
            avg_tps = statistics.mean([r["tps"] for r in prompt_results])
            avg_recall = statistics.mean([r["quality"]["recall"] for r in prompt_results])
            avg_lrdi = statistics.mean([r["quality"]["lrdi"] for r in prompt_results])

            results.append({
                "prompt_id": prompt_id,
                "prompt_name": prompt_info["nombre"],
                "avg_tps": round(avg_tps, 2),
                "avg_recall": round(avg_recall, 4),
                "avg_lrdi": round(avg_lrdi, 2),
                "details": prompt_results
            })

    # Ranking
    print("\n  RANKING DE PROMPTS (por Recall):")
    sorted_results = sorted(results, key=lambda x: x["avg_recall"], reverse=True)
    for i, r in enumerate(sorted_results, 1):
        print(f"    {i}. {r['prompt_id']}: Recall={r['avg_recall']:.4f}, LRDI={r['avg_lrdi']:.0f}%, TPS={r['avg_tps']:.2f}")

    return {
        "experiment": "prompt_comparison",
        "results": results,
        "ranking": [r["prompt_id"] for r in sorted_results]
    }


# =============================================================================
# EXPERIMENTO 3: EVALUACIÓN DE CALIDAD
# =============================================================================

def run_quality_evaluation(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                           prompt_id: str = "detailed", iterations: int = 1) -> Dict:
    """
    Experimento 3: Evaluación completa de calidad con métricas académicas.

    Métricas: Precision, Recall, F1, ALID, LR, LRDI, LRQI
    """
    print("\n" + "=" * 70)
    print("  EXPERIMENTO 3: Evaluación de Calidad (Métricas Académicas)")
    print("=" * 70)
    print(f"  Prompt: {prompt_id}")
    print(f"  Métricas: Precision, Recall, F1, LRDI, LRQI")
    print(f"  Papers: arXiv:2412.10918, arXiv:2406.00062")

    prompt_template = PROMPT_STRATEGIES[prompt_id]["template"]
    results = []

    all_precision = []
    all_recall = []
    all_f1 = []
    all_lrdi = []
    all_lrqi = []
    total_direct_escaped = 0

    for iteration in range(1, iterations + 1):
        print(f"\n  --- Iteración {iteration}/{iterations} ---")

        for caso_id, caso in CASOS_CLINICOS.items():
            prompt = prompt_template.format(text=caso["texto"])

            print(f"    {caso_id}: ", end="", flush=True)

            result = call_model(prompt, host, port)

            if result["success"]:
                quality = calculate_quality_metrics(result["text"], caso["entidades"])

                results.append({
                    "iteration": iteration,
                    "case_id": caso_id,
                    "performance": {
                        "tps": result["tps_generation"],
                        "time_s": result["total_time_s"]
                    },
                    "quality": quality
                })

                all_precision.append(quality["precision"])
                all_recall.append(quality["recall"])
                all_f1.append(quality["f1_micro"])
                all_lrdi.append(quality["lrdi"])
                all_lrqi.append(quality["lrqi"])
                total_direct_escaped += len(quality["direct_escaped"])

                lrdi_status = "OK" if quality["lrdi"] == 100 else "ALERTA"
                print(f"P:{quality['precision']:.2f} R:{quality['recall']:.2f} "
                      f"F1:{quality['f1_micro']:.2f} LRDI:{quality['lrdi']:.0f}% [{lrdi_status}]")
            else:
                print(f"ERROR: {result['error']}")

    # Resumen
    summary = {}
    if all_precision:
        summary = {
            "precision_mean": round(statistics.mean(all_precision), 4),
            "recall_mean": round(statistics.mean(all_recall), 4),
            "f1_micro_mean": round(statistics.mean(all_f1), 4),
            "lrdi_mean": round(statistics.mean(all_lrdi), 2),
            "lrqi_mean": round(statistics.mean(all_lrqi), 2),
            "total_direct_escaped": total_direct_escaped,
            "privacy_risk": "ALTO" if total_direct_escaped > 0 else "BAJO",
            "total_evaluations": len(results)
        }

        print("\n" + "=" * 70)
        print("  MÉTRICAS AGREGADAS (estilo paper académico)")
        print("=" * 70)
        print(f"\n  Métricas Estándar (arXiv:2412.10918):")
        print(f"    Precision:  {summary['precision_mean']:.4f}")
        print(f"    Recall:     {summary['recall_mean']:.4f}")
        print(f"    F1-micro:   {summary['f1_micro_mean']:.4f}")

        print(f"\n  Métricas Levenshtein (arXiv:2406.00062):")
        print(f"    LRDI:       {summary['lrdi_mean']:.2f}%  {'[OK]' if summary['lrdi_mean'] == 100 else '[ALERTA: Directos escapados]'}")
        print(f"    LRQI:       {summary['lrqi_mean']:.2f}%")

        print(f"\n  Riesgo de Privacidad: {summary['privacy_risk']}")
        if total_direct_escaped > 0:
            print(f"    {total_direct_escaped} identificadores directos escaparon en {len(results)} evaluaciones")

    return {
        "experiment": "quality_evaluation",
        "prompt_used": prompt_id,
        "results": results,
        "summary": summary
    }


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Protocolo de Experimentación v3.0")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host del servidor llama.cpp")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Puerto del servidor")
    parser.add_argument("--rendimiento", action="store_true", help="Ejecutar Exp 1: Rendimiento")
    parser.add_argument("--prompts", action="store_true", help="Ejecutar Exp 2: Comparativa prompts")
    parser.add_argument("--calidad", action="store_true", help="Ejecutar Exp 3: Calidad")
    parser.add_argument("--all", action="store_true", help="Ejecutar todos los experimentos")
    parser.add_argument("--iterations", type=int, default=1, help="Número de iteraciones")
    parser.add_argument("--output", default="results", help="Directorio de salida")

    args = parser.parse_args()

    print("=" * 70)
    print("  PROTOCOLO DE EXPERIMENTACIÓN v3.0")
    print("  Universidad de Montevideo - Tesis 2025")
    print("=" * 70)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Host: {args.host}:{args.port}")
    print(f"  Papers: arXiv:2412.10918, arXiv:2406.00062")
    print("=" * 70)

    all_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "host": args.host,
            "port": args.port,
            "iterations": args.iterations
        },
        "experiments": {}
    }

    # Ejecutar experimentos
    if args.all or args.rendimiento:
        result = run_performance_benchmark(args.host, args.port, args.iterations)
        all_results["experiments"]["performance"] = result

    if args.all or args.prompts:
        result = run_prompt_comparison(args.host, args.port)
        all_results["experiments"]["prompts"] = result

    if args.all or args.calidad:
        result = run_quality_evaluation(args.host, args.port, "detailed", args.iterations)
        all_results["experiments"]["quality"] = result

    # Guardar resultados
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"experiment_v3_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: {output_file}")
    print("=" * 70)

    return all_results


if __name__ == "__main__":
    main()
