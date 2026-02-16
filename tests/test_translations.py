import requests
import json
import os
import re
import unicodedata
from difflib import SequenceMatcher

# ------------------------------
# Normalización avanzada
# ------------------------------
def normalizar(texto):
    """
    Limpia el texto para comparación justa:
    - Minusculas
    - Elimina acentos
    - Quita signos de puntuación
    - Quita saltos de línea y espacios extras
    """
    texto = texto.lower()
    # Eliminar acentos
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    # Quitar puntuación
    texto = re.sub(r'[^\w\s]', '', texto)
    # Quitar saltos de línea y espacios múltiples
    return " ".join(texto.split())


# ------------------------------
# Métrica híbrida
# ------------------------------
def ngrams(texto, n=3):
    """
    Extrae n-gramas de caracteres, reemplazando espacios por "_"
    """
    texto = texto.replace(" ", "_")
    return set([texto[i:i+n] for i in range(len(texto)-n+1)])


def calcular_similitud_hibrida(a, b):
    """
    Combina:
    - SequenceMatcher (orden de caracteres)
    - Jaccard de palabras (ignora orden)
    - Trigramas (captura similitud semántica)
    """
    norm_a = normalizar(a)
    norm_b = normalizar(b)

    # 1️⃣ Secuencia de caracteres
    seq_score = SequenceMatcher(None, norm_a, norm_b).ratio()

    # 2️⃣ Jaccard de palabras
    words_a, words_b = set(norm_a.split()), set(norm_b.split())
    word_score = len(words_a & words_b) / len(words_a | words_b) if words_a and words_b else 0

    # 3️⃣ Trigramas
    tri_a, tri_b = ngrams(norm_a), ngrams(norm_b)
    tri_score = len(tri_a & tri_b) / len(tri_a | tri_b) if tri_a and tri_b else 0

    # Ponderación: trigramas > palabras > secuencia
    return 0.4*tri_score + 0.35*word_score + 0.25*seq_score


# ------------------------------
# Ejecución de tests
# ------------------------------
def ejecutar_test():
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, "data.json")
    url_api = "http://localhost:8000/translate"

    # Cargar tests
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            tests = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encuentra data.json en {base_path}")
        return

    print(f"🧪 Validando {len(tests)} frases con Métrica Híbrida Semántica...\n")
    print(f"{'TEXTO ORIGINAL':<40} | {'SIMILITUD':<10} | {'ESTADO'}")
    print("-" * 85)

    total_score = 0

    for item in tests:
        payload = {
            "text": item["source"],
            "source_lang": "auto",
            "target_lang": "spa_Latn"
        }

        try:
            response = requests.post(url_api, json=payload, timeout=10)
            response.raise_for_status()
            resultado = response.json().get("translatedText", "")
        except requests.RequestException as e:
            print(f"❌ Error HTTP: {item['source'][:30]}... -> {e}")
            continue
        except (ValueError, KeyError) as e:
            print(f"❌ Error JSON: {item['source'][:30]}... -> {e}")
            continue

        # Calcular similitud híbrida
        score = calcular_similitud_hibrida(resultado, item["expected"])
        total_score += score
        porcentaje = f"{score * 100:.1f}%"

        # Umbral de estado
        estado = "✅" if score > 0.85 else "⚠️" if score > 0.65 else "❌"

        # Cortar texto largo para tabla
        display_text = (item["source"][:37] + '..') if len(item["source"]) > 37 else item["source"]
        print(f"{display_text:<40} | {porcentaje:<10} | {estado}")

        # Mostrar detalle si no es casi perfecta
        if score < 0.88:
            print(f"   └─ Esperado: {item['expected']}")
            print(f"   └─ Obtenido: {resultado}\n")

    promedio = (total_score / len(tests)) * 100 if tests else 0
    print("-" * 85)
    print(f"📊 PRECISIÓN SEMÁNTICA MEDIA: {promedio:.2f}%")


# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    ejecutar_test()
