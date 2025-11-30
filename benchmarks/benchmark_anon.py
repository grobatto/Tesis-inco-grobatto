#!/usr/bin/env python3
"""
benchmark_anon.py - Benchmark de Anonimización de Historiales Clínicos
Universidad de Montevideo - Tesis 2025

Ejecuta benchmarks de anonimización de datos clínicos usando LLMs en IBM Power10.
Caso de prueba: Historia clínica real (datos sintéticos) del paciente Olaf Rasmusen.

Uso:
    python benchmark_anon.py                    # Usa puerto 8089 por defecto
    python benchmark_anon.py --port 8088        # Usa Mistral en puerto 8088
    python benchmark_anon.py --port 8090        # Usa Llama3 en puerto 8090

Requisitos:
    pip install requests
"""

import requests
import time
import json
import statistics
import argparse
from datetime import datetime


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

DEFAULT_PORT = 8089
ITERATIONS = 5

# =============================================================================
# TEXTO CLÍNICO DE PRUEBA (Caso Olaf Rasmusen - tampered (2).pdf)
# =============================================================================

CLINICAL_TEXT = """--- Sección 0 (Encabezado) ---
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
Andrea Cancela
"""

# =============================================================================
# SYSTEM PROMPT PARA ANONIMIZACIÓN
# =============================================================================

SYSTEM_PROMPT = """Eres un asistente especializado en anonimizar historias clínicas en español.

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
# FUNCIONES
# =============================================================================

def run_anonymization(port: int, clinical_text: str) -> dict:
    """
    Ejecuta una solicitud de anonimización al modelo.

    Returns:
        dict con 'content', 'tokens', 'time_ms', 'tps'
    """
    url = f"http://localhost:{port}/completion"

    prompt = SYSTEM_PROMPT.format(text=clinical_text)

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


def run_benchmark(port: int, iterations: int = ITERATIONS) -> dict:
    """
    Ejecuta el benchmark completo.
    """
    print(f"\n{'='*60}")
    print(f"  BENCHMARK DE ANONIMIZACIÓN CLÍNICA")
    print(f"  Puerto: {port} | Iteraciones: {iterations}")
    print(f"{'='*60}\n")

    results = []
    first_response = None

    for i in range(iterations):
        print(f"Iteración {i+1}/{iterations}...", end=" ", flush=True)

        try:
            result = run_anonymization(port, CLINICAL_TEXT)
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

    stats = {
        "port": port,
        "iterations": iterations,
        "timestamp": datetime.now().isoformat(),
        "tps_avg": statistics.mean(tps_values),
        "tps_std": statistics.stdev(tps_values) if len(tps_values) > 1 else 0,
        "tps_min": min(tps_values),
        "tps_max": max(tps_values),
        "time_avg_ms": statistics.mean(time_values),
        "tokens_avg": statistics.mean(token_values),
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

    print(f"\n{'='*60}")
    print(f"  PRIMERA RESPUESTA (para validación)")
    print(f"{'='*60}")
    print(stats["first_response"][:2000] if stats["first_response"] else "Sin respuesta")
    print(f"{'='*60}\n")


def save_results(stats: dict, filename: str = None):
    """Guarda los resultados en un archivo JSON."""
    if stats is None:
        return

    if filename is None:
        filename = f"benchmark_port{stats['port']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # No guardar la respuesta completa en el JSON para mantenerlo limpio
    save_stats = {k: v for k, v in stats.items() if k != "first_response"}
    save_stats["first_response_preview"] = stats["first_response"][:500] if stats["first_response"] else ""

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(save_stats, f, indent=2, ensure_ascii=False)

    print(f"Resultados guardados en: {filename}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Benchmark de anonimización clínica en IBM Power10"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"Puerto del servidor LLM (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=ITERATIONS,
        help=f"Número de iteraciones (default: {ITERATIONS})"
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

    args = parser.parse_args()

    print("\n" + "="*60)
    print("  BENCHMARK DE ANONIMIZACIÓN CLÍNICA - IBM POWER10")
    print("  Universidad de Montevideo - Tesis 2025")
    print("="*60)
    print(f"\nTexto clínico: {len(CLINICAL_TEXT)} caracteres")
    print(f"PHI a detectar: Nombre, CI, Dirección, Ciudad, Registro, ~10 nombres médicos")

    # Ejecutar benchmark
    stats = run_benchmark(args.port, args.iterations)

    # Mostrar resultados
    print_results(stats)

    # Guardar si se solicita
    if args.save and stats:
        save_results(stats, args.output)
