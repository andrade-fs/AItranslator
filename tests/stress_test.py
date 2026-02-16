import asyncio
import httpx
import time
import statistics
from tabulate import tabulate

URL = "http://localhost:8000/translate"
TOTAL_REQUESTS = 30
CONCURRENT_WORKERS = 4
TIMEOUT_LIMIT = 120.0

# Muestras etiquetadas para el análisis
SAMPLE_TEXTS = [
    # --- BLOQUE ÁRABE (Largo y Complejo) ---
    ("AR_ORIGINAL", "على الرغم من أن العالم العربي يمتلك موارد طبيعية هائلة، إلا أن الاستثمار في رأس المال البشري والتعليم التكنولوجي يظل هو المفتاح الحقيقي."),
    ("AR_REPEAT", "على الرغم من أن العالم العربي يمتلك موارد طبيعية هائلة، إلا أن الاستثمار في رأس المال البشري والتعليم التكنولوجي يظل هو المفتاح الحقيقي."),
    
    # --- BLOQUE INGLÉS (Técnico) ---
    ("EN_ORIGINAL", "Quantum computing depends on the principles of quantum mechanics, including superposition and entanglement to process data."),
    ("EN_REPEAT", "Quantum computing depends on the principles of quantum mechanics, including superposition and entanglement to process data."),
    
    # --- BLOQUE ALEMÁN (Estructura diferente) ---
    ("DE_ORIGINAL", "Die künstliche Intelligenz wird die Art und Weise, wie wir arbeiten und kommunizieren, in den nächsten Jahren grundlegend verändern."),
    ("DE_REPEAT", "Die künstliche Intelligenz wird die Art und Weise, wie wir arbeiten und kommunizieren, in den nächsten Jahren grundlegend verändern."),
    
    # --- BLOQUE FRANCÉS (Control) ---
    ("FR_ORIGINAL", "Le développement durable est devenu une priorité absolue pour les gouvernements du monde entier face au changement climatique."),
    ("FR_REPEAT", "Le développement durable est devenu une priorité absolue pour les gouvernements du monde entier face au changement climatique.")
]
async def worker(client, queue, results_by_type):
    while not queue.empty():
        label, text = await queue.get()
        payload = {"text": text, "target_lang": "spa_Latn"}
        
        start = time.perf_counter()
        try:
            response = await client.post(URL, json=payload, timeout=TIMEOUT_LIMIT)
            end = time.perf_counter()
            
            if response.status_code == 200:
                results_by_type[label].append(end - start)
            else:
                results_by_type[label].append("Error")
        except Exception:
            results_by_type[label].append("Timeout")
        finally:
            queue.task_done()

async def run_stress_test():
    print(f"🚀 Iniciando Test Detallado por Idioma/Longitud")
    
    queue = asyncio.Queue()
    results_by_type = {label: [] for label, _ in SAMPLE_TEXTS}
    
    for i in range(TOTAL_REQUESTS):
        await queue.put(SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)])

    async with httpx.AsyncClient() as client:
        start_test = time.perf_counter()
        workers = [asyncio.create_task(worker(client, queue, results_by_type)) for _ in range(CONCURRENT_WORKERS)]
        await queue.join()
        for w in workers: w.cancel()
        end_test = time.perf_counter()

    # --- PROCESAMIENTO DE DATOS ---
    table_data = []
    for label, latencies in results_by_type.items():
        valid = [l for l in latencies if isinstance(l, float)]
        avg = f"{statistics.mean(valid):.2f}s" if valid else "N/A"
        max_l = f"{max(valid):.2f}s" if valid else "N/A"
        table_data.append([label, len(valid), avg, max_l])

    total_time = end_test - start_test
    print("\n📊 DESGLOSE POR TIPO DE TEXTO:")
    print(tabulate(table_data, headers=["Etiqueta", "Éxitos", "Latencia Media", "Latencia Máxima"], tablefmt="fancy_grid"))
    print(f"\n⚡ RPS Global: {TOTAL_REQUESTS/total_time:.2f} req/s")
    print(f"⏱️ Tiempo total: {total_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(run_stress_test())