#!/usr/bin/env python3
"""
casos_sinteticos.py - Dataset de casos clínicos para benchmark de anonimización
Universidad de Montevideo - Tesis 2025

Contiene casos de prueba con ground truth (entidades PHI anotadas) para evaluar
la calidad de la anonimización de los modelos LLM.

Casos incluidos:
- caso_a: Emergencia Cardiología (del protocolo del tutor)
- caso_b: Oncología Evolución (del protocolo del tutor)
- caso_olaf: CTI Completo (historia clínica existente - Olaf Rasmusen)
"""

# =============================================================================
# CASO A: EMERGENCIA (CARDIOLOGÍA) - Del protocolo del tutor
# =============================================================================

CASO_A_TEXTO = """Paciente: Roberto Carlos Méndez, CI 3.456.789-1.
Consulta en Emergencia del Hospital Español el 14/11/2023.
Refiere dolor opresivo retroesternal de 2 horas de evolución, irradiado a brazo izquierdo.
Vive en Bulevar Artigas 2345, Montevideo.
Se llama a su hija Laura al 099-111-222 para informar sobre el ingreso.
Antecedentes: IAM previo (2019) tratado por Dr. Sanguinetti en Asociación Española.
HTA en tratamiento con Enalapril 10mg.
ECG: Supradesnivel ST en V1-V4.
Troponinas: elevadas (2.5 ng/mL).
Conducta: Se activa código infarto, derivación a hemodinamia."""

CASO_A_ENTIDADES = [
    {"tipo": "NOMBRE", "valor": "Roberto Carlos Méndez", "contexto": "nombre paciente"},
    {"tipo": "CI", "valor": "3.456.789-1", "contexto": "cédula de identidad"},
    {"tipo": "UBICACION", "valor": "Hospital Español", "contexto": "institución médica"},
    {"tipo": "FECHA", "valor": "14/11/2023", "contexto": "fecha consulta"},
    {"tipo": "DIRECCION", "valor": "Bulevar Artigas 2345", "contexto": "domicilio"},
    {"tipo": "UBICACION", "valor": "Montevideo", "contexto": "ciudad"},
    {"tipo": "NOMBRE", "valor": "Laura", "contexto": "nombre familiar"},
    {"tipo": "TELEFONO", "valor": "099-111-222", "contexto": "teléfono contacto"},
    {"tipo": "NOMBRE", "valor": "Dr. Sanguinetti", "contexto": "nombre médico"},
    {"tipo": "UBICACION", "valor": "Asociación Española", "contexto": "institución médica"},
]

# =============================================================================
# CASO B: ONCOLOGÍA (EVOLUCIÓN) - Del protocolo del tutor
# =============================================================================

CASO_B_TEXTO = """Ana María Rodríguez, 54 años. Historia Clínica: HC-998877.
Paciente en seguimiento por Carcinoma Ductal Infiltrante de mama izquierda,
diagnosticado en marzo 2023. Estadio IIA (T2N0M0).
Se realiza TAC de control en Asociación Española el 15/10/2023.
Visto por Dra. Gutiérrez en consultorio de Oncología.
Resultado: Sin evidencia de enfermedad metastásica.
Plan: Continuar con Tamoxifeno 20mg/día por 5 años.
Próximo control en 3 meses con mamografía bilateral.
Domicilio: Calle Rivera 456, Salto.
Teléfono de contacto: 473-25890.
Familiar responsable: esposo Juan Carlos Rodríguez, cel 099-888-777."""

CASO_B_ENTIDADES = [
    {"tipo": "NOMBRE", "valor": "Ana María Rodríguez", "contexto": "nombre paciente"},
    {"tipo": "REGISTRO", "valor": "HC-998877", "contexto": "historia clínica"},
    {"tipo": "UBICACION", "valor": "Asociación Española", "contexto": "institución médica"},
    {"tipo": "FECHA", "valor": "15/10/2023", "contexto": "fecha estudio"},
    {"tipo": "NOMBRE", "valor": "Dra. Gutiérrez", "contexto": "nombre médico"},
    {"tipo": "DIRECCION", "valor": "Calle Rivera 456", "contexto": "domicilio"},
    {"tipo": "UBICACION", "valor": "Salto", "contexto": "ciudad"},
    {"tipo": "TELEFONO", "valor": "473-25890", "contexto": "teléfono fijo"},
    {"tipo": "NOMBRE", "valor": "Juan Carlos Rodríguez", "contexto": "nombre familiar"},
    {"tipo": "TELEFONO", "valor": "099-888-777", "contexto": "celular familiar"},
]

# =============================================================================
# CASO OLAF: CTI COMPLETO - Historia clínica existente (del benchmark original)
# =============================================================================

CASO_OLAF_TEXTO = """--- Sección 0 (Encabezado) ---
Nombre:
OLAF RASMUSEN JAKOBSEN
Documento: 2.156.983-0
Ciudad:
MONTEVIDEO
Sexo:
M
Edad:
42
Dirección:
SALTO 3
Registro:
658974

--- Sección 1 ---
Fecha: 20/08/2025
PA: 0
Temperatura (ºC. Ax.): 0
Frec. Cardíaca: 0
Frec. Respiratoria: 0
Saturación de O2 (norm. >95%): 0
Diuresis: 0
Valoración del Dolor Escala Numérica: Sin Dato

Evolución:
Paciente que RO,inquieto por momentos,bajo goteo de Precedex a 15ml/hr,RFM+, apiretico.
SOT en AVM en modo PC c/ una SAT de O2 100%.
HD estable c/ RS al monitor, normotenso.
SNG - c/ NE, glicemia en rango.
RD conservado.
Dep -
H) Confort

Responsables del registro:
AE. M. Brown
LE. J. Bremmerman
Evolución de Enfermería

--- Sección 2 ---
Fecha: 19/08/2025
Evolución:
Usuario similar en lo neurologico, sin SAC, con precedex, impresiona ROS, no registros febriles.
ARM/SOT/PC, FIO2 0.7/PEEP 7, adaptado.
HD estable, RS, normotenso.
VVC YD/VARTPI.
Sonda vesical + RD moderado.
SG - tolerando NE, glicemia en rango.
Dep -
H. Higiene perineal, cambio de sábanas.
H. Fondo de OJOS.
H. Reanudación de goteo de Anfotericina, finaliza hora 23.
H. Acondicionamiento y confort.

Responsables del registro:
AE. N. Bergamazco.
LE. C. Juarez.
CTI 02 Evolucion medica

--- Sección 3 ---
Fecha: 19/08/2025
Evolución en CTI:
Bajo dexmedetomidina + quetiapina + BZD, vigil, ROS, sin focalidad neurologica. Mantiene agitacion por momentos peligrosa; se ajustan dosis, requiere administracion de sedacion puntual. Hipertenso con PAS hasta 200 mmHg sin DOB, se ajusta tratamiento antihipertensivo.
IRA KDIGO III con cifras en descenso, diuresis conservada (unica TSR 15/8).
Bajo tratamiento antimicrobiano con anfotericina B + fluconazol dirigido a criptococosis meníngea (fase inducción hasta 20/8 inclusive), DFC dirigido a enfermedad de Olaf tuberculosa y moxifloxacina dirigida a neumonia bacteriémica a Rhodococcus.
CV de CMV (14/8) positiva 2490, actualmente sin elementos clinicos de colitis, se solicita FGC en contexto de descenso reiterado de la Hb para descartar esofagitis.
Pendiente valoracion por OFT. Conducta expectante respecto a inicio de tto especifico.
Destaca peoria progresiva de rush cutaneo con franco predominio en tronco y MMSS, no asocia areas de decolamiento ni compromiso mucoso. Sin eosinofilia, se solicita hepatograma.
Discutido en conjunto con infectologia, dado dermopatia en contexto de polifarmacia y ausencia de elementos de gravedad se plantea valorar evolucion y se solicita interconsulta con Dermatología.

Sanguinetti, Hermida, Perroni.

--- Sección 4 (OFTALMOLOGÍA - Interconsulta) ---
Fecha: 19/08/2025
Resumen:
Enterados de HC. Fue solicitado FO en CTI para descartar retinitis por CMV.
Se realiza FO dilatado, con mayor dificultad en OD dado pupila no dilata completamente, dado imposibilidad de responder a ordenes, solo se pudo visualizar polo posterior sin poder evaluar periferia.
De lo que se pudo explorar, retina acolada, no se visualizan lesiones, papila rosada,bordes netos.
Dado limitacion de examen fisico por condicion clinica del pte, sin poder colaborar, se sugiere una vez dado de alta, realizar nueva interconsulta para completar valoracion en policlinica de oftalmologia.

Evolución de Enfermería de Olaf Rasmusen, paciente de C.I. 2.156.983-0

--- Sección 5 (Evolución Nefrologica) ---
Fecha: 19/08/2025
Sector: Guardia de Nefrología

Evolución:
GUARDIA NEFROLOGIA
Dras. Cristancho, Ramirez, Martinez.
Dia 9 en CTI
VIH, inmunodepresión severa. Criptocococcosis menignea bajo AnfoB + Fluconazol (FI: 23/7). BK en tratamiento con MOX + AMK + RIF (FI: 11/8). Neumonia bacteriemica a Rhodococcus (HCx1 30/7). Probable PCP en tratamiento con TMP/SMX.
Actualmente bajo goteo de precedex, ROS. Hemodinamia estable tendencia a la hipertension PAM entre 80-90 mmHg se inicia nifedipina 20 mg cada 12hs. Sin registros febriles en ultimas 24hs PCR210 en descenso. IOT+ARM buen IG PAFI 325 RxTx opacidad bilateral basal.
Hb estable en 8.2 g/dl. Sin sangrados evidentes, plaquetas de 140,000.
En lo NU. Diuresis 3750 en 24 hs sin estimulo diuretico, aportes 2500 dia. Aprox. Aporte de K y Mg iv. Por hipopotasemia actualmente sin disionias
crea a la mejoria de 2.68 mg/dl urea 0.89 g/l Na 142 mEq/l K 4.1 mEq/l HCO3 22 mmol/l
Conducta sin criterios de urgencia dialitica al momento
sugerimos solicitar control de magnesemia

--- Sección 6 ---
Fecha: 19/08/2025
Evolución:
Usuario con EPM, se avisa a guardia medica se aumenta goteo de precedex mmas dilusion de fentanyl, que no mejora, y midazo cede un poco pero luego vuelve a EPM
Apiretico
ARM modo espontaneo, se agota se cambia aVC
HD con tendencia a HTA, con TS
sg sin retencion
sv+ rd mantenido
dep (-)
H cuidados de enfermeria
pierde via femoral se utiliza via de HD

Responsables del registro:
Eliana Eulacio
Andrea Cancela"""

CASO_OLAF_ENTIDADES = [
    # Datos del paciente
    {"tipo": "NOMBRE", "valor": "OLAF RASMUSEN JAKOBSEN", "contexto": "nombre paciente"},
    {"tipo": "CI", "valor": "2.156.983-0", "contexto": "cédula de identidad"},
    {"tipo": "UBICACION", "valor": "MONTEVIDEO", "contexto": "ciudad"},
    {"tipo": "DIRECCION", "valor": "SALTO 3", "contexto": "domicilio"},
    {"tipo": "REGISTRO", "valor": "658974", "contexto": "número de registro"},
    # Fechas (múltiples)
    {"tipo": "FECHA", "valor": "20/08/2025", "contexto": "fecha evolución"},
    {"tipo": "FECHA", "valor": "19/08/2025", "contexto": "fecha evolución"},
    # Personal médico Sección 1
    {"tipo": "NOMBRE", "valor": "M. Brown", "contexto": "auxiliar enfermería"},
    {"tipo": "NOMBRE", "valor": "J. Bremmerman", "contexto": "licenciado enfermería"},
    # Personal médico Sección 2
    {"tipo": "NOMBRE", "valor": "N. Bergamazco", "contexto": "auxiliar enfermería"},
    {"tipo": "NOMBRE", "valor": "C. Juarez", "contexto": "licenciado enfermería"},
    # Personal médico Sección 3
    {"tipo": "NOMBRE", "valor": "Sanguinetti", "contexto": "médico CTI"},
    {"tipo": "NOMBRE", "valor": "Hermida", "contexto": "médico CTI"},
    {"tipo": "NOMBRE", "valor": "Perroni", "contexto": "médico CTI"},
    # Mención en texto
    {"tipo": "NOMBRE", "valor": "Olaf Rasmusen", "contexto": "nombre en evolución"},
    # Personal médico Sección 5
    {"tipo": "NOMBRE", "valor": "Cristancho", "contexto": "médico nefrología"},
    {"tipo": "NOMBRE", "valor": "Ramirez", "contexto": "médico nefrología"},
    {"tipo": "NOMBRE", "valor": "Martinez", "contexto": "médico nefrología"},
    # Personal médico Sección 6
    {"tipo": "NOMBRE", "valor": "Eliana Eulacio", "contexto": "enfermería"},
    {"tipo": "NOMBRE", "valor": "Andrea Cancela", "contexto": "enfermería"},
]

# =============================================================================
# DICCIONARIO PRINCIPAL DE CASOS
# =============================================================================

CASOS = {
    "caso_a": {
        "id": "caso_a",
        "nombre": "Emergencia Cardiología",
        "descripcion": "Caso del protocolo del tutor - Dolor torácico agudo, código infarto",
        "texto": CASO_A_TEXTO,
        "entidades": CASO_A_ENTIDADES,
        "num_entidades": len(CASO_A_ENTIDADES),
        "origen": "Protocolo tutor - FASE 3"
    },
    "caso_b": {
        "id": "caso_b",
        "nombre": "Oncología Evolución",
        "descripcion": "Caso del protocolo del tutor - Seguimiento carcinoma de mama",
        "texto": CASO_B_TEXTO,
        "entidades": CASO_B_ENTIDADES,
        "num_entidades": len(CASO_B_ENTIDADES),
        "origen": "Protocolo tutor - FASE 3"
    },
    "caso_olaf": {
        "id": "caso_olaf",
        "nombre": "CTI Completo - Olaf Rasmusen",
        "descripcion": "Historia clínica completa de CTI con múltiples evoluciones",
        "texto": CASO_OLAF_TEXTO,
        "entidades": CASO_OLAF_ENTIDADES,
        "num_entidades": len(CASO_OLAF_ENTIDADES),
        "origen": "Benchmark original - tampered (2).pdf"
    }
}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def listar_casos():
    """Lista todos los casos disponibles."""
    print("\n" + "=" * 60)
    print("  CASOS DE PRUEBA DISPONIBLES")
    print("=" * 60)
    for caso_id, caso in CASOS.items():
        print(f"\n  [{caso_id}] {caso['nombre']}")
        print(f"      {caso['descripcion']}")
        print(f"      Entidades PHI: {caso['num_entidades']}")
        print(f"      Caracteres: {len(caso['texto'])}")
    print("\n" + "=" * 60)


def obtener_caso(caso_id: str) -> dict:
    """Obtiene un caso por su ID."""
    if caso_id not in CASOS:
        raise ValueError(f"Caso '{caso_id}' no encontrado. Disponibles: {list(CASOS.keys())}")
    return CASOS[caso_id]


def obtener_todos_los_casos() -> dict:
    """Retorna todos los casos."""
    return CASOS


if __name__ == "__main__":
    listar_casos()

    # Mostrar detalle del caso A como ejemplo
    print("\n" + "=" * 60)
    print("  DETALLE CASO A (ejemplo)")
    print("=" * 60)
    caso = obtener_caso("caso_a")
    print(f"\nTexto ({len(caso['texto'])} chars):")
    print("-" * 40)
    print(caso["texto"][:500] + "...")
    print("-" * 40)
    print(f"\nEntidades a anonimizar ({len(caso['entidades'])}):")
    for e in caso["entidades"]:
        print(f"  - [{e['tipo']}] \"{e['valor']}\" ({e['contexto']})")
