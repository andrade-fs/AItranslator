import asyncio
import httpx
import time

# Configuración
API_URL = "http://localhost:8000/translate"
CONCURRENT_REQUESTS = 50  # Número de personas traduciendo a la vez
TOTAL_REQUESTS = 200      # Total de traducciones a realizar

payload = {
    "text": "Este es un mensaje de prueba para medir la capacidad del servidor de traducción.",
    "source_lang": "spa_Latn",
    "target_lang": "ary_Arab"
}

async def send_request(client, stats):
    start = time.perf_counter()
    try:
        response = await client.post(API_URL, json=payload, timeout=20.0)
        end = time.perf_counter()
        if response.status_code == 200:
            stats['success'] += 1
            stats['times'].append(end - start)
        else:
            stats['errors'] += 1
    except Exception:
        stats['errors'] += 1

async def run_stress_test():
    stats = {'success': 0, 'errors': 0, 'times': []}
    
    print(f"🚀 Iniciando test: {TOTAL_REQUESTS} peticiones totales ({CONCURRENT_REQUESTS} concurrentes)...")
    
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=CONCURRENT_REQUESTS)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = []
        for _ in range(TOTAL_REQUESTS):
            tasks.append(send_request(client, stats))
        
        start_test = time.perf_counter()
        await asyncio.gather(*tasks)
        end_test = time.perf_counter()

    # Cálculos
    total_time = end_test - start_test
    avg_time = sum(stats['times']) / len(stats['times']) if stats['times'] else 0
    rps = stats['success'] / total_time

    print("\n--- 📊 RESULTADOS DEL TEST DE ESTRÉS ---")
    print(f"Tiempo total: {total_time:.2f} segundos")
    print(f"Peticiones por segundo (RPS): {rps:.2f}")
    print(f"Latencia media: {avg_time:.4f} segundos")
    print(f"Éxitos: {stats['success']}")
    print(f"Errores: {stats['errors']}")
    print("---------------------------------------")

if __name__ == "__main__":
    asyncio.run(run_stress_test())