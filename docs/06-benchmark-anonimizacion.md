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

## Resultados Esperados

### Comparativa de Modelos

| Modelo | TPS Esperado | Calidad Anonimización |
|--------|--------------|----------------------|
| **Qwen2.5-7B** | ~15-20 | Muy buena |
| **Mistral-7B** | ~18-22 | Buena |
| **Llama-3.1-8B** | ~14-18 | Excelente (medicina) |

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

### TPS (Tokens Por Segundo)

| Rango TPS | Evaluación | Recomendación |
|-----------|------------|---------------|
| >20 | Excelente | Óptimo para producción |
| 15-20 | Bueno | Adecuado |
| 10-15 | Aceptable | Considerar optimización |
| <10 | Bajo | Revisar configuración |

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
- Probar con Llama 3.1 para mejor comprensión médica

### TPS muy bajo

- Reducir `n_predict` si no es necesario
- Verificar carga del sistema con `htop`
- Asegurar que MMA está activo

## Referencias

- [llama.cpp API](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md)
- [HIPAA De-identification](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
- [Ley 18.331 - Protección de Datos Personales (Uruguay)](https://www.impo.com.uy/bases/leyes/18331-2008)
