import os
import json
import requests
from openai import OpenAI
from datetime import datetime

class EvaluadorRealistaIA:
    def __init__(self):
        # Configuración de LiteLLM / OpenAI
        self.client = OpenAI(
            base_url=os.getenv("LITELLM_BASE_URL", "http://11.11.11.113:4000/v1"),
            api_key=os.getenv("LITELLM_KEY", "sk-1234")
        )
        self.url_mi_api = "http://localhost:8000/translate"
        self.modelo = "gpt-4o-mini"

    def generar_dataset_sucio(self, cantidad=30):
        """Genera frases con errores de escritura intencionados (Typos)"""
        print(f"🛠️ Generando {cantidad} frases con errores de escritura (Realismo Chat)...\n")
        
        prompt = f"""
        Actúa como un usuario de chat administrativo que escribe con prisas y comete errores.
        Genera {cantidad} frases de trámites técnicos (extranjería, impuestos, salud).
        IDIOMAS: Árabe, Francés, Inglés y Vasco (mezclados).
        
        REQUISITO CRÍTICO DE ERRORES:
        - El campo "source" DEBE tener errores: comerse letras, falta de acentos, letras adyacentes cambiadas (ej: "queir" en vez de "quiero"), falta de espacios.
        - En Árabe, omite algunos puntos o usa letras parecidas.
        - En Vasco, Francés e Inglés, escribe como alguien que no domina bien el teclado.
        - El campo "expected" DEBE ser la traducción PERFECTA y limpia al español.

        Devuelve SOLO un JSON estrictamente con este formato:
        [
          {{
            "source": "frase con errores y typos",
            "expected": "traducción limpia y perfecta al español",
            "idioma_original": "nombre del idioma"
          }}
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8
            )
            raw_content = response.choices[0].message.content.strip()
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            return json.loads(raw_content)
        except Exception as e:
            print(f"❌ Error generando frases: {e}")
            return []

    def llamar_a_mi_sistema(self, texto):
        payload = {"text": texto, "source_lang": "auto", "target_lang": "spa_Latn"}
        try:
            res = requests.post(self.url_mi_api, json=payload, timeout=15)
            return res.json().get("translatedText", "ERROR_API")
        except Exception:
            return "ERROR_CONEXION"

    def evaluar_calidad(self, original_con_errores, esperado_perfecto, obtenido):
        """El juez IA sabe que el original está mal escrito y evalúa si se entendió la intención"""
        prompt = f"""
        Actúa como juez de calidad. El 'ORIGINAL' tiene errores de ortografía y typos.
        Evalúa si la traducción 'OBTENIDA' refleja correctamente la intención de la frase 'ESPERADA'.
        
        ORIGINAL (CON ERRORES): {original_con_errores}
        ESPERADA (PERFECTA): {esperado_perfecto}
        OBTENIDA: {obtenido}
        
        Responde SOLO con un número del 0.0 al 1.0.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return float(response.choices[0].message.content.strip())
        except:
            return 0.0

    def ejecutar_test_robusto(self):
        dataset = self.generar_dataset_sucio(30)
        if not dataset: return

        salida_json = {
            "fecha_test": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tipo_test": "Resiliencia a errores de escritura (Typos)",
            "lista_referencia": [],
            "resultados_tabla": []
        }

        print("📋 LISTA DE FRASES CON ERRORES (LO QUE EL SISTEMA RECIBE):")
        print("-" * 50)
        for i, item in enumerate(dataset, 1):
            print(f"{i}. [{item['idioma_original']}] Source: {item['source']}")
            print(f"   Target esperado: {item['expected']}\n")
            salida_json["lista_referencia"].append({
                "id": i, "idioma": item['idioma_original'], "source": item['source'], "expected": item['expected']
            })

        print("-" * 90)
        print(f"{'ID':<3} | {'IDIOMA':<10} | {'TRADUCCIÓN OBTENIDA':<55} | {'SCORE'}")
        print("-" * 90)

        total_score = 0
        for i, item in enumerate(dataset, 1):
            obtenido = self.llamar_a_mi_sistema(item['source'])
            score = self.evaluar_calidad(item['source'], item['expected'], obtenido)
            total_score += score
            
            truncado = (obtenido[:52] + '...') if len(obtenido) > 52 else obtenido
            estado = "✅" if score > 0.85 else "⚠️" if score > 0.60 else "❌"
            
            print(f"{i:<3} | {item['idioma_original']:<10} | {truncado:<55} | {score:.2f} {estado}")

            salida_json["resultados_tabla"].append({
                "id": i, "score": score, "obtenido": obtenido, "estado": estado
            })

        promedio = (total_score / len(dataset)) * 100
        print("-" * 90)
        print(f"📊 RESILIENCIA MEDIA A ERRORES: {promedio:.2f}%")

        with open("reporte_resiliencia_typos.json", "w", encoding="utf-8") as f:
            json.dump(salida_json, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    test = EvaluadorRealistaIA()
    test.ejecutar_test_robusto()