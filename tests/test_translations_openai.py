import os
import json
import requests
from openai import OpenAI
from datetime import datetime

class EvaluadorAdministrativoIA:
    def __init__(self):
        # Configuración de LiteLLM / OpenAI
        self.client = OpenAI(
            base_url=os.getenv("LITELLM_BASE_URL", "http://11.11.11.113:4000/v1"),
            api_key=os.getenv("LITELLM_KEY", "sk-1234")
        )
        self.url_mi_api = "http://localhost:8000/translate"
        self.modelo = "gpt-4o-mini"

    def generar_dataset_complejo(self, cantidad=30):
        print(f"🧠 Generando {cantidad} frases de trámites administrativos complejos...\n")
        
        prompt = f"""
        Genera {cantidad} frases de trámites administrativos técnicos (extranjería, legal, impuestos, salud).
        IDIOMAS: Árabe, Francés, Inglés y Vasco (mezclados).
        Devuelve SOLO un JSON estrictamente con este formato:
        [
          {{
            "source": "frase original",
            "expected": "traducción perfecta al español",
            "idioma_original": "nombre del idioma"
          }}
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
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

    def evaluar_calidad(self, original, esperado, obtenido):
        prompt = f"Compara estas traducciones administrativas y devuelve SOLO un número del 0.0 al 1.0:\nORIGINAL: {original}\nESPERADA: {esperado}\nOBTENIDA: {obtenido}"
        try:
            response = self.client.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            return float(response.choices[0].message.content.strip())
        except:
            return 0.0

    def ejecutar_test_completo(self):
        dataset = self.generar_dataset_complejo(30)
        if not dataset: return

        # Estructura para el JSON de salida
        salida_json = {
            "fecha_test": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "configuracion": {"modelo_evaluador": self.modelo, "api_traduccion": self.url_mi_api},
            "lista_referencia": [],
            "resultados_tabla": [],
            "resumen_final": {}
        }

        print("📋 LISTA DE FRASES A EVALUAR:")
        print("-" * 40)
        for i, item in enumerate(dataset, 1):
            bloque_referencia = {
                "id": i,
                "idioma": item['idioma_original'],
                "original": item['source'],
                "esperado": item['expected']
            }
            salida_json["lista_referencia"].append(bloque_referencia)
            
            print(f"{i}. [{item['idioma_original']}]")
            print(f"   Original: {item['source']}")
            print(f"   Esperado: {item['expected']}\n")

        print("-" * 80)
        print(f"{'ID':<3} | {'IDIOMA':<10} | {'TRADUCCIÓN OBTENIDA':<50} | {'SCORE'}")
        print("-" * 80)

        total_score = 0
        
        for i, item in enumerate(dataset, 1):
            obtenido = self.llamar_a_mi_sistema(item['source'])
            score = self.evaluar_calidad(item['source'], item['expected'], obtenido)
            total_score += score
            
            truncado = (obtenido[:47] + '...') if len(obtenido) > 47 else obtenido
            estado = "✅" if score > 0.85 else "⚠️" if score > 0.60 else "❌"
            
            print(f"{i:<3} | {item['idioma_original']:<10} | {truncado:<50} | {score:.2f} {estado}")

            salida_json["resultados_tabla"].append({
                "id": i,
                "idioma": item['idioma_original'],
                "obtenido": obtenido,
                "score": score,
                "estado": estado
            })

        promedio = (total_score / len(dataset)) * 100
        salida_json["resumen_final"] = {
            "puntuacion_media": f"{promedio:.2f}%",
            "total_frases": len(dataset)
        }

        print("-" * 80)
        print(f"📊 RENDIMIENTO GLOBAL: {promedio:.2f}%")

        # GUARDAR EL JSON COMPLETO
        nombre_archivo = "reporte_completo_validacion.json"
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            json.dump(salida_json, f, indent=4, ensure_ascii=False)
        
        print(f"\n💾 ¡Éxito! Salida completa guardada en: {nombre_archivo}")

if __name__ == "__main__":
    test = EvaluadorAdministrativoIA()
    test.ejecutar_test_completo()