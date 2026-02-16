import asyncio
import httpx
import time
import statistics
from tabulate import tabulate # Si no la tienes: pip install tabulate

# --- CONFIGURACIÓN DEL TEST ---
URL = "http://localhost:8000/translate"
TOTAL_REQUESTS = 30       # Número total de traducciones
CONCURRENT_WORKERS = 4    # Peticiones simultáneas (supera tu semáforo de 2 para probar la cola)
TIMEOUT_LIMIT = 120.0     # El 1.3B es lento, damos margen

SAMPLE_TEXTS = [
    "El desarrollo de la inteligencia artificial requiere una ética profunda.",
    "The quantum computing era is closer than we think for global security.",
    "La cybersécurité est un enjeu majeur pour les entreprises modernes.",
    "Die Energiewende ist notwendig für eine nachhaltige Zukunft."
]

async def worker(client, queue, results):
    """Función que consume tareas de la cola."""
    while not queue.empty():
        text = await queue.get()
        payload = {
            "text": text,
            "target_lang": "spa_Latn"
        }
        
        start = time.perf_counter()
        try:
            response = await client.post(URL, json=payload, timeout=TIMEOUT_LIMIT)
            end = time.perf_counter()
            
            if response.status_code == 200:
                results.append(end - start)
            else:
                results.append(f"Error {response.status_code}")
        except Exception as e:
            results.append("Timeout/Exception")
        finally:
            queue.task_done()

async def run_stress_test():
    print(f"🚀 Iniciando Test de Estrés en NLLB 1.3B")
    print(f"📊 Configuración: {TOTAL_REQUESTS} tareas | {CONCURRENT_WORKERS} workers simultáneos")
    print("-" * 60)

    # Llenar la cola con textos aleatorios de la muestra
    queue = asyncio.Queue()
    for i in range(TOTAL_REQUESTS):
        await queue.put(SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)])

    results = []
    
    async with httpx.AsyncClient() as client:
        start_time = time.perf_counter()
        
        # Crear workers concurrentes
        workers = [asyncio.create_task(worker(client, queue, results)) for _ in range(CONCURRENT_WORKERS)]
        
        # Esperar a que la cola se vacíe
        await queue.join()
        
        # Cancelar workers (ya terminaron)
        for w in workers:
            w.cancel()
            
        end_time = time.perf_counter()

    # --- PROCESAMIENTO DE MÉTRICAS ---
    latencies = [r for r in results if isinstance(r, (float, int))]
    errors = [r for r in results if not isinstance(r, (float, int))]
    total_duration = end_time - start_time
    rps = len(latencies) / total_duration

    # Tabla de resultados
    data = [
        ["Métrica", "Valor"],
        ["Tiempo Total del Test", f"{total_duration:.2f} s"],
        ["Peticiones por Segundo (RPS)", f"{rps:.2f} req/s"],
        ["Latencia Media", f"{statistics.mean(latencies):.2f} s" if latencies else "N/A"],
        ["Latencia P95 (Peor caso)", f"{statistics.quantiles(latencies, n=20)[18]:.2f} s" if len(latencies) > 1 else "N/A"],
        ["Éxitos ✅", len(latencies)],
        ["Errores ❌", len(errors)]
    ]

    print("\n" + tabulate(data, headers="firstrow", tablefmt="fancy_grid"))

if __name__ == "__main__":
    try:
        asyncio.run(run_stress_test())
    except KeyboardInterrupt:
        pass