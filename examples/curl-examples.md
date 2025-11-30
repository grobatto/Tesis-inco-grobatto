# Ejemplos de Uso con curl

Esta guía contiene ejemplos prácticos para interactuar con los modelos LLM desplegados en IBM Power10.

## Configuración Base

```bash
# Variables de configuración
export LLM_HOST="localhost"
export LLM_PORT="8089"
export LLM_URL="http://${LLM_HOST}:${LLM_PORT}"
```

## Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/completion` | POST | Completar texto |
| `/v1/chat/completions` | POST | API compatible OpenAI |
| `/health` | GET | Estado del servidor |
| `/props` | GET | Propiedades del modelo |

---

## 1. Health Check

```bash
# Verificar que el servidor está corriendo
curl -s http://localhost:8089/health | jq '.'
```

**Respuesta esperada:**
```json
{
  "status": "ok"
}
```

---

## 2. Completar Texto (Básico)

```bash
curl -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "La inteligencia artificial es",
    "n_predict": 50,
    "temperature": 0.7
  }'
```

---

## 3. Completar Texto (Con Parámetros Avanzados)

```bash
curl -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explica en 3 puntos qué es Machine Learning:",
    "n_predict": 200,
    "temperature": 0.7,
    "top_k": 40,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "stop": ["\n\n", "###"]
  }'
```

### Parámetros Explicados

| Parámetro | Descripción | Valor Típico |
|-----------|-------------|--------------|
| `n_predict` | Máximo de tokens a generar | 100-500 |
| `temperature` | Creatividad (0=determinístico, 1=creativo) | 0.7 |
| `top_k` | Considera los K tokens más probables | 40 |
| `top_p` | Nucleus sampling (probabilidad acumulada) | 0.9 |
| `repeat_penalty` | Penaliza repeticiones | 1.1 |
| `stop` | Secuencias para detener generación | ["\n\n"] |

---

## 4. API Compatible con OpenAI

```bash
curl -X POST http://localhost:8089/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {"role": "system", "content": "Eres un asistente experto en tecnología IBM."},
      {"role": "user", "content": "¿Qué es IBM Power10?"}
    ],
    "temperature": 0.7,
    "max_tokens": 200
  }'
```

---

## 5. Conversación Multi-turno

```bash
curl -X POST http://localhost:8089/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {"role": "system", "content": "Eres un experto en IA."},
      {"role": "user", "content": "¿Qué es deep learning?"},
      {"role": "assistant", "content": "Deep learning es una rama del machine learning que utiliza redes neuronales con múltiples capas para aprender representaciones jerárquicas de los datos."},
      {"role": "user", "content": "Dame un ejemplo práctico."}
    ],
    "temperature": 0.7
  }'
```

---

## 6. Caso de Uso: Anonimización Clínica

```bash
curl -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "[INST] Eres un sistema de anonimización de datos clínicos. Tu tarea es identificar y reemplazar información de salud protegida (PHI) con marcadores genéricos.

Tipos de PHI a anonimizar:
- Nombres: [NOMBRE]
- Fechas: [FECHA]
- Ubicaciones: [UBICACION]
- Números de identificación: [ID]
- Teléfonos: [TELEFONO]

Texto a anonimizar:
\"El paciente Juan García López, de 45 años, fue atendido el 15 de marzo de 2024 en el Hospital Central de Montevideo. Su número de historia clínica es HC-12345. Contacto: 099-123-456.\"

Devuelve SOLO el texto anonimizado: [/INST]",
    "n_predict": 300,
    "temperature": 0.3,
    "stop": ["[/INST]", "\n\n\n"]
  }'
```

---

## 7. Generación con Streaming

```bash
curl -N -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Cuenta una historia corta sobre un robot:",
    "n_predict": 200,
    "stream": true
  }'
```

---

## 8. Obtener Propiedades del Modelo

```bash
curl -s http://localhost:8089/props | jq '.'
```

---

## 9. Benchmark Simple

```bash
# Medir tiempo de respuesta
time curl -s -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test de velocidad:",
    "n_predict": 100
  }' | jq '.timings'
```

---

## 10. Extraer Solo el Texto de la Respuesta

```bash
curl -s -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hola, ¿cómo estás?",
    "n_predict": 50
  }' | jq -r '.content'
```

---

## 11. Guardar Respuesta en Archivo

```bash
curl -s -X POST http://localhost:8089/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Genera un resumen sobre IBM Power:",
    "n_predict": 500
  }' | jq -r '.content' > respuesta.txt
```

---

## Scripts Útiles

### Script de Consulta Rápida

```bash
#!/bin/bash
# query.sh - Hacer consultas rápidas al modelo
# Uso: ./query.sh "tu pregunta aquí"

PROMPT="$1"
PORT="${2:-8089}"

curl -s -X POST "http://localhost:$PORT/completion" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"$PROMPT\",
    \"n_predict\": 200,
    \"temperature\": 0.7
  }" | jq -r '.content'
```

### Script de Chat Interactivo

```bash
#!/bin/bash
# chat.sh - Chat interactivo con el modelo

PORT="${1:-8089}"

echo "Chat con LLM (escribe 'salir' para terminar)"
echo "============================================"

while true; do
    echo -n "Tú: "
    read -r input

    if [ "$input" = "salir" ]; then
        echo "¡Hasta luego!"
        break
    fi

    echo -n "Bot: "
    curl -s -X POST "http://localhost:$PORT/completion" \
      -H "Content-Type: application/json" \
      -d "{
        \"prompt\": \"[INST] $input [/INST]\",
        \"n_predict\": 200,
        \"temperature\": 0.7
      }" | jq -r '.content'
    echo ""
done
```

---

## Códigos de Error Comunes

| Código | Significado | Solución |
|--------|-------------|----------|
| `Connection refused` | Servidor no está corriendo | Verificar contenedor Docker |
| `503 Service Unavailable` | Modelo cargando | Esperar unos segundos |
| `400 Bad Request` | JSON malformado | Verificar sintaxis |
| `Empty response` | Timeout o error | Aumentar timeout, verificar logs |

---

## Tips

1. **Usa `jq` para formatear JSON**: `curl ... | jq '.'`
2. **Guarda prompts largos en archivos**: `curl -d @prompt.json ...`
3. **Usa `-s` para modo silencioso**: No muestra barra de progreso
4. **Usa `-N` para streaming**: Muestra tokens en tiempo real
