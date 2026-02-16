Para transformar un simple log de comandos en un **README profesional**, necesitamos estructura, contexto técnico y una presentación visual clara de los excelentes resultados que obtuviste.

Aquí tienes una versión optimizada que resalta la eficiencia del motor **NLLB 1.3B** en CPU.

---

# 🌍 AI Translator API (NLLB-200 1.3B)

API profesional de traducción masiva basada en el modelo **NLLB-200 (1.3B Distilled)** de Meta, optimizada para ejecutarse en CPU mediante **CTranslate2**.

## 🚀 Características

* **Modelo:** NLLB-200 1.3B (Cuantización **Int8**).
* **Precisión:** Validación semántica real de ~86%.
* **Rendimiento:** ~0.8 RPS en 4 núcleos de CPU.
* **Dialectos:** Soporte extendido (incluyendo Árabe Marroquí `ary_Arab`, Euskera, etc.).

---

## 🛠️ Instalación y Configuración

### 1. Preparar el Entorno

```bash
# Crear entorno virtual
python3 -m venv nllb-env

# Activar entorno
# Linux/Mac:
source nllb-env/bin/activate
# Windows:
nllb-env\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

```

### 2. Descarga y Conversión del Modelo

Para obtener la máxima velocidad, descargamos los metadatos y convertimos los pesos originales al formato optimizado de **CTranslate2**.

```bash
# Descargar configuración y tokenizador
python3 -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='facebook/nllb-200-distilled-1.3B', local_dir='nllb-200-distilled-1.3B', allow_patterns=['tokenizer*', 'config.json', 'sentencepiece.bpe.model', 'special_tokens_map.json'], local_dir_use_symlinks=False)"

# Convertir y cuantizar a Int8 (Reduce RAM y aumenta velocidad en CPU)
ct2-transformers-converter --model facebook/nllb-200-distilled-1.3B --output_dir nllb_ct2_1.3b --quantization int8

```

---

## 🖥️ Ejecución de la API

Inicia el servidor con Uvicorn. Se recomienda 1 worker con múltiples hilos internos para optimizar el uso de CPU en modelos pesados.

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1

```

### Ejemplo de Uso (cURL)

```bash
curl -X 'POST' 'http://localhost:8000/translate' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "Buenos días, ¿cómo estás?",
  "source_lang": "spa_Latn",
  "target_lang": "ary_Arab"
}'

```

---

## 📊 Benchmarking y Stress Test

El sistema ha sido testeado bajo una carga de **30 tareas concurrentes** con un límite estricto de **4 hilos de CPU**.

### Resultados del Stress Test

| Métrica | Valor |
| --- | --- |
| **Tiempo Total (30 reqs)** | 36.90 s |
| **Throughput (RPS)** | **0.81 req/s** |
| **Latencia Media** | 4.65 s |
| **Latencia P95** | 5.06 s |
| **Tasa de Éxito** | 100% ✅ |

> **Nota técnica:** Los resultados demuestran una alta estabilidad. La latencia P95 se mantiene cerca de la media, lo que indica que la gestión de colas mediante semáforos asíncronos en FastAPI es eficiente para hardware con recursos limitados.

---

## 🐳 Docker (Opcional)

Para desplegar en entornos productivos o Kubernetes:

```bash
docker build -t ai-translator .
docker run -p 8000:8000 --cpus="4" ai-translator

```

---
