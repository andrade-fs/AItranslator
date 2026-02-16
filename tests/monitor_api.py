import psutil
import time
import os
from tabulate import tabulate

def get_api_process():
    """Busca el proceso de Python que tiene el modelo cargado (el de más RAM)."""
    target_proc = None
    max_ram = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and any("python" in arg or "uvicorn" in arg for arg in cmdline):
                # Si el proceso consume más de 500MB, es nuestro candidato
                ram = proc.info['memory_info'].rss
                if ram > max_ram:
                    max_ram = ram
                    target_proc = proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return target_proc
def monitor():
    print("🕵️ Buscando proceso de la API NLLB...")
    
    # Intentamos encontrar el proceso inicialmente
    process = None
    while process is None:
        process = get_api_process()
        if not process:
            print("❌ API no detectada. Esperando a que inicies 'python3 main.py'...", end="\r")
            time.sleep(2)
    
    print(f"\n✅ Proceso detectado (PID: {process.pid}). Iniciando monitoreo...")
    time.sleep(1)

    try:
        while True:
            # Obtener métricas de CPU y Memoria
            # .cpu_percent(interval=1) nos da la media del último segundo
            cpu_usage = process.cpu_percent(interval=1.0)
            memory_info = process.memory_info()
            
            # Convertimos bytes a Megabytes para que el jefe lo entienda fácil
            memory_mb = memory_info.rss / (1024 * 1024)
            memory_vms = memory_info.vms / (1024 * 1024) # Memoria virtual total
            memory_percent = process.memory_percent()
            
            # Formatear tabla
            table = [
                ["Métrica", "Uso Actual"],
                ["PID del Proceso", process.pid],
                ["Uso de CPU", f"{cpu_usage}% (Total Cores)"],
                ["RAM Física (RSS)", f"{memory_mb:.2f} MB"],
                ["RAM Virtual (VMS)", f"{memory_vms:.2f} MB"],
                ["Uso de RAM %", f"{memory_percent:.2f}%"]
            ]
            
            # Limpiar pantalla para efecto de "Dashboard"
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f"📊 MONITOR DE RECURSOS - NLLB 1.3B")
            print(tabulate(table, headers="firstrow", tablefmt="fancy_grid"))
            print(f"\nÚltima actualización: {time.strftime('%H:%M:%S')}")
            print("💡 Lanza el stress_test.py ahora para ver el impacto.")
            
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        print("\n⚠️ El proceso de la API se ha detenido o se ha perdido el acceso.")
    except KeyboardInterrupt:
        print("\n👋 Monitoreo finalizado.")

if __name__ == "__main__":
    monitor()