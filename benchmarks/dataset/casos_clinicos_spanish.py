#!/usr/bin/env python3
"""
casos_clinicos_spanish.py - Dataset expandido de casos clínicos para benchmark
Universidad de Montevideo - Tesis 2025

Basado en metodología de:
- arXiv:2412.10918 (LLMs-in-the-Loop Part 2)
- arXiv:2406.00062 (Unlocking LLMs for Clinical Text Anonymization)
- i2b2 2014 De-identification Challenge

Contiene 10+ casos clínicos sintéticos con ground truth anotado según
categorías PHI adaptadas a Uruguay (Ley 18.331).
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# =============================================================================
# CATEGORÍAS PHI (basado en i2b2 2014, adaptado a Uruguay)
# =============================================================================

class PHICategory(Enum):
    """Categorías de Protected Health Information según i2b2 2014."""
    # Identificadores Directos
    NAME_PATIENT = "NAME_PATIENT"
    NAME_DOCTOR = "NAME_DOCTOR"
    NAME_NURSE = "NAME_NURSE"
    NAME_FAMILY = "NAME_FAMILY"
    ID_CI = "ID_CI"  # Cédula de Identidad Uruguay
    ID_MEDICAL_RECORD = "ID_MEDICAL_RECORD"
    ID_CARNE_SALUD = "ID_CARNE_SALUD"
    CONTACT_PHONE = "CONTACT_PHONE"
    CONTACT_EMAIL = "CONTACT_EMAIL"

    # Cuasi-Identificadores
    LOCATION_STREET = "LOCATION_STREET"
    LOCATION_CITY = "LOCATION_CITY"
    LOCATION_DEPARTMENT = "LOCATION_DEPARTMENT"
    LOCATION_HOSPITAL = "LOCATION_HOSPITAL"
    LOCATION_ORGANIZATION = "LOCATION_ORGANIZATION"
    DATE_ADMISSION = "DATE_ADMISSION"
    DATE_DISCHARGE = "DATE_DISCHARGE"
    DATE_BIRTH = "DATE_BIRTH"
    DATE_PROCEDURE = "DATE_PROCEDURE"
    PROFESSION = "PROFESSION"
    AGE = "AGE"


@dataclass
class PHIEntity:
    """Representa una entidad PHI en el texto."""
    category: PHICategory
    value: str
    start_pos: int  # Posición inicial en el texto
    end_pos: int    # Posición final en el texto
    context: str    # Descripción del contexto
    is_direct: bool # True si es identificador directo


# =============================================================================
# CASO A1: EMERGENCIA CARDIOLOGÍA
# =============================================================================

CASO_A1_TEXTO = """HOSPITAL DE CLÍNICAS - SERVICIO DE EMERGENCIA
Fecha de ingreso: 15/11/2024 - Hora: 03:47

DATOS DEL PACIENTE:
Nombre: Roberto Carlos Méndez Aguilar
Documento: 3.847.291-6
Edad: 58 años
Sexo: Masculino
Domicilio: Bulevar Artigas 2847, apto 302
Ciudad: Montevideo
Teléfono: 099 847 231
Historia Clínica N°: HC-2024-48721

MOTIVO DE CONSULTA:
Dolor precordial opresivo de 2 horas de evolución, irradiado a brazo izquierdo y mandíbula. Diaforesis profusa. Náuseas sin vómitos.

ANTECEDENTES PERSONALES:
- HTA en tratamiento con Enalapril 10mg c/12hs
- Dislipemia - Atorvastatina 20mg/noche
- Tabaquista activo (25 paquetes/año)
- Padre fallecido por IAM a los 62 años

EXAMEN FÍSICO:
PA: 160/95 mmHg | FC: 98 lpm | FR: 22 rpm | SatO2: 94% AA
Paciente sudoroso, pálido, ansioso.
CV: R1R2 en 4 focos, sin soplos.
PP: MV conservado bilateral.

PARACLÍNICA:
- ECG: Supradesnivel ST en V1-V4 de 3mm
- Troponinas: 2.5 ng/mL (VN <0.04)

CONDUCTA:
1. AAS 300mg VO (administrado por móvil SEMM)
2. Clopidogrel 600mg carga
3. Heparina sódica 5000 UI IV bolo
4. Contacto con Hemodinamia - Dra. María Fernanda Sosa confirma disponibilidad
5. Traslado urgente a Sala de Cateterismo

Responsable del registro:
Dr. Alejandro Martínez Vidal
Médico de Guardia - CI 1.892.445-3"""

CASO_A1_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Roberto Carlos Méndez Aguilar", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "3.847.291-6", "context": "cédula de identidad", "is_direct": True},
    {"category": "LOCATION_STREET", "value": "Bulevar Artigas 2847, apto 302", "context": "domicilio", "is_direct": False},
    {"category": "LOCATION_CITY", "value": "Montevideo", "context": "ciudad", "is_direct": False},
    {"category": "CONTACT_PHONE", "value": "099 847 231", "context": "teléfono móvil", "is_direct": True},
    {"category": "ID_MEDICAL_RECORD", "value": "HC-2024-48721", "context": "historia clínica", "is_direct": True},
    {"category": "DATE_ADMISSION", "value": "15/11/2024", "context": "fecha ingreso", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL DE CLÍNICAS", "context": "institución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "María Fernanda Sosa", "context": "médico hemodinamia", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Alejandro Martínez Vidal", "context": "médico guardia", "is_direct": True},
    {"category": "ID_CI", "value": "1.892.445-3", "context": "CI médico", "is_direct": True},
    {"category": "LOCATION_ORGANIZATION", "value": "SEMM", "context": "servicio emergencia", "is_direct": False},
]


# =============================================================================
# CASO A2: CONSULTA ONCOLOGÍA
# =============================================================================

CASO_A2_TEXTO = """ASOCIACIÓN ESPAÑOLA - SERVICIO DE ONCOLOGÍA
Fecha: 20/10/2024

PACIENTE: Ana María Rodríguez Ferreira
CI: 2.156.873-4
Edad: 54 años
Procedencia: Salto
Domicilio: Calle Uruguay 456, esq. Brasil
Teléfono: 473-25890
HC: ON-2024-1234

DIAGNÓSTICO:
Carcinoma Ductal Infiltrante de mama izquierda, diagnosticado en marzo 2024.
Estadio IIA (T2N0M0). RE+, RP+, HER2-.

ESTUDIOS DE CONTROL:
TAC tórax-abdomen-pelvis (15/10/2024): Sin evidencia de enfermedad metastásica.
Mamografía bilateral: Sin hallazgos sospechosos.
Marcadores tumorales: CA 15-3: 18 U/mL (VN <30)

TRATAMIENTO ACTUAL:
- Tamoxifeno 20mg/día (inicio: abril 2024)
- Calcio + Vitamina D

CONDUCTA:
Continuar tratamiento hormonal por 5 años.
Control en 3 meses con marcadores y mamografía.

FAMILIAR RESPONSABLE:
Esposo: Juan Carlos Rodríguez
Cel: 099-888-777

Médico tratante:
Dra. Valentina Gutiérrez Oreggioni
Oncóloga - Reg. MSP 45678"""

CASO_A2_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Ana María Rodríguez Ferreira", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "2.156.873-4", "context": "cédula paciente", "is_direct": True},
    {"category": "LOCATION_CITY", "value": "Salto", "context": "procedencia", "is_direct": False},
    {"category": "LOCATION_STREET", "value": "Calle Uruguay 456, esq. Brasil", "context": "domicilio", "is_direct": False},
    {"category": "CONTACT_PHONE", "value": "473-25890", "context": "teléfono fijo", "is_direct": True},
    {"category": "ID_MEDICAL_RECORD", "value": "ON-2024-1234", "context": "historia clínica", "is_direct": True},
    {"category": "DATE_PROCEDURE", "value": "20/10/2024", "context": "fecha consulta", "is_direct": False},
    {"category": "DATE_PROCEDURE", "value": "15/10/2024", "context": "fecha TAC", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "ASOCIACIÓN ESPAÑOLA", "context": "institución", "is_direct": False},
    {"category": "NAME_FAMILY", "value": "Juan Carlos Rodríguez", "context": "familiar", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "099-888-777", "context": "teléfono familiar", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Valentina Gutiérrez Oreggioni", "context": "oncóloga", "is_direct": True},
]


# =============================================================================
# CASO A3: EVOLUCIÓN CTI
# =============================================================================

CASO_A3_TEXTO = """CTI - HOSPITAL MACIEL
Fecha: 22/11/2024 - Hora: 08:00

PACIENTE: Fernando José Acosta Píriz
CI: 1.987.654-2
Edad: 67 años
Cama: CTI-12
HC: 2024-CTI-789
Día de internación: 8

DIAGNÓSTICOS:
1. Neumonía grave adquirida en la comunidad
2. SDRA moderado
3. Shock séptico en resolución
4. Diabetes tipo 2

EVOLUCIÓN:
Paciente en VMI modo PSV 12/5, FiO2 0.4, SatO2 96%.
Hemodinámicamente estable sin vasoactivos desde hace 24hs.
Afebril. Glasgow 11 (O4V2M5) bajo sedación mínima.
Diuresis 1.8 ml/kg/h con furosemide 20mg c/8hs.

LABORATORIO (22/11/2024):
- Leucocitos: 11.500 (mejorando)
- PCR: 85 mg/L (descendiendo)
- Procalcitonina: 0.8 ng/mL
- Creatinina: 1.2 mg/dL
- Glicemia: 145 mg/dL

PLAN:
1. Continuar ATB: Piperacilina-Tazobactam día 6/7
2. Weaning progresivo de VMI
3. Iniciar KTR
4. Control de glicemia con insulina según protocolo

Pase de guardia con Dr. Rodríguez Hermida.
Interconsulta pendiente con Neumología - Dr. Martín Fernández.
Se llama a esposa Sra. Carmen Díaz al 094-567-890 para informar evolución.

Responsables:
Dra. Lucía Gómez Pereira - CTI
LE. Patricia Núñez - Enfermería
Domicilio familiar: Av. 8 de Octubre 3456, Montevideo"""

CASO_A3_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Fernando José Acosta Píriz", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "1.987.654-2", "context": "cédula paciente", "is_direct": True},
    {"category": "ID_MEDICAL_RECORD", "value": "2024-CTI-789", "context": "historia clínica", "is_direct": True},
    {"category": "DATE_PROCEDURE", "value": "22/11/2024", "context": "fecha evolución", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL MACIEL", "context": "institución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "Rodríguez Hermida", "context": "médico guardia", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Martín Fernández", "context": "neumólogo", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Carmen Díaz", "context": "esposa", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "094-567-890", "context": "teléfono familiar", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Lucía Gómez Pereira", "context": "médica CTI", "is_direct": True},
    {"category": "NAME_NURSE", "value": "Patricia Núñez", "context": "enfermera", "is_direct": True},
    {"category": "LOCATION_STREET", "value": "Av. 8 de Octubre 3456", "context": "domicilio familiar", "is_direct": False},
    {"category": "LOCATION_CITY", "value": "Montevideo", "context": "ciudad", "is_direct": False},
]


# =============================================================================
# CASO A4: ALTA MÉDICA CIRUGÍA
# =============================================================================

CASO_A4_TEXTO = """SANATORIO AMERICANO - CIRUGÍA GENERAL
EPICRISIS DE ALTA

Paciente: María Elena Suárez Bentancor
CI: 4.321.098-7
Edad: 45 años
Domicilio: Rbla. Rep. Argentina 1234, apto 501
Ciudad: Punta del Este
Departamento: Maldonado
Tel: 042-445566
Email: mesuarez@gmail.com
HC: CG-2024-5678

FECHA INGRESO: 18/11/2024
FECHA ALTA: 24/11/2024
DÍAS DE INTERNACIÓN: 6

DIAGNÓSTICO PREOPERATORIO:
Colecistitis aguda litiásica

PROCEDIMIENTO REALIZADO (19/11/2024):
Colecistectomía laparoscópica sin incidentes.
Equipo quirúrgico: Dr. Carlos Pérez Aguirre (cirujano principal)
                   Dra. Andrea Silva (ayudante)
                   Dr. Gonzalo Martínez (anestesista)

EVOLUCIÓN POSTOPERATORIA:
Buena evolución. Tolerancia oral progresiva.
Heridas operatorias sin signos de infección.
Afebril durante toda la internación.

INDICACIONES AL ALTA:
1. Reposo relativo 7 días
2. Dieta blanda, progresiva a normal
3. Paracetamol 1g c/8hs dolor
4. Ibuprofeno 400mg c/8hs si precisa
5. Control en 7 días en policlínica

FAMILIAR ACOMPAÑANTE:
Hija: Laura Fernández Suárez
Tel: 099-123-456

Firma: Dr. Carlos Pérez Aguirre
Cirujano General - Reg. MSP 34521"""

CASO_A4_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "María Elena Suárez Bentancor", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "4.321.098-7", "context": "cédula paciente", "is_direct": True},
    {"category": "LOCATION_STREET", "value": "Rbla. Rep. Argentina 1234, apto 501", "context": "domicilio", "is_direct": False},
    {"category": "LOCATION_CITY", "value": "Punta del Este", "context": "ciudad", "is_direct": False},
    {"category": "LOCATION_DEPARTMENT", "value": "Maldonado", "context": "departamento", "is_direct": False},
    {"category": "CONTACT_PHONE", "value": "042-445566", "context": "teléfono fijo", "is_direct": True},
    {"category": "CONTACT_EMAIL", "value": "mesuarez@gmail.com", "context": "email", "is_direct": True},
    {"category": "ID_MEDICAL_RECORD", "value": "CG-2024-5678", "context": "historia clínica", "is_direct": True},
    {"category": "DATE_ADMISSION", "value": "18/11/2024", "context": "fecha ingreso", "is_direct": False},
    {"category": "DATE_DISCHARGE", "value": "24/11/2024", "context": "fecha alta", "is_direct": False},
    {"category": "DATE_PROCEDURE", "value": "19/11/2024", "context": "fecha cirugía", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "SANATORIO AMERICANO", "context": "institución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "Carlos Pérez Aguirre", "context": "cirujano", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Andrea Silva", "context": "ayudante", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Gonzalo Martínez", "context": "anestesista", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Laura Fernández Suárez", "context": "hija", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "099-123-456", "context": "teléfono familiar", "is_direct": True},
]


# =============================================================================
# CASO A5: INTERCONSULTA NEUROLOGÍA
# =============================================================================

CASO_A5_TEXTO = """MÉDICA URUGUAYA - NEUROLOGÍA
INFORME DE INTERCONSULTA

Fecha: 25/11/2024
Solicitante: Dra. Carolina Méndez (Medicina Interna)

DATOS DEL PACIENTE:
Nombre: Jorge Luis Fernández Castro
CI: 3.654.987-1
Edad: 72 años
Procedencia: Flores
HC: MU-2024-9876

MOTIVO DE CONSULTA:
Valoración por cuadro confusional de 48hs de evolución.

ANTECEDENTES:
- HTA
- FA crónica anticoagulada con Warfarina
- ACV isquémico en 2019

EXAMEN NEUROLÓGICO:
Vigil, desorientado en tiempo y espacio.
Lenguaje: fluente, sin afasia.
Pares craneales: sin alteraciones.
Motor: hemiparesia braquiocrural derecha secuelar.
NIHSS: 4 puntos.

ESTUDIOS:
TAC cráneo (25/11/2024): Sin lesiones agudas. Leucoaraiosis moderada.
INR: 2.8

IMPRESIÓN DIAGNÓSTICA:
Síndrome confusional agudo. Descartar infección urinaria vs causa metabólica.

RECOMENDACIONES:
1. Urocultivo + sedimento
2. Ionograma, función renal, hepatograma
3. Mantener anticoagulación
4. Evitar benzodiacepinas
5. Re-evaluación en 48hs

Dr. Mauricio Rodríguez Brum
Neurólogo - Reg. MSP 56789
Contacto: mrodriguez@medicauruguaya.com.uy"""

CASO_A5_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Jorge Luis Fernández Castro", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "3.654.987-1", "context": "cédula paciente", "is_direct": True},
    {"category": "LOCATION_CITY", "value": "Flores", "context": "procedencia", "is_direct": False},
    {"category": "ID_MEDICAL_RECORD", "value": "MU-2024-9876", "context": "historia clínica", "is_direct": True},
    {"category": "DATE_PROCEDURE", "value": "25/11/2024", "context": "fecha interconsulta", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "MÉDICA URUGUAYA", "context": "institución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "Carolina Méndez", "context": "médica solicitante", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Mauricio Rodríguez Brum", "context": "neurólogo", "is_direct": True},
    {"category": "CONTACT_EMAIL", "value": "mrodriguez@medicauruguaya.com.uy", "context": "email médico", "is_direct": True},
]


# =============================================================================
# CASO B1: EPICRISIS MEDICINA INTERNA
# =============================================================================

CASO_B1_TEXTO = """HOSPITAL PASTEUR - MEDICINA INTERNA
EPICRISIS

DATOS DE IDENTIFICACIÓN:
Paciente: Ricardo Daniel Olivera Techera
CI: 2.789.456-3
Fecha de nacimiento: 15/03/1955
Edad: 69 años
Domicilio: Camino Maldonado 5678, Barrio Carrasco
Ciudad: Montevideo
Teléfonos: Fijo 2601-5678, Cel 091-234-567
Prestador: ASSE
HC: HP-2024-12345

PERÍODO DE INTERNACIÓN:
Ingreso: 10/11/2024
Alta: 28/11/2024
Días de internación: 18

DIAGNÓSTICOS AL INGRESO:
1. Insuficiencia cardíaca descompensada (FEVI 35%)
2. Diabetes tipo 2 mal controlada
3. Enfermedad renal crónica estadio 3b
4. Fibrilación auricular permanente

EVOLUCIÓN:
Paciente ingresa por disnea progresiva clase funcional III-IV, edemas en MMII y oliguria.
Se inicia tratamiento con furosemide IV, restricción hidrosalina y ajuste de anticoagulación.
Evoluciona favorablemente con balance negativo progresivo.
Se realiza ecocardiograma (15/11/2024): FEVI 38%, IM moderada, HTP leve.
Valorado por Cardiología (Dr. Fernando González) y Nefrología (Dra. Mónica Pérez).

TRATAMIENTO AL ALTA:
1. Furosemide 40mg c/12hs
2. Carvedilol 12.5mg c/12hs
3. Enalapril 10mg c/12hs
4. Espironolactona 25mg/día
5. Warfarina según INR (objetivo 2-3)
6. Metformina 850mg c/12hs
7. Insulina NPH 20 UI noche

CONTROLES:
- Policlínica Cardiología en 7 días
- Laboratorio (INR, función renal) en 3 días
- Peso diario, restringir líquidos 1.5L/día

FAMILIAR DE REFERENCIA:
Esposa: Marta Lucía Rodríguez
Tel: 099-876-543

Médico responsable:
Dr. Pablo Martín Sánchez Aguiar
Medicina Interna - Reg. MSP 23456"""

CASO_B1_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Ricardo Daniel Olivera Techera", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "2.789.456-3", "context": "cédula paciente", "is_direct": True},
    {"category": "DATE_BIRTH", "value": "15/03/1955", "context": "fecha nacimiento", "is_direct": False},
    {"category": "LOCATION_STREET", "value": "Camino Maldonado 5678, Barrio Carrasco", "context": "domicilio", "is_direct": False},
    {"category": "LOCATION_CITY", "value": "Montevideo", "context": "ciudad", "is_direct": False},
    {"category": "CONTACT_PHONE", "value": "2601-5678", "context": "teléfono fijo", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "091-234-567", "context": "teléfono móvil", "is_direct": True},
    {"category": "LOCATION_ORGANIZATION", "value": "ASSE", "context": "prestador salud", "is_direct": False},
    {"category": "ID_MEDICAL_RECORD", "value": "HP-2024-12345", "context": "historia clínica", "is_direct": True},
    {"category": "DATE_ADMISSION", "value": "10/11/2024", "context": "fecha ingreso", "is_direct": False},
    {"category": "DATE_DISCHARGE", "value": "28/11/2024", "context": "fecha alta", "is_direct": False},
    {"category": "DATE_PROCEDURE", "value": "15/11/2024", "context": "fecha eco", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL PASTEUR", "context": "institución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "Fernando González", "context": "cardiólogo", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Mónica Pérez", "context": "nefróloga", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Marta Lucía Rodríguez", "context": "esposa", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "099-876-543", "context": "teléfono familiar", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Pablo Martín Sánchez Aguiar", "context": "médico tratante", "is_direct": True},
]


# =============================================================================
# CASO B2: RESUMEN PEDIATRÍA
# =============================================================================

CASO_B2_TEXTO = """HOSPITAL PEREIRA ROSSELL - PEDIATRÍA
RESUMEN DE INTERNACIÓN

Paciente: Sofía Valentina Hernández Correa
CI: 5.987.321-0
Fecha nacimiento: 12/08/2020
Edad: 4 años 3 meses
Domicilio: Av. Italia 3456, Buceo
Teléfono madre: 099-555-333
HC: PR-2024-7890

MADRE: Lorena Correa Martínez, CI 3.456.123-8

PERÍODO:
Ingreso: 20/11/2024
Alta: 23/11/2024

DIAGNÓSTICO:
Bronquiolitis por VRS

RESUMEN:
Lactante mayor que ingresa por dificultad respiratoria de 24hs de evolución.
Antecedente de cuadro catarral 5 días previos.
Saturación al ingreso 88% AA.
Se inicia oxigenoterapia por cánula nasal.
Evolución favorable con retiro progresivo de O2.

TRATAMIENTO AL ALTA:
1. Salbutamol inhalado 2 puff c/6hs por 5 días
2. Paracetamol 150mg c/6hs si fiebre

VACUNAS: Esquema completo para la edad.

CONTROL: Pediatra de cabecera Dra. María José López en 48hs.

Médico responsable:
Dr. Andrés Fernández Olivera
Pediatra - Reg. MSP 67890"""

CASO_B2_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Sofía Valentina Hernández Correa", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "5.987.321-0", "context": "cédula paciente", "is_direct": True},
    {"category": "DATE_BIRTH", "value": "12/08/2020", "context": "fecha nacimiento", "is_direct": False},
    {"category": "LOCATION_STREET", "value": "Av. Italia 3456, Buceo", "context": "domicilio", "is_direct": False},
    {"category": "CONTACT_PHONE", "value": "099-555-333", "context": "teléfono madre", "is_direct": True},
    {"category": "ID_MEDICAL_RECORD", "value": "PR-2024-7890", "context": "historia clínica", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Lorena Correa Martínez", "context": "madre", "is_direct": True},
    {"category": "ID_CI", "value": "3.456.123-8", "context": "cédula madre", "is_direct": True},
    {"category": "DATE_ADMISSION", "value": "20/11/2024", "context": "fecha ingreso", "is_direct": False},
    {"category": "DATE_DISCHARGE", "value": "23/11/2024", "context": "fecha alta", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL PEREIRA ROSSELL", "context": "institución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "María José López", "context": "pediatra cabecera", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Andrés Fernández Olivera", "context": "médico tratante", "is_direct": True},
]


# =============================================================================
# CASO B3: NOTA OPERATORIA TRAUMATOLOGÍA
# =============================================================================

CASO_B3_TEXTO = """HOSPITAL DE CLÍNICAS - TRAUMATOLOGÍA
PROTOCOLO OPERATORIO

Fecha: 26/11/2024
Hora inicio: 14:30 - Hora fin: 16:45

DATOS DEL PACIENTE:
Nombre: Miguel Ángel Rodríguez Techera
CI: 1.234.567-8
Edad: 35 años
Domicilio: Calle Durazno 1234, Ciudad Vieja
Teléfono: 2916-7890
Email: marodriguez@hotmail.com
HC: TRAU-2024-4567
Cama: Traumatología B - Cama 8

DIAGNÓSTICO PREOPERATORIO:
Fractura diafisaria de fémur izquierdo (AO 32-A2)

PROCEDIMIENTO:
Reducción abierta + osteosíntesis con clavo endomedular bloqueado (Synthes)
Tiempo quirúrgico: 2h 15min
Sangrado estimado: 250ml
Sin complicaciones intraoperatorias.

EQUIPO QUIRÚRGICO:
- Cirujano principal: Dr. Martín González Etchegoyen
- Primer ayudante: Dr. Federico Álvarez Pérez
- Anestesiólogo: Dra. Gabriela Suárez Núñez
- Instrumentista: LE. Marcela Fernández

INDICACIONES POSTOPERATORIAS:
1. Analgesia multimodal
2. Tromboprofilaxis con enoxaparina 40mg SC/día
3. ATB: Cefazolina 1g c/8hs x 24hs
4. Control Rx en 24hs
5. Movilización precoz con KTR

FAMILIAR AVISADO:
Esposa: Claudia Martínez (tel: 099-777-888)

Firma del cirujano:
Dr. Martín González Etchegoyen
Traumatólogo - Reg. MSP 12345"""

CASO_B3_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Miguel Ángel Rodríguez Techera", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "1.234.567-8", "context": "cédula paciente", "is_direct": True},
    {"category": "LOCATION_STREET", "value": "Calle Durazno 1234, Ciudad Vieja", "context": "domicilio", "is_direct": False},
    {"category": "CONTACT_PHONE", "value": "2916-7890", "context": "teléfono fijo", "is_direct": True},
    {"category": "CONTACT_EMAIL", "value": "marodriguez@hotmail.com", "context": "email", "is_direct": True},
    {"category": "ID_MEDICAL_RECORD", "value": "TRAU-2024-4567", "context": "historia clínica", "is_direct": True},
    {"category": "DATE_PROCEDURE", "value": "26/11/2024", "context": "fecha cirugía", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL DE CLÍNICAS", "context": "institución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "Martín González Etchegoyen", "context": "cirujano", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Federico Álvarez Pérez", "context": "ayudante", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Gabriela Suárez Núñez", "context": "anestesióloga", "is_direct": True},
    {"category": "NAME_NURSE", "value": "Marcela Fernández", "context": "instrumentista", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Claudia Martínez", "context": "esposa", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "099-777-888", "context": "teléfono familiar", "is_direct": True},
]


# =============================================================================
# CASO C1: HISTORIA COMPLETA PSIQUIATRÍA
# =============================================================================

CASO_C1_TEXTO = """HOSPITAL VILARDEBÓ - SERVICIO DE PSIQUIATRÍA
HISTORIA CLÍNICA COMPLETA

DATOS DE FILIACIÓN:
Nombre: Eduardo Sebastián Pérez Rodríguez
CI: 3.876.543-2
Fecha nacimiento: 05/07/1985
Edad: 39 años
Estado civil: Divorciado
Ocupación: Contador
Domicilio: Av. Rivera 4567, Pocitos
Ciudad: Montevideo
Teléfono: 2709-8765
Celular: 094-321-654
Email: espearez@gmail.com
Prestador: CASMU
HC: PSI-2024-3456

FAMILIAR DE REFERENCIA:
Madre: Rosa María Rodríguez de Pérez
CI: 1.234.098-7
Tel: 099-654-321
Domicilio: Calle Soriano 789, Centro

FECHA INGRESO: 15/11/2024
MOTIVO: Ingreso involuntario por riesgo autolítico

ANTECEDENTES PSIQUIÁTRICOS:
- Trastorno Depresivo Mayor, episodio único grave (2019)
- Internación previa en Clínica Psiquiátrica del Sur (marzo 2019)
- Tratamiento ambulatorio con Dr. Martín Fernández Brum (psiquiatra)
- Psicoterapia con Lic. Ana Laura Gómez (psicóloga)

HISTORIA DE ENFERMEDAD ACTUAL:
Paciente traído por familiares por ideación suicida activa con plan estructurado.
Refiere empeoramiento del ánimo hace 3 semanas post-separación.
Dejó medicación hace 1 mes (Sertralina 100mg + Quetiapina 50mg).
Niega consumo de sustancias. Alcohol social esporádico.

EXAMEN PSIQUIÁTRICO:
Aspecto: descuidado, adelgazado
Actitud: colaborador con entrevista
Conciencia: lúcida
Orientación: conservada en tiempo, espacio y persona
Atención: disminuida
Memoria: sin alteraciones evidentes
Pensamiento: curso bradipsíquico, contenido con ideación de muerte
Afectividad: deprimido, anhedonia, llanto fácil
Sensopercepción: sin alteraciones
Juicio y autocrítica: parcialmente conservados
Sueño: insomnio mixto

DIAGNÓSTICO (CIE-10):
F32.2 - Episodio depresivo grave sin síntomas psicóticos
Z65.3 - Problemas relacionados con otras circunstancias legales

PLAN DE TRATAMIENTO:
1. Internación en Sala cerrada
2. Sertralina 50mg/día, aumentar a 100mg en 1 semana
3. Quetiapina 100mg noche
4. Clonazepam 0.5mg c/12hs (descenso progresivo)
5. Psicoterapia de apoyo
6. Entrevistas familiares

Médico tratante:
Dra. Victoria González Silveira
Psiquiatra - Reg. MSP 78901

Fecha: 15/11/2024"""

CASO_C1_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "Eduardo Sebastián Pérez Rodríguez", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "3.876.543-2", "context": "cédula paciente", "is_direct": True},
    {"category": "DATE_BIRTH", "value": "05/07/1985", "context": "fecha nacimiento", "is_direct": False},
    {"category": "PROFESSION", "value": "Contador", "context": "ocupación", "is_direct": False},
    {"category": "LOCATION_STREET", "value": "Av. Rivera 4567, Pocitos", "context": "domicilio", "is_direct": False},
    {"category": "LOCATION_CITY", "value": "Montevideo", "context": "ciudad", "is_direct": False},
    {"category": "CONTACT_PHONE", "value": "2709-8765", "context": "teléfono fijo", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "094-321-654", "context": "celular", "is_direct": True},
    {"category": "CONTACT_EMAIL", "value": "espearez@gmail.com", "context": "email", "is_direct": True},
    {"category": "LOCATION_ORGANIZATION", "value": "CASMU", "context": "prestador", "is_direct": False},
    {"category": "ID_MEDICAL_RECORD", "value": "PSI-2024-3456", "context": "historia clínica", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Rosa María Rodríguez de Pérez", "context": "madre", "is_direct": True},
    {"category": "ID_CI", "value": "1.234.098-7", "context": "cédula madre", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "099-654-321", "context": "teléfono madre", "is_direct": True},
    {"category": "LOCATION_STREET", "value": "Calle Soriano 789, Centro", "context": "domicilio madre", "is_direct": False},
    {"category": "DATE_ADMISSION", "value": "15/11/2024", "context": "fecha ingreso", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL VILARDEBÓ", "context": "institución", "is_direct": False},
    {"category": "LOCATION_HOSPITAL", "value": "Clínica Psiquiátrica del Sur", "context": "internación previa", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "Martín Fernández Brum", "context": "psiquiatra tratante", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Ana Laura Gómez", "context": "psicóloga", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Victoria González Silveira", "context": "psiquiatra actual", "is_direct": True},
]


# =============================================================================
# CASO C2: MULTI-EVOLUCIÓN (caso más complejo)
# =============================================================================

CASO_C2_TEXTO = """--- HOSPITAL MACIEL - CTI ---
EVOLUCIONES MÚLTIPLES

DATOS DEL PACIENTE:
Nombre: OSCAR DANIEL MARTÍNEZ FERNÁNDEZ
CI: 2.345.678-9
Edad: 55 años
Domicilio: Av. Gral. Flores 7890, La Teja
Ciudad: Montevideo
Prestador: Mutualista Círculo Católico
HC: CTI-2024-8901
Cama: CTI-05

--- EVOLUCIÓN 1 (27/11/2024 08:00) ---
Día 5 de internación en CTI.
Diagnósticos: Pancreatitis aguda necrotizante, SDRA, IRA KDIGO 2.
Paciente en ARM modo VC, FiO2 0.5, PEEP 10. Parámetros estables.
Bajo noradrenalina 0.15 mcg/kg/min.
Laboratorio: Lipasa 1500, Cr 2.8, Lac 2.1
Se solicita TAC abd-pelvis de control.
Se coordina con Cirugía General (Dr. Rodríguez Pérez) para eventual necrosectomía.

Responsables:
Dr. Santiago García Núñez
Dra. María Belén Fernández
LE. Carolina Suárez

--- EVOLUCIÓN 2 (27/11/2024 14:00) ---
Se realiza TAC: Necrosis >50%, colecciones peripancreáticas.
Gastroenterología (Dra. Patricia López) sugiere drenaje percutáneo.
Se llama a esposa Sra. Laura Martínez al 099-111-222.
Familiar informado sobre gravedad.
Se consulta a Infectología (Dr. Mauricio Álvarez) por cubrimiento ATB.

Responsable: Dr. Santiago García Núñez

--- EVOLUCIÓN 3 (28/11/2024 08:00) ---
Día 6. Paciente inestable. Aumentó requerimiento de NAD a 0.3.
FiO2 0.7. Oligoanúrico, inicia TRRC.
Interconsulta con Nefrología - Dra. Valeria González.
Familia presente: esposa Laura Martínez, hijo mayor Martín Martínez.
Pronóstico reservado.

Médico responsable: Dr. Santiago García Núñez
Enfermería: LE. Patricia Núñez Olivera

--- EVOLUCIÓN 4 (28/11/2024 20:00) ---
Evolución tórpida. Shock refractario.
Se discute con familia limitación del esfuerzo terapéutico.
Presente: esposa, hijo, hermano del paciente (Sr. Jorge Martínez).
Familia acepta LET.
Paciente fallece a las 23:45.

Certificado de defunción emitido.
Médico certificador: Dr. Santiago García Núñez
CI médico: 2.567.890-1"""

CASO_C2_ENTIDADES = [
    {"category": "NAME_PATIENT", "value": "OSCAR DANIEL MARTÍNEZ FERNÁNDEZ", "context": "nombre paciente", "is_direct": True},
    {"category": "ID_CI", "value": "2.345.678-9", "context": "cédula paciente", "is_direct": True},
    {"category": "LOCATION_STREET", "value": "Av. Gral. Flores 7890, La Teja", "context": "domicilio", "is_direct": False},
    {"category": "LOCATION_CITY", "value": "Montevideo", "context": "ciudad", "is_direct": False},
    {"category": "LOCATION_ORGANIZATION", "value": "Mutualista Círculo Católico", "context": "prestador", "is_direct": False},
    {"category": "ID_MEDICAL_RECORD", "value": "CTI-2024-8901", "context": "historia clínica", "is_direct": True},
    {"category": "LOCATION_HOSPITAL", "value": "HOSPITAL MACIEL", "context": "institución", "is_direct": False},
    {"category": "DATE_PROCEDURE", "value": "27/11/2024", "context": "fecha evolución", "is_direct": False},
    {"category": "DATE_PROCEDURE", "value": "28/11/2024", "context": "fecha evolución", "is_direct": False},
    {"category": "NAME_DOCTOR", "value": "Rodríguez Pérez", "context": "cirujano", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Santiago García Núñez", "context": "médico CTI", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "María Belén Fernández", "context": "médica CTI", "is_direct": True},
    {"category": "NAME_NURSE", "value": "Carolina Suárez", "context": "enfermera", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Patricia López", "context": "gastroenteróloga", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Laura Martínez", "context": "esposa", "is_direct": True},
    {"category": "CONTACT_PHONE", "value": "099-111-222", "context": "teléfono esposa", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Mauricio Álvarez", "context": "infectólogo", "is_direct": True},
    {"category": "NAME_DOCTOR", "value": "Valeria González", "context": "nefróloga", "is_direct": True},
    {"category": "NAME_NURSE", "value": "Patricia Núñez Olivera", "context": "enfermera", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Martín Martínez", "context": "hijo", "is_direct": True},
    {"category": "NAME_FAMILY", "value": "Jorge Martínez", "context": "hermano", "is_direct": True},
    {"category": "ID_CI", "value": "2.567.890-1", "context": "cédula médico", "is_direct": True},
]


# =============================================================================
# DICCIONARIO PRINCIPAL DE CASOS
# =============================================================================

CASOS_CLINICOS = {
    "A1": {
        "id": "A1",
        "nombre": "Emergencia Cardiología",
        "tipo": "Emergencia",
        "especialidad": "Cardiología",
        "descripcion": "Paciente con IAM SCEST, código infarto",
        "texto": CASO_A1_TEXTO,
        "entidades": CASO_A1_ENTIDADES,
        "num_entidades": len(CASO_A1_ENTIDADES),
        "tokens_estimados": 200,
        "complejidad": "Media"
    },
    "A2": {
        "id": "A2",
        "nombre": "Consulta Oncología",
        "tipo": "Consulta",
        "especialidad": "Oncología",
        "descripcion": "Seguimiento carcinoma de mama",
        "texto": CASO_A2_TEXTO,
        "entidades": CASO_A2_ENTIDADES,
        "num_entidades": len(CASO_A2_ENTIDADES),
        "tokens_estimados": 150,
        "complejidad": "Media"
    },
    "A3": {
        "id": "A3",
        "nombre": "Evolución CTI",
        "tipo": "Evolución",
        "especialidad": "Cuidados Intensivos",
        "descripcion": "Paciente crítico con neumonía y SDRA",
        "texto": CASO_A3_TEXTO,
        "entidades": CASO_A3_ENTIDADES,
        "num_entidades": len(CASO_A3_ENTIDADES),
        "tokens_estimados": 400,
        "complejidad": "Alta"
    },
    "A4": {
        "id": "A4",
        "nombre": "Alta Médica Cirugía",
        "tipo": "Epicrisis",
        "especialidad": "Cirugía General",
        "descripcion": "Alta post-colecistectomía laparoscópica",
        "texto": CASO_A4_TEXTO,
        "entidades": CASO_A4_ENTIDADES,
        "num_entidades": len(CASO_A4_ENTIDADES),
        "tokens_estimados": 300,
        "complejidad": "Media"
    },
    "A5": {
        "id": "A5",
        "nombre": "Interconsulta Neurología",
        "tipo": "Interconsulta",
        "especialidad": "Neurología",
        "descripcion": "Valoración por síndrome confusional",
        "texto": CASO_A5_TEXTO,
        "entidades": CASO_A5_ENTIDADES,
        "num_entidades": len(CASO_A5_ENTIDADES),
        "tokens_estimados": 180,
        "complejidad": "Media"
    },
    "B1": {
        "id": "B1",
        "nombre": "Epicrisis Medicina Interna",
        "tipo": "Epicrisis",
        "especialidad": "Medicina Interna",
        "descripcion": "IC descompensada, internación prolongada",
        "texto": CASO_B1_TEXTO,
        "entidades": CASO_B1_ENTIDADES,
        "num_entidades": len(CASO_B1_ENTIDADES),
        "tokens_estimados": 500,
        "complejidad": "Alta"
    },
    "B2": {
        "id": "B2",
        "nombre": "Resumen Pediatría",
        "tipo": "Resumen",
        "especialidad": "Pediatría",
        "descripcion": "Bronquiolitis en lactante mayor",
        "texto": CASO_B2_TEXTO,
        "entidades": CASO_B2_ENTIDADES,
        "num_entidades": len(CASO_B2_ENTIDADES),
        "tokens_estimados": 220,
        "complejidad": "Media"
    },
    "B3": {
        "id": "B3",
        "nombre": "Nota Operatoria Traumatología",
        "tipo": "Protocolo Quirúrgico",
        "especialidad": "Traumatología",
        "descripcion": "Osteosíntesis de fractura de fémur",
        "texto": CASO_B3_TEXTO,
        "entidades": CASO_B3_ENTIDADES,
        "num_entidades": len(CASO_B3_ENTIDADES),
        "tokens_estimados": 450,
        "complejidad": "Alta"
    },
    "C1": {
        "id": "C1",
        "nombre": "Historia Completa Psiquiatría",
        "tipo": "Historia Clínica",
        "especialidad": "Psiquiatría",
        "descripcion": "Depresión grave con riesgo suicida",
        "texto": CASO_C1_TEXTO,
        "entidades": CASO_C1_ENTIDADES,
        "num_entidades": len(CASO_C1_ENTIDADES),
        "tokens_estimados": 800,
        "complejidad": "Muy Alta"
    },
    "C2": {
        "id": "C2",
        "nombre": "Multi-Evolución CTI",
        "tipo": "Evoluciones Múltiples",
        "especialidad": "Cuidados Intensivos",
        "descripcion": "Pancreatitis necrotizante, evolución fatal",
        "texto": CASO_C2_TEXTO,
        "entidades": CASO_C2_ENTIDADES,
        "num_entidades": len(CASO_C2_ENTIDADES),
        "tokens_estimados": 1000,
        "complejidad": "Muy Alta"
    },
}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def listar_casos():
    """Lista todos los casos disponibles con estadísticas."""
    print("\n" + "=" * 80)
    print("  DATASET DE CASOS CLÍNICOS - Protocolo v3.0")
    print("  Basado en i2b2 2014 + arXiv:2412.10918 + arXiv:2406.00062")
    print("=" * 80)

    total_entidades = 0
    total_directas = 0

    print(f"\n  {'ID':<4} {'Nombre':<30} {'Especialidad':<18} {'PHI':>4} {'Tokens':>7} {'Complejidad':<10}")
    print(f"  {'-'*4} {'-'*30} {'-'*18} {'-'*4} {'-'*7} {'-'*10}")

    for caso_id, caso in CASOS_CLINICOS.items():
        directas = sum(1 for e in caso['entidades'] if e.get('is_direct', False))
        total_entidades += caso['num_entidades']
        total_directas += directas

        print(f"  {caso_id:<4} {caso['nombre']:<30} {caso['especialidad']:<18} "
              f"{caso['num_entidades']:>4} {caso['tokens_estimados']:>7} {caso['complejidad']:<10}")

    print(f"\n  {'='*80}")
    print(f"  TOTAL: {len(CASOS_CLINICOS)} casos | {total_entidades} entidades PHI | {total_directas} identificadores directos")
    print(f"  {'='*80}\n")


def obtener_caso(caso_id: str) -> dict:
    """Obtiene un caso por su ID."""
    if caso_id not in CASOS_CLINICOS:
        raise ValueError(f"Caso '{caso_id}' no encontrado. Disponibles: {list(CASOS_CLINICOS.keys())}")
    return CASOS_CLINICOS[caso_id]


def obtener_todos_los_casos() -> dict:
    """Retorna todos los casos."""
    return CASOS_CLINICOS


def obtener_entidades_directas(caso_id: str) -> list:
    """Obtiene solo las entidades directas (críticas) de un caso."""
    caso = obtener_caso(caso_id)
    return [e for e in caso['entidades'] if e.get('is_direct', False)]


def obtener_entidades_cuasi(caso_id: str) -> list:
    """Obtiene solo las entidades cuasi-identificadoras de un caso."""
    caso = obtener_caso(caso_id)
    return [e for e in caso['entidades'] if not e.get('is_direct', False)]


def get_statistics() -> dict:
    """Retorna estadísticas del dataset."""
    stats = {
        "total_casos": len(CASOS_CLINICOS),
        "total_entidades": 0,
        "entidades_directas": 0,
        "entidades_cuasi": 0,
        "por_categoria": {},
        "por_complejidad": {"Media": 0, "Alta": 0, "Muy Alta": 0}
    }

    for caso in CASOS_CLINICOS.values():
        stats["total_entidades"] += caso['num_entidades']
        stats["por_complejidad"][caso['complejidad']] = stats["por_complejidad"].get(caso['complejidad'], 0) + 1

        for entidad in caso['entidades']:
            cat = entidad.get('category', 'UNKNOWN')
            stats["por_categoria"][cat] = stats["por_categoria"].get(cat, 0) + 1

            if entidad.get('is_direct', False):
                stats["entidades_directas"] += 1
            else:
                stats["entidades_cuasi"] += 1

    return stats


if __name__ == "__main__":
    listar_casos()

    print("\n" + "=" * 80)
    print("  ESTADÍSTICAS DEL DATASET")
    print("=" * 80)

    stats = get_statistics()
    print(f"\n  Total casos: {stats['total_casos']}")
    print(f"  Total entidades PHI: {stats['total_entidades']}")
    print(f"  - Identificadores directos: {stats['entidades_directas']}")
    print(f"  - Cuasi-identificadores: {stats['entidades_cuasi']}")

    print(f"\n  Por complejidad:")
    for comp, count in stats['por_complejidad'].items():
        print(f"    - {comp}: {count} casos")

    print(f"\n  Top categorías PHI:")
    sorted_cats = sorted(stats['por_categoria'].items(), key=lambda x: x[1], reverse=True)[:10]
    for cat, count in sorted_cats:
        print(f"    - {cat}: {count}")
