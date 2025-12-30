#!/usr/bin/env python3
"""
Benchmark de Rendimiento - IBM Power10
Universidad de Montevideo - Tesis 2025
"""

import urllib.request
import json
import time
import statistics
from datetime import datetime

# Casos clínicos de prueba
CASOS = {
    "A1": {
        "nombre": "Emergencia Cardiología",
        "texto": """Paciente Juan Pérez, CI 1.234.567-8, 58 años, ingresa a Emergencia del Hospital Maciel el 15/03/2024.
Reside en Av. Italia 2345, Montevideo. Tel: 099-123-456.
Atendido por Dr. García. Diagnóstico: IAM anterior. Tratamiento: AAS, Clopidogrel.
Familiar: María López (esposa).""",
    },
    "A2": {
        "nombre": "Consulta Oncología",
        "texto": """HC-2024-00456. Paciente María Rodríguez, CI 2.345.678-9, 45 años.
Domicilio: Bvar. Artigas 1234, Pocitos, Montevideo.
Antecedente: Ca mama. Tratamiento: Quimioterapia.
Control con Dra. Fernández. Tel: 2600-1234.""",
    },
    "A3": {
        "nombre": "Evolución CTI",
        "texto": """Hospital de Clínicas. Paciente Roberto Silva, CI 3.456.789-0, 67 años.
Día 5 internación. Ingreso: 10/03/2024. Diagnóstico: Neumonía COVID-19.
ARM: FiO2 50%. Dr. Martínez. LE. Ana González.
Familiar: Carlos Silva, cel 098-111-222.""",
    },
    "A4": {
        "nombre": "Alta Cirugía",
        "texto": """Alta médica - Sanatorio Americano.
Paciente: Pedro Gómez, CI 4.567.890-1, 52 años.
Cirugía: Colecistectomía laparoscópica 18/03/2024.
Evolución favorable. Alta 20/03/2024.
Control con Dr. Rodríguez en 7 días. Tel: 099-888-777.""",
    },
    "A5": {
        "nombre": "Interconsulta Neurología",
        "texto": """Interconsulta Neurología - CASMU.
Paciente Laura Fernández, CI 5.678.901-2, 35 años.
Cefalea crónica. RM encéfalo normal.
Indicación: Topiramato 25mg/noche.
Dra. Martínez. Próximo control: 01/04/2024.""",
    }
}

# Prompts a evaluar
PROMPTS = {
    "baseline": """Anonimiza el siguiente texto clínico reemplazando datos personales por placeholders.
Usa: NOMBRE, CI, DIRECCION, UBICACION, TELEFONO, FECHA, REGISTRO entre corchetes.
Solo devuelve el texto anonimizado:

{text}""",

    "detailed": """Eres un asistente de anonimización clínica.

Reemplaza:
- Nombres de personas por NOMBRE entre corchetes
- Cédulas por CI entre corchetes
- Direcciones por DIRECCION entre corchetes
- Ciudades y hospitales por UBICACION entre corchetes
- Teléfonos por TELEFONO entre corchetes
- Fechas por FECHA entre corchetes
- Historias clínicas por REGISTRO entre corchetes

Conserva diagnósticos, tratamientos y valores médicos.
Solo devuelve el texto anonimizado:

{text}""",

    "few_shot": """Ejemplo de anonimización:
Input: Dr. García atendió a Juan, CI 1.234.567-8
Output: Dr. NOMBRE atendió a NOMBRE, CI CI (todo entre corchetes)

Ahora anonimiza:
{text}"""
}


def llamar_modelo(prompt, host="localhost", port=8080, timeout=120):
    """Llama al servidor llama.cpp."""
    payload = {
        "prompt": prompt,
        "n_predict": 300,
        "temperature": 0.1,
        "top_k": 40,
        "top_p": 0.95,
        "stream": False
    }

    url = f"http://{host}:{port}/completion"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    inicio = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    tiempo_total = time.time() - inicio

    tokens_gen = result.get("tokens_predicted", 0)
    tokens_prompt = result.get("tokens_evaluated", 0)
    tiempo_gen_ms = result.get("timings", {}).get("predicted_ms", tiempo_total * 1000)
    tiempo_prompt_ms = result.get("timings", {}).get("prompt_ms", 0)

    tps_gen = tokens_gen / (tiempo_gen_ms / 1000) if tiempo_gen_ms > 0 else 0
    tps_prompt = tokens_prompt / (tiempo_prompt_ms / 1000) if tiempo_prompt_ms > 0 else 0

    return {
        "texto": result.get("content", ""),
        "tokens_gen": tokens_gen,
        "tokens_prompt": tokens_prompt,
        "tiempo_gen_ms": tiempo_gen_ms,
        "tiempo_prompt_ms": tiempo_prompt_ms,
        "tps_gen": tps_gen,
        "tps_prompt": tps_prompt
    }


def main():
    print("=" * 70)
    print("  BENCHMARK IBM Power10 - Anonimización con LLM")
    print("  Universidad de Montevideo - Tesis 2025")
    print("=" * 70)
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Modelo: Qwen2.5-1.5B-Instruct Q4_K_M")
    print(f"  Hardware: IBM Power10 (ppc64le)")
    print("=" * 70)

    resultados = []

    for prompt_id, prompt_template in PROMPTS.items():
        print(f"\n  === Prompt: {prompt_id} ===")

        for caso_id, caso in CASOS.items():
            prompt = prompt_template.format(text=caso["texto"])

            print(f"    {caso_id} ({caso['nombre']}): ", end="", flush=True)

            try:
                r = llamar_modelo(prompt)
                resultados.append({
                    "prompt": prompt_id,
                    "caso": caso_id,
                    "caso_nombre": caso["nombre"],
                    "tps_gen": r["tps_gen"],
                    "tps_prompt": r["tps_prompt"],
                    "tokens_gen": r["tokens_gen"],
                    "tokens_prompt": r["tokens_prompt"],
                    "tiempo_gen_ms": r["tiempo_gen_ms"],
                    "tiempo_prompt_ms": r["tiempo_prompt_ms"]
                })
                print(f"TPS: {r['tps_gen']:.2f} | Tokens: {r['tokens_gen']}")
            except Exception as e:
                print(f"ERROR: {e}")

    # Calcular estadísticas
    print("\n" + "=" * 70)
    print("  RESULTADOS AGREGADOS")
    print("=" * 70)

    # Por prompt
    for prompt_id in PROMPTS.keys():
        datos = [r for r in resultados if r["prompt"] == prompt_id]
        if datos:
            tps_values = [r["tps_gen"] for r in datos]
            print(f"\n  [{prompt_id}]")
            print(f"    TPS promedio:     {statistics.mean(tps_values):.2f}")
            if len(tps_values) > 1:
                print(f"    TPS desv. std:    {statistics.stdev(tps_values):.2f}")
            print(f"    Casos evaluados:  {len(datos)}")

    # Global
    all_tps = [r["tps_gen"] for r in resultados]
    all_tps_prompt = [r["tps_prompt"] for r in resultados]

    print("\n" + "-" * 40)
    print("  MÉTRICAS GLOBALES:")
    print(f"    TPS generación promedio:  {statistics.mean(all_tps):.2f}")
    print(f"    TPS generación min/max:   {min(all_tps):.2f} / {max(all_tps):.2f}")
    print(f"    TPS prompt eval promedio: {statistics.mean(all_tps_prompt):.2f}")
    print(f"    Total pruebas:            {len(resultados)}")

    # Guardar resultados
    output = {
        "experimento": "benchmark_power10_v3",
        "timestamp": datetime.now().isoformat(),
        "hardware": {
            "plataforma": "IBM Power10",
            "arquitectura": "ppc64le",
            "compilacion": "llama.cpp con -mcpu=power10"
        },
        "modelo": {
            "nombre": "Qwen2.5-1.5B-Instruct",
            "cuantizacion": "Q4_K_M",
            "archivo": "qwen2.5-1.5b-instruct-q4_k_m.gguf"
        },
        "resultados": resultados,
        "resumen": {
            "tps_generacion_promedio": statistics.mean(all_tps),
            "tps_generacion_std": statistics.stdev(all_tps) if len(all_tps) > 1 else 0,
            "tps_generacion_min": min(all_tps),
            "tps_generacion_max": max(all_tps),
            "tps_prompt_promedio": statistics.mean(all_tps_prompt),
            "total_pruebas": len(resultados)
        }
    }

    output_file = f"/root/benchmarks/results/benchmark_power10_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: {output_file}")
    print("=" * 70)

    return output


if __name__ == "__main__":
    main()
