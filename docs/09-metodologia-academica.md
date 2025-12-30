# Metodología Académica - Benchmark de Anonimización con LLMs

**Universidad de Montevideo - Tesis 2025**

## Objetivo Principal de la Tesis

**Demostrar que los aceleradores MMA (Matrix Math Accelerator) integrados en IBM Power10 representan una capacidad subutilizada que, al ser activada, proporciona ganancia de rendimiento cuantificable para inferencia de IA Generativa on-premise.**

La anonimización de datos clínicos es el **caso de uso** para validar esta hipótesis, NO el objetivo principal de la investigación.

---

## Papers de Referencia

Esta metodología se basa en dos papers académicos recientes:

### 1. LLMs-in-the-Loop Part 2 (arXiv:2412.10918)

**Título completo:** "LLMs-in-the-Loop Part 2: Expert Small AI Models for Anonymization and De-identification of PHI Across Multiple Languages"

**Aportes clave:**
- Metodología de evaluación multilingüe para des-identificación PHI
- F1-micro score de 0.978 en español
- 18 categorías PHI basadas en i2b2 2014 De-identification Challenge
- Evaluación con modelos pequeños (2-8B parámetros)

**Métricas adoptadas:**
- Precision, Recall, F1-micro, F1-macro
- Evaluación por categoría PHI
- Distinción entre identificadores directos y cuasi-identificadores

### 2. Unlocking LLMs for Clinical Text Anonymization (arXiv:2406.00062)

**Título completo:** "Unlocking the Potential of Large Language Models for Clinical Text Anonymization: A Comparative Study"

**Aportes clave:**
- 6 métricas de evaluación específicas para anonimización
- Métricas basadas en distancia de Levenshtein
- Evaluación de retención de utilidad clínica

**Métricas adoptadas:**
- **ALID:** Average Levenshtein Index of Dissimilarity
- **LR:** Levenshtein Recall (threshold 0.85)
- **LRDI:** LR para Identificadores Directos (todo o nada)
- **LRQI:** LR para Cuasi-Identificadores (proporcional)

---

## Categorías PHI (i2b2 2014)

Basado en el i2b2 2014 De-identification Challenge, adaptado al contexto uruguayo:

### Identificadores Directos (Críticos - LRDI = 100%)

| Categoría | Descripción | Placeholder |
|-----------|-------------|-------------|
| NAME_PATIENT | Nombre del paciente | [NOMBRE] |
| NAME_DOCTOR | Nombre del médico | [NOMBRE] |
| NAME_NURSE | Nombre enfermero/a | [NOMBRE] |
| NAME_FAMILY | Nombre de familiar | [NOMBRE] |
| ID_CI | Cédula de Identidad (x.xxx.xxx-x) | [CI] |
| ID_MEDICAL_RECORD | Historia clínica | [REGISTRO] |
| CONTACT_PHONE_MOBILE | Celular (09x-xxx-xxx) | [TELEFONO] |
| CONTACT_PHONE_FIXED | Teléfono fijo | [TELEFONO] |
| CONTACT_EMAIL | Correo electrónico | [EMAIL] |

### Cuasi-Identificadores (LRQI proporcional)

| Categoría | Descripción | Placeholder |
|-----------|-------------|-------------|
| LOCATION_STREET | Dirección (calle y número) | [DIRECCION] |
| LOCATION_CITY | Ciudad | [UBICACION] |
| LOCATION_DEPARTMENT | Departamento (19 de Uruguay) | [UBICACION] |
| LOCATION_HOSPITAL | Hospital/Sanatorio | [UBICACION] |
| LOCATION_MUTUALISTA | Mutualista | [UBICACION] |
| DATE_ADMISSION | Fecha de ingreso | [FECHA] |
| DATE_DISCHARGE | Fecha de alta | [FECHA] |
| DATE_BIRTH | Fecha de nacimiento | [FECHA] |
| AGE | Edad (>89 según HIPAA) | [EDAD] |
| PROFESSION | Profesión/ocupación | [PROFESION] |

---

## Métricas de Evaluación

### Métricas de Rendimiento (Objetivo Principal: MMA)

| Métrica | Descripción | Unidad |
|---------|-------------|--------|
| TPS (generation) | Tokens por segundo en generación | tokens/s |
| TPS (prompt eval) | Tokens por segundo evaluando prompt | tokens/s |
| Latencia primer token | Tiempo hasta primer token | ms |
| Latencia total | Tiempo total de inferencia | ms |
| CPU utilization | Uso de CPU durante inferencia | % |
| RAM usage | Memoria utilizada | GB |

### Métricas de Calidad (Caso de Uso)

#### Métricas Estándar (Paper 2412.10918)

```
Precision = TP / (TP + FP)
Recall = TP / (TP + FN)  # Crítico para privacidad
F1-micro = 2 * (Precision * Recall) / (Precision + Recall)
F1-macro = promedio(F1 por categoría)
```

#### Métricas Levenshtein (Paper 2406.00062)

```
ALID = 1 - similitud_levenshtein(original, anonimizado)
LR = 1 si ALID >= 0.85, else 0
LRDI = 100% si TODOS los identificadores directos fueron anonimizados
LRQI = porcentaje de cuasi-identificadores anonimizados
```

---

## Dataset de Evaluación

### Casos Clínicos Sintéticos (10 casos)

| ID | Tipo | Especialidad | Entidades PHI | Tokens Est. | Complejidad |
|----|------|--------------|---------------|-------------|-------------|
| A1 | Emergencia | Cardiología | 15 | ~200 | Media |
| A2 | Consulta | Oncología | 12 | ~150 | Media |
| A3 | Evolución CTI | Intensivo | 25 | ~400 | Alta |
| A4 | Alta médica | Cirugía | 18 | ~300 | Media |
| A5 | Interconsulta | Neurología | 14 | ~180 | Media |
| B1 | Epicrisis | Medicina Interna | 20 | ~500 | Alta |
| B2 | Resumen | Pediatría | 16 | ~220 | Media |
| B3 | Nota operatoria | Traumatología | 22 | ~450 | Alta |
| C1 | Historia completa | Psiquiatría | 30 | ~800 | Muy Alta |
| C2 | Multi-evolución | General | 35 | ~1000 | Muy Alta |

### Características del Dataset

- **Idioma:** Español (Uruguay)
- **Terminología:** Adaptada al contexto uruguayo (mutualistas, ASSE, departamentos)
- **Ground Truth:** Cada caso incluye lista de entidades PHI anotadas manualmente
- **Diversidad:** Múltiples especialidades y tipos de documentos clínicos

---

## Modelos a Evaluar

| Modelo | Parámetros | Puerto | Cuantización | Justificación |
|--------|------------|--------|--------------|---------------|
| Phi-3.5-mini | 3.5B | 8093 | Q4_K_M | Mejor velocidad previa (16.8 TPS) |
| Mistral-Nemo-12B | 12B | 8097 | Q4_K_M | Mejor calidad previa (100% detección) |
| Qwen2.5-7B | 7B | 8089 | Q4_K_M | Balance velocidad/calidad |
| BioMistral-7B | 7B | 8092 | Q4_K_M | Especializado dominio médico |
| Llama-3.1-8B | 8B | 8094 | Q4_K_M | Referencia paper 2406.00062 |
| Gemma-2-9B | 9B | 8095 | Q4_K_M | Alternativa arquitectura |

---

## Estrategias de Prompting (8 variantes)

| ID | Estrategia | Descripción | Tokens Prompt |
|----|------------|-------------|---------------|
| baseline | Zero-Shot Simple | Instrucción mínima | ~80 |
| detailed | Zero-Shot Detallado | 8 reglas + categorías PHI | ~350 |
| few_shot | Few-Shot (3 ejemplos) | Ejemplos input/output | ~300 |
| chain_of_thought | Chain of Thought | Razonamiento paso a paso | ~250 |
| master_tutor | Master Prompt | Prompt del protocolo tutor | ~120 |
| medico | Médico Especializado | Enfoque Ley 18.331 Uruguay | ~280 |
| structured_output | Structured Output | Categorías PHI explícitas | ~200 |
| hybrid | Hybrid (Few-Shot + CoT) | Combina ejemplos + razonamiento | ~450 |

---

## Diseño Experimental

### Experimento 1: Benchmark de Rendimiento MMA

**Objetivo:** Cuantificar ganancia de rendimiento con MMA activo.

**Variables:**
- 6 modelos × 10 casos × 3 iteraciones = 180 ejecuciones

**Métricas:**
- TPS (generación y evaluación de prompt)
- Latencia (primer token y total)
- Uso de CPU y RAM
- Estabilidad (desviación estándar)

**Output:** Tabla comparativa de rendimiento por modelo.

### Experimento 2: Comparativa de Prompts

**Objetivo:** Determinar mejor estrategia de prompting.

**Variables:**
- 8 prompts × top 2 modelos × 10 casos = 160 ejecuciones

**Métricas:**
- F1-micro, Recall
- Tiempo de respuesta
- Tokens generados

**Output:** Ranking de prompts por calidad/velocidad.

### Experimento 3: Evaluación de Calidad

**Objetivo:** Validar calidad con métricas académicas.

**Variables:**
- Top 3 modelos × top 3 prompts × 10 casos × 5 iteraciones = 450 ejecuciones

**Métricas:**
- Precision, Recall, F1-micro, F1-macro
- ALID, LR, LRDI, LRQI

**Output:** Tabla de métricas estilo paper académico.

---

## Comparativa GPU (Contextualización)

| Plataforma | TPS Est. | Speedup vs Power10 | Costo/hora | Privacidad |
|------------|----------|-------------------|------------|------------|
| **IBM Power10 (MMA)** | 13-17 | 1.0x (baseline) | $0 on-prem | Total |
| Nvidia T4 (AWS) | 20-25 | ~1.5x | $0.526 | Cloud |
| Nvidia A10G (AWS) | 40-50 | ~3x | $1.212 | Cloud |
| Nvidia A100 (GCP) | 80-120 | ~7x | $3.67 | Cloud |
| RTX 4090 (Local) | 100-150 | ~10x | CapEx ~$1600 | Local |

### Argumento "Best Fit"

> "Aunque GPUs cloud son 2-7x más rápidas, Power10 on-premises elimina el riesgo de fuga de datos PHI y cumple automáticamente con Ley 18.331 (Uruguay). El rendimiento de 13-17 TPS es **suficiente** para procesos batch y flujos donde la latencia extrema no es crítica."

---

## Referencias

1. Gunay, M., Keles, B., & Hizlan, R. (2024). *LLMs-in-the-Loop Part 2: Expert Small AI Models for Anonymization and De-identification of PHI Across Multiple Languages*. arXiv:2412.10918

2. Pissarra, D., et al. (2024). *Unlocking the Potential of Large Language Models for Clinical Text Anonymization: A Comparative Study*. PrivateNLP Workshop, ACL 2024. arXiv:2406.00062

3. Stubbs, A., Uzuner, Ö., Kotfila, C., Goldstein, I., & Szolovits, P. (2015). *Challenges in Synthesizing Surrogate PHI in Narrative EMRs*. AMIA Annual Symposium.

4. i2b2 2014 De-identification Challenge - 1,304 notas clínicas longitudinales

5. Simon, T., et al. (2024). *IBM Power E1080 Technical Overview*. IBM Redbooks.

6. Ley 18.331 de Uruguay - Protección de Datos Personales y Acción de Habeas Data
