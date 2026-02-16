# 06 - Benchmark de Anonimización de Datos Clínicos

## Introducción

Este documento describe el proceso de benchmark para evaluar la capacidad de los modelos LLM de anonimizar historiales clínicos en español, ejecutándose en IBM Power10 con aceleradores MMA.

## Caso de Uso

### Contexto

La Facultad de Medicina de la Universidad de la República (UdelaR) necesita anonimizar historiales clínicos para:
- Investigación médica
- Formación de estudiantes
- Cumplimiento normativo (protección de datos de salud)

### Datos a Anonimizar (PHI - Protected Health Information)

| Tipo de Dato | Placeholder | Ejemplo |
|--------------|-------------|---------|
| Nombres de personas | `[NOMBRE]` | Pacientes, médicos, enfermeros |
| Cédula de identidad | `[CI]` | 2.156.983-0 |
| Direcciones | `[DIRECCIÓN]` | SALTO 3 |
| Ciudades | `[UBICACIÓN]` | MONTEVIDEO |
| Teléfonos | `[TELEFONO]` | 099-123-456 |
| Registros médicos | `[REGISTRO]` | 658974 |

## Caso de Prueba: Olaf Rasmusen

### Documento Original

El documento de prueba (`tampered (2).pdf`) contiene:
- **12 páginas** de evolución clínica
- **~15 nombres** de personal médico
- **Múltiples secciones**: Evolución CTI, Enfermería, Nefrología, Oftalmología
- **Datos sensibles**: Nombre, CI, dirección, ciudad, registro

### PHI a Detectar

```
Nombre:       OLAF RASMUSEN JAKOBSEN
Documento:    2.156.983-0
Ciudad:       MONTEVIDEO
Dirección:    SALTO 3
Registro:     658974
Personal:     M. Brown, J. Bremmerman, N. Bergamazco, C. Juarez,
              Sanguinetti, Hermida, Perroni, Eliana Eulacio,
              Andrea Cancela, Dras. Cristancho, Ramirez, Martinez...
```

## Script de Benchmark

### Ubicación

```
benchmarks/
├── benchmark_anon.py       # Script principal
├── run_all_models.sh       # Ejecutar en todos los modelos
└── results/                # Resultados JSON
```

### Uso

```bash
# Benchmark en un modelo específico
python benchmark_anon.py --port 8089

# Benchmark con más iteraciones
python benchmark_anon.py --port 8089 --iterations 10

# Guardar resultados
python benchmark_anon.py --port 8089 --save

# Ejecutar en todos los modelos
./run_all_models.sh
```

### Parámetros

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `--port`, `-p` | Puerto del servidor LLM | 8089 |
| `--iterations`, `-i` | Número de iteraciones | 5 |
| `--save`, `-s` | Guardar resultados en JSON | False |
| `--output`, `-o` | Archivo de salida | Auto-generado |

## Prompt de Anonimización

### System Prompt Utilizado

```
Eres un asistente especializado en anonimizar historias clínicas en español.

INSTRUCCIONES OBLIGATORIAS
1) Sustituye SOLO datos personales por estos placeholders exactos:
   - Nombres y apellidos de personas → [NOMBRE]
   - Teléfonos → [TELEFONO]
   - Cédulas de identidad / documentos → [CI]
   - Direcciones postales/domicilios → [DIRECCIÓN]
   - Ciudades y localidades → [UBICACIÓN]
   - Números de registro/historia clínica → [REGISTRO]

2) Conserva TODO lo demás sin cambios: síntomas, diagnósticos, dosis,
   resultados, unidades, abreviaturas.

3) Títulos y roles: conserva el título y reemplaza solo el nombre.
   Ej.: "Dr. [NOMBRE]", "AE. [NOMBRE]"

4) Devuelve ÚNICAMENTE el texto anonimizado, sin explicaciones.
```

### Configuración del Modelo

```python
payload = {
    "prompt": prompt,
    "n_predict": 2000,
    "temperature": 0.3,    # Baja para consistencia
    "top_k": 40,
    "top_p": 0.9
}
```

## Métricas de Evaluación

### Rendimiento

| Métrica | Descripción |
|---------|-------------|
| **TPS** | Tokens por segundo generados |
| **Tiempo total** | Milisegundos por request |
| **Tokens generados** | Cantidad de tokens en respuesta |

### Calidad de Anonimización

| Métrica | Descripción | Objetivo |
|---------|-------------|----------|
| **Precisión** | PHI correctamente detectado | >95% |
| **Recall** | PHI no omitido | >90% |
| **Preservación** | Datos clínicos intactos | 100% |

## Resultados Finales del Experimento (Dic 2025)

### 6 Modelos Evaluados (Tarea de Anonimización)

| Modelo | Puerto | TPS | Calidad | Resultado |
|--------|--------|-----|---------|-----------|
| **Llama-3.1-8B** | 8094 | 4.34 | ★★★★★ | **BEST FIT** - 100% Recall, 100% LRDI con Baseline |
| **Gemma-2-9B** | 8095 | 3.1 | ★★★★☆ | 96.67% Recall, 100% LRDI con Structured Output |
| **Mistral-7B** | 8088 | 4.6 | ★★★★☆ | 96.67% Recall, 100% LRDI con Structured Output |
| **Phi-3.5-mini** | 8093 | 6.1 | ★★★☆☆ | 73.33% Recall, LRDI 78.6% |
| **Qwen2.5-1.5B** | 8089 | 13.3 | ★★☆☆☆ | 73.33% Recall, LRDI 70.2% |
| Qwen2.5-14B | 8096 | — | ❌ | Excluido: latencia >6 minutos por documento |

### Respuestas Detalladas

#### Llama-3.1-8B (BEST FIT)

Llama-3.1-8B alcanzó **100% Recall** y **100% LRDI** con el prompt más simple (Baseline).
Es el único modelo que logra "Fuga Cero" sin necesidad de prompts complejos.
Procesamiento de historias clínicas estándar en menos de 2 minutos (4.34 TPS).

```
Nombre: [NOMBRE]
Documento: [CI]
Ciudad: [UBICACIÓN]
Dirección: [DIRECCIÓN]
Registro: [REGISTRO]

Evolución médica:
Paciente bajo dexmedetomidina + quetiapina + BZD, vigil.
Responsables: Dr. [NOMBRE], Dras. [NOMBRE], [NOMBRE].
AE. [NOMBRE], LE. [NOMBRE]
```

✅ Detectó TODOS los nombres (pacientes, médicos, enfermeros)
✅ Detectó CI, direcciones, ciudades, registros
✅ Preservó datos clínicos intactos
✅ LRDI 100% (cero fuga de identificadores directos)

#### Gemma-2-9B y Mistral-7B (Excelentes)

Ambos modelos alcanzan 96.67% Recall y 100% LRDI, pero requieren el prompt `structured_output` para lograrlo. Son alternativas viables cuando se necesita más velocidad que Llama.

### Selección de Modelos - Justificación (Evaluación Final)

| Modelo | Resultado | Justificación | Fuente |
|--------|-----------|---------------|--------|
| **Llama-3.1-8B** | **BEST FIT** | 100% Recall, 100% LRDI con Baseline | [Meta](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct) |
| **Gemma-2-9B** | Excelente | 96.67% Recall, 100% LRDI con Structured Output | [Google](https://huggingface.co/google/gemma-2-9b-it) |
| **Mistral-7B** | Excelente | 96.67% Recall, 100% LRDI con Structured Output | [Mistral AI](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3) |
| **Phi-3.5-mini** | Aceptable | 73.33% Recall, LRDI 78.6% - LRDI insuficiente | [Microsoft](https://huggingface.co/microsoft/Phi-3.5-mini-instruct) |
| **Qwen2.5-1.5B** | Insuficiente | 73.33% Recall, LRDI 70.2% - Mayor velocidad pero riesgo de fuga | [Alibaba](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) |
| **Qwen2.5-14B** | Excluido | Latencia >6 minutos por documento | [Alibaba](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct) |

### Ejemplo de Salida Esperada

**Entrada:**
```
Nombre:
OLAF RASMUSEN JAKOBSEN
Documento: 2.156.983-0
Ciudad:
MONTEVIDEO
Dirección:
SALTO 3
...
Responsables del registro:
AE. M. Brown
LE. J. Bremmerman
```

**Salida esperada:**
```
Nombre:
[NOMBRE]
Documento: [CI]
Ciudad:
[UBICACIÓN]
Dirección:
[DIRECCIÓN]
...
Responsables del registro:
AE. [NOMBRE]
LE. [NOMBRE]
```

## Interpretación de Resultados

### TPS (Tokens Por Segundo) - Tarea de Anonimización

| Rango TPS | Evaluación | Recomendación |
|-----------|------------|---------------|
| >10 | Excelente | Óptimo para batch processing |
| 5-10 | Bueno | Adecuado para producción |
| 3-5 | Aceptable | Viable para procesos batch |
| <3 | Bajo | Solo para casos específicos |

> **Nota**: Los TPS de la tarea de anonimización (3-13 TPS) son menores que el benchmark puro de rendimiento (14.98 TPS) debido a la complejidad del prompt y la longitud de los documentos clínicos.

### Validación de Anonimización

Verificar manualmente en la primera respuesta:
1. ✅ `OLAF RASMUSEN JAKOBSEN` → `[NOMBRE]`
2. ✅ `2.156.983-0` → `[CI]`
3. ✅ `MONTEVIDEO` → `[UBICACIÓN]`
4. ✅ `SALTO 3` → `[DIRECCIÓN]`
5. ✅ `658974` → `[REGISTRO]`
6. ✅ Nombres de médicos → `[NOMBRE]`
7. ✅ Datos clínicos preservados (diagnósticos, dosis, resultados)

## Troubleshooting

### Error: Connection refused

```bash
# Verificar que el servidor está corriendo
docker ps
curl http://localhost:8089/health
```

### Baja calidad de anonimización

- Verificar que se usa `temperature: 0.3`
- Aumentar `n_predict` si el texto se corta
- Usar Llama-3.1-8B con prompt `baseline` para máxima calidad (Best Fit)

### TPS muy bajo

- Reducir `n_predict` si no es necesario
- Verificar carga del sistema con `htop`
- Asegurar que MMA está activo

## Referencias

- [llama.cpp API](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md)
- [HIPAA De-identification](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
- [Ley 18.331 - Protección de Datos Personales (Uruguay)](https://www.impo.com.uy/bases/leyes/18331-2008)
