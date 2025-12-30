#!/usr/bin/env python3
"""
prompts_anonimizacion.py - Suite de prompts para benchmark de anonimización
Universidad de Montevideo - Tesis 2025

Contiene diferentes estrategias de prompting para evaluar cuál produce
mejores resultados en la tarea de anonimización de datos clínicos.

Basado en metodología de papers académicos:
- arXiv:2412.10918 - LLMs-in-the-Loop Part 2
- arXiv:2406.00062 - Unlocking LLMs for Clinical Text Anonymization

Estrategias (8 total):
- baseline: Instrucción mínima (zero-shot simple)
- detailed: Instrucciones completas (prompt original del proyecto)
- few_shot: Ejemplos antes del texto
- chain_of_thought: Razonamiento paso a paso
- master_tutor: Prompt sugerido por el tutor
- medico: Enfoque en Ley 18.331 y terminología PHI
- structured_output: Formato JSON estructurado
- hybrid: Combina few-shot + chain-of-thought
"""

# =============================================================================
# PROMPT BASELINE - Instrucción mínima
# =============================================================================

PROMPT_BASELINE = """Anonimiza el siguiente texto clínico reemplazando:
- Nombres de personas por [NOMBRE]
- Cédulas/documentos por [CI]
- Direcciones por [DIRECCION]
- Ciudades por [UBICACION]
- Teléfonos por [TELEFONO]
- Fechas por [FECHA]
- Registros/historias clínicas por [REGISTRO]

Texto a anonimizar:
{text}"""

# =============================================================================
# PROMPT DETAILED - Instrucciones completas (original del proyecto)
# =============================================================================

PROMPT_DETAILED = """Eres un asistente especializado en anonimizar historias clínicas en español.

INSTRUCCIONES OBLIGATORIAS
1) Sustituye SOLO datos personales por estos placeholders exactos:
   - Nombres y apellidos de personas (pacientes, familiares, médicos) → [NOMBRE]
   - Teléfonos (cualquier formato, nacional o internacional) → [TELEFONO]
   - Cédulas de identidad / documentos → [CI]
   - Direcciones postales/domicilios (calle/avenida + número, esquinas, apto, barrio) → [DIRECCIÓN]
   - Ciudades y localidades específicas → [UBICACIÓN]
   - Números de registro/historia clínica → [REGISTRO]

2) Conserva TODO lo demás sin cambios: síntomas, diagnósticos, dosis, resultados, unidades, abreviaturas, signos de puntuación, mayúsculas/minúsculas.

3) Si ya hay placeholders ([NOMBRE], [TELEFONO], [CI], [DIRECCIÓN]), NO los modifiques.

4) Títulos y roles: conserva el título y reemplaza solo el nombre. Ej.: "Dr. [NOMBRE]", "Lic. [NOMBRE]", "AE. [NOMBRE]", "LE. [NOMBRE]".

5) Teléfonos: reemplaza secuencias de 7+ dígitos o con separadores (+598, -, espacios, paréntesis).

6) Direcciones: incluye referencias claras de domicilio (calle/esquina/número/apto/barrio).

7) No inventes datos, no agregues comentarios, no cambies el formato. Respeta saltos de línea y espacios originales.

8) Devuelve ÚNICAMENTE el texto anonimizado, sin explicaciones ni encabezados.

Texto a anonimizar:
{text}"""

# =============================================================================
# PROMPT FEW-SHOT - Con ejemplos antes del texto
# =============================================================================

PROMPT_FEW_SHOT = """Anonimiza textos clínicos reemplazando datos personales por placeholders.

=== EJEMPLO 1 ===
Input: "Dr. García atendió a Juan Pérez, CI 1.234.567-8, en Hospital Central."
Output: "Dr. [NOMBRE] atendió a [NOMBRE], CI [CI], en [UBICACION]."

=== EJEMPLO 2 ===
Input: "Paciente María López vive en Av. Italia 2345, Montevideo. Tel: 099-123-456."
Output: "Paciente [NOMBRE] vive en [DIRECCION], [UBICACION]. Tel: [TELEFONO]."

=== EJEMPLO 3 ===
Input: "Historia Clínica HC-12345. Fecha: 15/03/2024. Responsable: Dra. Fernández."
Output: "Historia Clínica [REGISTRO]. Fecha: [FECHA]. Responsable: Dra. [NOMBRE]."

=== REGLAS ===
- [NOMBRE]: nombres de pacientes, familiares, médicos
- [CI]: cédulas de identidad, documentos
- [DIRECCION]: calles, avenidas con números
- [UBICACION]: ciudades, hospitales, instituciones
- [TELEFONO]: números de teléfono
- [FECHA]: fechas específicas
- [REGISTRO]: números de historia clínica

=== AHORA ANONIMIZA ===
{text}"""

# =============================================================================
# PROMPT CHAIN-OF-THOUGHT - Razonamiento paso a paso
# =============================================================================

PROMPT_CHAIN_OF_THOUGHT = """Vas a anonimizar un texto clínico siguiendo estos pasos:

PASO 1: Lee el texto e identifica TODOS los datos personales:
- Nombres de personas (pacientes, familiares, médicos, enfermeros)
- Números de documento/cédula
- Direcciones y domicilios
- Ciudades e instituciones médicas
- Números de teléfono
- Fechas específicas
- Números de registro/historia clínica

PASO 2: Para cada dato encontrado, determina su categoría:
- Nombres → [NOMBRE]
- Documentos → [CI]
- Direcciones → [DIRECCION]
- Ciudades/hospitales → [UBICACION]
- Teléfonos → [TELEFONO]
- Fechas → [FECHA]
- Registros → [REGISTRO]

PASO 3: Reemplaza cada dato por su placeholder correspondiente.

PASO 4: Verifica que NO hayas modificado datos clínicos (diagnósticos, medicamentos, dosis, resultados de laboratorio).

PASO 5: Devuelve ÚNICAMENTE el texto anonimizado, sin explicaciones.

Texto a anonimizar:
{text}"""

# =============================================================================
# PROMPT MASTER TUTOR - Del protocolo del tutor
# =============================================================================

PROMPT_MASTER_TUTOR = """Eres un asistente experto en privacidad médica. Tu tarea es anonimizar la historia clínica proporcionada siguiendo estrictamente estas reglas:

- Reemplaza NOMBRES de pacientes, familiares y médicos por [NOMBRE].
- Reemplaza FECHAS exactas por [FECHA].
- Reemplaza LUGARES (direcciones, ciudades, hospitales) por [UBICACIÓN].
- Reemplaza IDENTIFICADORES (Cédulas, Teléfonos, Historias Clínicas) por [ID].
- NO modifiques diagnósticos, síntomas ni medicamentos.
- Devuelve SOLO el texto anonimizado, sin introducciones.

Texto a anonimizar:
{text}"""

# =============================================================================
# PROMPT MÉDICO ESPECIALIZADO - Enfoque en terminología médica
# =============================================================================

PROMPT_MEDICO = """Eres un profesional de salud especializado en protección de datos según la Ley 18.331 de Uruguay.

Tu tarea es des-identificar la siguiente historia clínica eliminando toda Información de Salud Protegida (PHI) mientras preservas la utilidad clínica del documento.

DATOS A ANONIMIZAR (PHI):
1. Identificadores directos:
   - Nombres completos → [NOMBRE]
   - Cédula de identidad → [CI]
   - Números de teléfono → [TELEFONO]
   - Números de historia clínica → [REGISTRO]

2. Cuasi-identificadores:
   - Direcciones específicas → [DIRECCION]
   - Ciudades/localidades → [UBICACION]
   - Fechas exactas → [FECHA]
   - Nombres de instituciones → [UBICACION]

DATOS A PRESERVAR (Utilidad Clínica):
- Diagnósticos y códigos CIE-10
- Medicamentos y dosis
- Resultados de laboratorio y valores
- Signos vitales
- Procedimientos realizados
- Abreviaturas médicas (ECG, TAC, RM, etc.)

Devuelve SOLO el texto anonimizado:

{text}"""

# =============================================================================
# PROMPT STRUCTURED OUTPUT - Formato JSON estructurado
# =============================================================================

PROMPT_STRUCTURED_OUTPUT = """Anonimiza el siguiente texto clínico y devuelve el resultado en formato estructurado.

TAREA: Identificar y reemplazar toda la Información de Salud Protegida (PHI).

CATEGORÍAS PHI A DETECTAR:
1. NOMBRE: Nombres de pacientes, médicos, familiares, enfermeros
2. CI: Cédula de identidad, documentos de identificación
3. TELEFONO: Números de teléfono (fijos y móviles)
4. DIRECCION: Calles, avenidas, números, apartamentos
5. UBICACION: Ciudades, departamentos, hospitales, clínicas
6. FECHA: Fechas de ingreso, alta, nacimiento, procedimientos
7. REGISTRO: Números de historia clínica, expedientes

FORMATO DE SALIDA:
Devuelve ÚNICAMENTE el texto anonimizado usando los placeholders [NOMBRE], [CI], [TELEFONO], [DIRECCION], [UBICACION], [FECHA], [REGISTRO].

NO incluyas explicaciones, listas de entidades encontradas, ni comentarios adicionales.

TEXTO A ANONIMIZAR:
{text}"""

# =============================================================================
# PROMPT HYBRID - Combina Few-Shot + Chain-of-Thought
# =============================================================================

PROMPT_HYBRID = """Eres un experto en des-identificación de registros médicos.

=== EJEMPLOS DE REFERENCIA ===

Ejemplo 1:
Input: "Dr. Martínez evaluó a Pedro Gómez (CI 3.456.789-0) el 20/01/2024."
Proceso: Identifico nombre médico (Martínez), nombre paciente (Pedro Gómez), CI (3.456.789-0), fecha (20/01/2024).
Output: "Dr. [NOMBRE] evaluó a [NOMBRE] (CI [CI]) el [FECHA]."

Ejemplo 2:
Input: "Paciente de 45 años, residente en Colonia 1234 apto 5, Pocitos. Contacto: 099-888-777."
Proceso: Identifico dirección (Colonia 1234 apto 5), barrio (Pocitos), teléfono (099-888-777). Edad se preserva.
Output: "Paciente de 45 años, residente en [DIRECCION], [UBICACION]. Contacto: [TELEFONO]."

Ejemplo 3:
Input: "HC-2024-00123. Ingresa a CASMU derivado del Hospital Maciel con diagnóstico de IAM."
Proceso: Identifico registro (HC-2024-00123), instituciones (CASMU, Hospital Maciel). Diagnóstico (IAM) se preserva.
Output: "[REGISTRO]. Ingresa a [UBICACION] derivado del [UBICACION] con diagnóstico de IAM."

=== AHORA ES TU TURNO ===

PASO 1: Lee el texto e identifica todas las entidades PHI.
PASO 2: Clasifica cada entidad en su categoría.
PASO 3: Reemplaza por el placeholder correspondiente.
PASO 4: Verifica que datos clínicos (diagnósticos, medicamentos, valores) permanezcan intactos.
PASO 5: Devuelve SOLO el texto anonimizado.

TEXTO:
{text}"""

# =============================================================================
# DICCIONARIO PRINCIPAL DE PROMPTS
# =============================================================================

PROMPTS = {
    "baseline": {
        "id": "baseline",
        "nombre": "Prompt Simple",
        "descripcion": "Instrucción mínima sin ejemplos ni detalles",
        "template": PROMPT_BASELINE,
        "esperado": "Baja precisión, puede fallar en casos edge",
        "tokens_estimados": 80
    },
    "detailed": {
        "id": "detailed",
        "nombre": "Prompt Detallado (Original)",
        "descripcion": "Instrucciones completas con 8 reglas específicas",
        "template": PROMPT_DETAILED,
        "esperado": "Alta precisión, usado en benchmarks previos",
        "tokens_estimados": 350
    },
    "few_shot": {
        "id": "few_shot",
        "nombre": "Few-Shot Learning",
        "descripcion": "3 ejemplos concretos antes del texto a procesar",
        "template": PROMPT_FEW_SHOT,
        "esperado": "Buena precisión por aprendizaje en contexto",
        "tokens_estimados": 300
    },
    "chain_of_thought": {
        "id": "chain_of_thought",
        "nombre": "Chain of Thought",
        "descripcion": "Razonamiento paso a paso en 5 etapas",
        "template": PROMPT_CHAIN_OF_THOUGHT,
        "esperado": "Mayor tiempo pero potencialmente más preciso",
        "tokens_estimados": 250
    },
    "master_tutor": {
        "id": "master_tutor",
        "nombre": "Master Prompt (Tutor)",
        "descripcion": "Prompt sugerido en el protocolo del tutor",
        "template": PROMPT_MASTER_TUTOR,
        "esperado": "Referencia del protocolo de experimentación",
        "tokens_estimados": 120
    },
    "medico": {
        "id": "medico",
        "nombre": "Médico Especializado",
        "descripcion": "Enfoque en Ley 18.331 y terminología PHI",
        "template": PROMPT_MEDICO,
        "esperado": "Mejor distinción entre PHI y datos clínicos",
        "tokens_estimados": 280
    },
    "structured_output": {
        "id": "structured_output",
        "nombre": "Structured Output",
        "descripcion": "Categorías PHI explícitas con formato estructurado",
        "template": PROMPT_STRUCTURED_OUTPUT,
        "esperado": "Consistencia en placeholders, menos variabilidad",
        "tokens_estimados": 200
    },
    "hybrid": {
        "id": "hybrid",
        "nombre": "Hybrid (Few-Shot + CoT)",
        "descripcion": "Combina ejemplos con razonamiento paso a paso",
        "template": PROMPT_HYBRID,
        "esperado": "Mejor precisión combinando técnicas (mayor latencia)",
        "tokens_estimados": 450
    }
}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def listar_prompts():
    """Lista todos los prompts disponibles."""
    print("\n" + "=" * 70)
    print("  ESTRATEGIAS DE PROMPTING DISPONIBLES")
    print("=" * 70)
    for prompt_id, prompt in PROMPTS.items():
        print(f"\n  [{prompt_id}] {prompt['nombre']}")
        print(f"      {prompt['descripcion']}")
        print(f"      Tokens estimados: ~{prompt['tokens_estimados']}")
        print(f"      Esperado: {prompt['esperado']}")
    print("\n" + "=" * 70)


def obtener_prompt(prompt_id: str) -> dict:
    """Obtiene un prompt por su ID."""
    if prompt_id not in PROMPTS:
        raise ValueError(f"Prompt '{prompt_id}' no encontrado. Disponibles: {list(PROMPTS.keys())}")
    return PROMPTS[prompt_id]


def formatear_prompt(prompt_id: str, texto: str) -> str:
    """Formatea un prompt con el texto clínico."""
    prompt = obtener_prompt(prompt_id)
    return prompt["template"].format(text=texto)


def obtener_todos_los_prompts() -> dict:
    """Retorna todos los prompts."""
    return PROMPTS


if __name__ == "__main__":
    listar_prompts()

    # Mostrar ejemplo de prompt formateado
    print("\n" + "=" * 70)
    print("  EJEMPLO: Prompt 'baseline' formateado")
    print("=" * 70)
    texto_ejemplo = "Dr. García atendió a Juan Pérez, CI 1.234.567-8"
    prompt_formateado = formatear_prompt("baseline", texto_ejemplo)
    print(prompt_formateado)
