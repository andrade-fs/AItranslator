import asyncio
import fasttext
import os
import ctranslate2
import transformers
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import re
import time
import psutil

app = FastAPI(title="NLLB 1.3B Professional Agency API")

# --- CONFIGURACIÓN DE MODELOS ---
MODEL_CT2 = "nllb_ct2_1.3b"
MODEL_HF = "nllb-200-distilled-1.3B"

# Configuración 2:2 para balancear latencia y concurrencia en 4 núcleos
translator = ctranslate2.Translator(
    MODEL_CT2,
    device="cpu",
    intra_threads=2,
    inter_threads=2,
    compute_type="int8" # Aseguramos el uso de la cuantización
)

tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_HF)
lang_model = fasttext.load_model("lid.176.ftz")

# Semáforo para controlar la carga de trabajo paralela
sem = asyncio.Semaphore(2)

# Mapeo profesional: ISO 639-1 (FastText) -> NLLB-200 
LANG_MAP = {
    # Principales
    "es": "spa_Latn", "en": "eng_Latn", "fr": "fra_Latn", "de": "deu_Latn",
    "it": "ita_Latn", "pt": "por_Latn", "nl": "nld_Latn", "ru": "rus_Cyrl",
    
    # Árabe (FastText suele dar 'ar', NLLB prefiere Standard o dialectos)
    "ar": "arb_Arab",  # Árabe Estándar Moderno (más seguro para NLLB que ary)
    "ary": "ary_Arab", # Árabe Marroquí (si FastText lo detecta específico)
    
    # Regionales España / Europa
    "ca": "cat_Latn", "eu": "eus_Latn", "gl": "glg_Latn", "ro": "ron_Latn",
    
    # Otros comunes
    "pl": "pol_Latn", "tr": "tur_Latn", "zh": "zho_Hans", "ja": "jpn_Jpan",
    "ko": "kor_Hang", "hi": "hin_Deva", "uk": "ukr_Cyrl", "sv": "swe_Latn",
    "fi": "fin_Latn", "no": "nob_Latn", "da": "dan_Latn"
}

# --- SCHEMAS ---
class DetectedLanguage(BaseModel):
    confidence: float
    language: str

class TranslationRequest(BaseModel):
    text: str
    source_lang: Optional[str] = "auto"
    target_lang: str = "spa_Latn"

class TranslationResponse(BaseModel):
    alternatives: List[str] = []
    detectedLanguage: DetectedLanguage
    translatedText: str
    processing_time: str # Añadido para monitoreo

# --- UTILS ---
def clean_output(text: str) -> str:
    text = re.sub(r"<unk>", "", text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip())

def get_nllb_code(lang_input: str, text: str):
    default_nllb = "eng_Latn"
    
    if not lang_input or lang_input.lower() == "auto":
        try:
            predictions = lang_model.predict(text.replace("\n", " "), k=1)
            iso_code = predictions[0][0].replace("__label__", "")
            confidence = round(float(predictions[1][0]) * 100, 2)
            
            # 1. Buscar en el mapa
            if iso_code in LANG_MAP:
                return LANG_MAP[iso_code], iso_code, confidence
            
            # 2. Intento de construcción dinámica (ej: 'fr' -> 'fra_Latn' es difícil, 
            # pero para muchos idiomas de 3 letras funciona)
            # Como regla general, si no está en el mapa, devolvemos el default seguro.
            return default_nllb, iso_code, confidence
            
        except Exception:
            return default_nllb, "en", 0.0
    
    # Si el usuario fuerza un idioma manual (ej: "es")
    return LANG_MAP.get(lang_input, f"{lang_input}_Latn"), lang_input, 100.0

# --- ENDPOINTS ---
@app.post("/translate", response_model=TranslationResponse)
async def translate(request: TranslationRequest):
    async with sem:
        start_time = time.perf_counter()
        try:
            src_nllb, iso_detected, confidence = get_nllb_code(request.source_lang, request.text)
            
            # Tokenización
            tokenizer.src_lang = src_nllb
            source_ids = tokenizer.encode(normalize_text(request.text))
            source_tokens = tokenizer.convert_ids_to_tokens(source_ids)
            
            # Ejecución en pool de hilos para no bloquear el loop de FastAPI
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None, 
                lambda: translator.translate_batch(
                    source=[source_tokens],
                    target_prefix=[[request.target_lang]],
                    beam_size=4, # Un poco más ligero para mejorar RPS
                    num_hypotheses=3,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
            )
            
            # Procesamiento de hipótesis
            processed_hyps = []
            for hyp in results[0].hypotheses:
                tokens = hyp[1:] if hyp[0] == request.target_lang else hyp
                decoded = tokenizer.decode(tokenizer.convert_tokens_to_ids(tokens))
                processed_hyps.append(clean_output(decoded))
            
            elapsed = time.perf_counter() - start_time
            
            return {
                "alternatives": processed_hyps[1:] if len(processed_hyps) > 1 else [],
                "detectedLanguage": {"confidence": confidence, "language": iso_detected},
                "translatedText": processed_hyps[0],
                "processing_time": f"{elapsed:.2f}s"
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Verifica la salud del servicio y el uso de recursos."""
    process = psutil.Process(os.getpid())
    mem_rss = process.memory_info().rss / (1024 * 1024)  # MB
    
    return {
        "status": "healthy",
        "model": "NLLB-200-1.3B",
        "engine": "CTranslate2",
        "device": "cpu",
        "uptime_ready": True,
        "resource_usage": {
            "memory_física_mb": round(mem_rss, 2),
            "cpu_threads_total": os.cpu_count(),
            "active_tasks_semaphore": 2 - sem._value # Cuántas están procesando ahora
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)