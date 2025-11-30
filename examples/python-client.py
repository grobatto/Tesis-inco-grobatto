#!/usr/bin/env python3
"""
Cliente Python para interactuar con modelos LLM en IBM Power10
Universidad de Montevideo - Proyecto Final de Grado

Uso:
    python python-client.py

Requisitos:
    pip install requests
"""

import requests
import json
import time
from typing import Optional, List, Dict, Any


class LLMClient:
    """Cliente para interactuar con el servidor llama.cpp"""

    def __init__(self, host: str = "localhost", port: int = 8089):
        """
        Inicializa el cliente LLM.

        Args:
            host: Hostname del servidor
            port: Puerto del servidor
        """
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()

    def health_check(self) -> bool:
        """Verifica si el servidor está disponible."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def complete(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_k: int = 40,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Genera una completación de texto.

        Args:
            prompt: Texto inicial para completar
            max_tokens: Máximo de tokens a generar
            temperature: Creatividad (0-1)
            top_k: Top-K sampling
            top_p: Nucleus sampling
            stop: Lista de secuencias para detener

        Returns:
            Diccionario con la respuesta del modelo
        """
        payload = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
        }

        if stop:
            payload["stop"] = stop

        response = self.session.post(
            f"{self.base_url}/completion",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 200,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Realiza una conversación usando el formato OpenAI.

        Args:
            messages: Lista de mensajes [{"role": "user", "content": "..."}]
            max_tokens: Máximo de tokens a generar
            temperature: Creatividad

        Returns:
            Diccionario con la respuesta del modelo
        """
        payload = {
            "model": "local",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json()

    def get_text(self, response: Dict[str, Any]) -> str:
        """Extrae solo el texto de una respuesta de completion."""
        return response.get("content", "")

    def get_chat_text(self, response: Dict[str, Any]) -> str:
        """Extrae solo el texto de una respuesta de chat."""
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return ""

    def get_metrics(self, response: Dict[str, Any]) -> Dict[str, float]:
        """Extrae métricas de rendimiento de una respuesta."""
        timings = response.get("timings", {})
        return {
            "prompt_tokens_per_sec": timings.get("prompt_per_second", 0),
            "generation_tokens_per_sec": timings.get("predicted_per_second", 0),
            "prompt_ms": timings.get("prompt_ms", 0),
            "generation_ms": timings.get("predicted_ms", 0),
            "tokens_generated": timings.get("predicted_n", 0)
        }


class ClinicalAnonymizer:
    """
    Anonimizador de textos clínicos usando LLM.
    Caso de uso principal de la tesis.
    """

    SYSTEM_PROMPT = """Eres un sistema de anonimización de datos clínicos.
Tu tarea es identificar y reemplazar información de salud protegida (PHI).

Tipos de PHI a anonimizar:
- Nombres de personas: [NOMBRE]
- Fechas específicas: [FECHA]
- Ubicaciones: [UBICACION]
- Números de identificación: [ID]
- Teléfonos: [TELEFONO]
- Direcciones de email: [EMAIL]
- Números de historia clínica: [HC]

Devuelve SOLO el texto anonimizado, sin explicaciones adicionales."""

    def __init__(self, client: LLMClient):
        self.client = client

    def anonymize(self, clinical_text: str) -> str:
        """
        Anonimiza un texto clínico.

        Args:
            clinical_text: Texto con información clínica

        Returns:
            Texto anonimizado
        """
        prompt = f"""[INST] {self.SYSTEM_PROMPT}

Texto a anonimizar:
\"{clinical_text}\"

Texto anonimizado: [/INST]"""

        response = self.client.complete(
            prompt=prompt,
            max_tokens=len(clinical_text) + 100,
            temperature=0.3,  # Baja temperatura para mayor precisión
            stop=["[/INST]", "\n\n\n"]
        )

        return self.client.get_text(response).strip()


def demo_basic():
    """Demostración básica de uso del cliente."""
    print("=" * 50)
    print("Demo: Uso Básico del Cliente LLM")
    print("=" * 50)

    client = LLMClient(port=8089)

    # Verificar conexión
    print("\n1. Verificando conexión...")
    if not client.health_check():
        print("Error: No se puede conectar al servidor")
        return

    print("   Servidor OK")

    # Completación simple
    print("\n2. Completación de texto...")
    response = client.complete(
        prompt="La inteligencia artificial es",
        max_tokens=50
    )
    print(f"   Respuesta: {client.get_text(response)}")

    # Métricas
    metrics = client.get_metrics(response)
    print(f"\n   Métricas:")
    print(f"   - Prompt: {metrics['prompt_tokens_per_sec']:.1f} tokens/seg")
    print(f"   - Generación: {metrics['generation_tokens_per_sec']:.1f} tokens/seg")


def demo_chat():
    """Demostración del modo chat."""
    print("\n" + "=" * 50)
    print("Demo: Modo Chat (API OpenAI Compatible)")
    print("=" * 50)

    client = LLMClient(port=8089)

    messages = [
        {"role": "system", "content": "Eres un experto en tecnología IBM."},
        {"role": "user", "content": "¿Qué es IBM Power10?"}
    ]

    print("\n1. Primera pregunta...")
    response = client.chat(messages, max_tokens=150)
    assistant_response = client.get_chat_text(response)
    print(f"   Bot: {assistant_response[:200]}...")

    # Continuar conversación
    messages.append({"role": "assistant", "content": assistant_response})
    messages.append({"role": "user", "content": "¿Qué son los aceleradores MMA?"})

    print("\n2. Pregunta de seguimiento...")
    response = client.chat(messages, max_tokens=150)
    print(f"   Bot: {client.get_chat_text(response)[:200]}...")


def demo_anonymization():
    """Demostración del caso de uso de anonimización clínica."""
    print("\n" + "=" * 50)
    print("Demo: Anonimización de Datos Clínicos")
    print("=" * 50)

    client = LLMClient(port=8089)
    anonymizer = ClinicalAnonymizer(client)

    clinical_text = """
    El paciente Juan García López, de 45 años, fue atendido el 15 de marzo
    de 2024 en el Hospital Central de Montevideo. Su número de historia
    clínica es HC-12345. El Dr. María Rodríguez realizó el diagnóstico
    de hipertensión arterial. Contacto del paciente: 099-123-456.
    """

    print(f"\nTexto original:")
    print(f"   {clinical_text.strip()}")

    print(f"\nAnonimizando...")
    start_time = time.time()
    anonymized = anonymizer.anonymize(clinical_text)
    elapsed = time.time() - start_time

    print(f"\nTexto anonimizado:")
    print(f"   {anonymized}")
    print(f"\nTiempo de procesamiento: {elapsed:.2f} segundos")


def demo_benchmark():
    """Benchmark simple de rendimiento."""
    print("\n" + "=" * 50)
    print("Demo: Benchmark de Rendimiento")
    print("=" * 50)

    client = LLMClient(port=8089)
    iterations = 3

    prompt_rates = []
    gen_rates = []

    print(f"\nEjecutando {iterations} iteraciones...")

    for i in range(iterations):
        response = client.complete(
            prompt="Explica brevemente qué es la computación cuántica:",
            max_tokens=100
        )
        metrics = client.get_metrics(response)
        prompt_rates.append(metrics["prompt_tokens_per_sec"])
        gen_rates.append(metrics["generation_tokens_per_sec"])

        print(f"   Iteración {i+1}: Prompt={metrics['prompt_tokens_per_sec']:.1f} t/s, "
              f"Gen={metrics['generation_tokens_per_sec']:.1f} t/s")

        time.sleep(1)

    avg_prompt = sum(prompt_rates) / len(prompt_rates)
    avg_gen = sum(gen_rates) / len(gen_rates)

    print(f"\nResultados promedio:")
    print(f"   Prompt: {avg_prompt:.1f} tokens/seg")
    print(f"   Generación: {avg_gen:.1f} tokens/seg")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CLIENTE PYTHON PARA LLM EN IBM POWER10")
    print("  Universidad de Montevideo - Tesis 2025")
    print("=" * 60)

    try:
        demo_basic()
        demo_chat()
        demo_anonymization()
        demo_benchmark()

    except requests.exceptions.ConnectionError:
        print("\nError: No se puede conectar al servidor.")
        print("Asegúrate de que el contenedor Docker está corriendo:")
        print("  docker ps")
        print("  docker logs qwen-7b")

    except Exception as e:
        print(f"\nError: {e}")

    print("\n" + "=" * 60)
    print("  FIN DE LA DEMOSTRACIÓN")
    print("=" * 60 + "\n")
