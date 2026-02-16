import asyncio
import fasttext
import os
import ctranslate2
import transformers
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re

app = FastAPI(title="NLLB 1.3B Professional Agency API")

# --- CONFIGURACIÓN DE MODELOS (1.3B) ---
MODEL_CT2 = "nllb_ct2_1.3b"
MODEL_HF = "nllb-200-distilled-1.3B"

# Optimizamos hilos para el 1.3B: más intra_threads ayudan con la carga pesada
translator = ctranslate2.Translator(
    MODEL_CT2,
    device="cpu",
    intra_threads=min(4, os.cpu_count()-1),
    inter_threads=1
)

tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_HF)
lang_model = fasttext.load_model("lid.176.ftz")

# El 1.3B consume más RAM. Bajamos a 2 concurrentes para evitar colapsos en CPU modestas.
sem = asyncio.Semaphore(2)

# Mapeo extendido para "idiomas de todo tipo"
LANG_MAP = {
    "es": "spa_Latn", "en": "eng_Latn", "fr": "fra_Latn", 
    "ar": "ary_Arab", "it": "ita_Latn", "de": "deu_Latn",
    "pt": "por_Latn", "nl": "nld_Latn", "ru": "rus_Cyrl",
    "ca": "cat_Latn", "eu": "eus_Latn", "ro": "ron_Latn",
    "gl": "glg_Latn", "tr": "tur_Latn", "pl": "pol_Latn"
}

class DetectedLanguage(BaseModel):
    confidence: float
    language: str

class TranslationRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"
    target_lang: str = "spa_Latn" # Fijamos target a español por defecto

class TranslationResponse(BaseModel):
    alternatives: List[str] = []
    detectedLanguage: DetectedLanguage
    translatedText: str

# --- FUNCIONES DE LIMPIEZA ---
def clean_output(text: str) -> str:
    text = re.sub(r"<unk>", "", text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([.,!?])\1+', r'\1', text)  # evita puntuación repetida
    return text.strip()


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # espacios múltiples
    text = re.sub(r'[“”«»]', '"', text)  # comillas especiales
    text = re.sub(r"[‘’´`]", "'", text)  # comillas simples
    return text

def get_nllb_code(lang_input: str, text: str):
    # fallback seguro
    default_nllb = "eng_Latn"

    if not lang_input or lang_input.lower() == "auto":
        try:
            predictions = lang_model.predict(text.replace("\n", " "), k=1)
            iso_code = predictions[0][0].replace("__label__", "")
            confidence = round(float(predictions[1][0]) * 100, 2)
        except Exception:
            # si fasttext falla
            return default_nllb, "en", 0.0

        nllb_code = LANG_MAP.get(iso_code, default_nllb)
        return nllb_code, iso_code, confidence
    else:
        nllb_code = LANG_MAP.get(lang_input, f"{lang_input}_Latn")
        return nllb_code, lang_input, 100.0


import asyncio
import fasttext
import os
import ctranslate2
import transformers
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re

app = FastAPI(title="NLLB 1.3B Professional Agency API")

# --- CONFIGURACIÓN DE MODELOS (1.3B) ---
MODEL_CT2 = "nllb_ct2_1.3b"
MODEL_HF = "nllb-200-distilled-1.3B"

# Optimizamos hilos para el 1.3B: más intra_threads ayudan con la carga pesada
translator = ctranslate2.Translator(
    MODEL_CT2,
    device="cpu",
    intra_threads=min(4, os.cpu_count()-1),
    inter_threads=1
)

tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_HF)
lang_model = fasttext.load_model("lid.176.ftz")

# El 1.3B consume más RAM. Bajamos a 2 concurrentes para evitar colapsos en CPU modestas.
sem = asyncio.Semaphore(2)

# Mapeo extendido para "idiomas de todo tipo"
LANG_MAP = {
    "es": "spa_Latn", "en": "eng_Latn", "fr": "fra_Latn", 
    "ar": "ary_Arab", "it": "ita_Latn", "de": "deu_Latn",
    "pt": "por_Latn", "nl": "nld_Latn", "ru": "rus_Cyrl",
    "ca": "cat_Latn", "eu": "eus_Latn", "ro": "ron_Latn",
    "gl": "glg_Latn", "tr": "tur_Latn", "pl": "pol_Latn"
}

class DetectedLanguage(BaseModel):
    confidence: float
    language: str

class TranslationRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"
    target_lang: str = "spa_Latn" # Fijamos target a español por defecto

class TranslationResponse(BaseModel):
    alternatives: List[str] = []
    detectedLanguage: DetectedLanguage
    translatedText: str

# --- FUNCIONES DE LIMPIEZA ---
def clean_output(text: str) -> str:
    text = re.sub(r"<unk>", "", text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'([.,!?])\1+', r'\1', text)  # evita puntuación repetida
    return text.strip()


def normalize_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # espacios múltiples
    text = re.sub(r'[“”«»]', '"', text)  # comillas especiales
    text = re.sub(r"[‘’´`]", "'", text)  # comillas simples
    return text

def get_nllb_code(lang_input: str, text: str):
    # fallback seguro
    default_nllb = "eng_Latn"

    if not lang_input or lang_input.lower() == "auto":
        try:
            predictions = lang_model.predict(text.replace("\n", " "), k=1)
            iso_code = predictions[0][0].replace("__label__", "")
            confidence = round(float(predictions[1][0]) * 100, 2)
        except Exception:
            # si fasttext falla
            return default_nllb, "en", 0.0

        nllb_code = LANG_MAP.get(iso_code, default_nllb)
        return nllb_code, iso_code, confidence
    else:
        nllb_code = LANG_MAP.get(lang_input, f"{lang_input}_Latn")
        return nllb_code, lang_input, 100.0



@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest):
    async with sem:
        try:
            # 1. Identificación
            src_nllb, iso_detected, confidence = get_nllb_code(request.source_lang, request.text)
            
            # 2. Tokenización (PASO CRUCIAL)
            tokenizer.src_lang = src_nllb
            clean_text = normalize_text(request.text)
            
            # Convertimos el string en una lista de tokens (strings)
            source_ids = tokenizer.encode(clean_text)
            source_tokens = tokenizer.convert_ids_to_tokens(source_ids)
            
            # 3. Traducción asíncrona
            loop = asyncio.get_running_loop()
            
            # ¡OJO a la estructura de las listas aquí!
            results = await loop.run_in_executor(
                None, 
                lambda: translator.translate_batch(
                    source=[source_tokens],
                    target_prefix=[[request.target_lang]],
                    beam_size=5,
                    num_hypotheses=3,
                    repetition_penalty=1.2,       # Evita bucles infinitos en frases complejas
                    length_penalty=1.0,           # 1.0 es neutro, >1.0 favorece frases largas
                    no_repeat_ngram_size=3        # Evita que el modelo se atasque repitiendo frases
                )
            )
            
            # 4. Decodificación de resultados
            # Procesamos todas las hipótesis (alternativas)
            processed_hyps = []
            for hyp_tokens in results[0].hypotheses:
                # Quitamos el token de idioma si aparece al principio
                if hyp_tokens and hyp_tokens[0] == request.target_lang:
                    clean_tokens = hyp_tokens[1:]
                else:
                    clean_tokens = hyp_tokens
                
                # Convertimos tokens de vuelta a texto
                decoded = tokenizer.decode(tokenizer.convert_tokens_to_ids(clean_tokens))
                processed_hyps.append(clean_output(decoded))
            
            return {
                "alternatives": processed_hyps[1:] if len(processed_hyps) > 1 else [],
                "detectedLanguage": {
                    "confidence": confidence,
                    "language": iso_detected
                },
                "translatedText": processed_hyps[0]
            }

        except Exception as e:
            print(f"❌ Error en la API: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Aumentamos el timeout porque el 1.3B tarda más en procesar frases largas
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=60)
