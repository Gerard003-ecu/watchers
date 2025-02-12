#!/usr/bin/env python3
import os
import tempfile
import time
import subprocess
import requests

# Ajusta estas rutas según la ubicación real de tus scripts
WATCHERS_SCRIPT = "/home/gerardo/Documentos/Proyectos/watchers/watchers/main.py"
WATCHERS_WAVE_SCRIPT = "/home/gerardo/Documentos/Proyectos/watchers_wave/watchers_wave.py"

def run_integration_test():
    # 1. Crear un directorio temporal que servirá como directorio de monitoreo para watchers
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Directorio temporal creado: {temp_dir}")
        
        # 2. Iniciar watchers_wave en un proceso separado
        print("Iniciando watchers_wave...")
        watchers_wave_proc = subprocess.Popen(
            ["python", WATCHERS_WAVE_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Esperar a que watchers_wave inicie completamente (por ejemplo, 5 segundos)
        time.sleep(5)
        
        # 3. Iniciar watchers, indicándole que monitorice el directorio temporal
        print("Iniciando watchers...")
        watchers_proc = subprocess.Popen(
            ["python", WATCHERS_SCRIPT, temp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Esperar a que watchers inicie (por ejemplo, 5 segundos)
        time.sleep(5)
        
        # 4. Simular un cambio en el directorio monitoreado: crear un archivo o modificarlo
        test_file = os.path.join(temp_dir, "test_file.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Contenido de prueba para integración.")
        print(f"Se creó/modificó el archivo: {test_file}")
        
        # Esperar unos segundos para que watchers detecte el cambio y envíe el evento a watchers_wave
        time.sleep(10)
        
        # 5. Consultar el endpoint /api/config de watchers_wave para verificar la información
        try:
            response = requests.get("http://localhost:5000/api/config", timeout=5)
            print("Respuesta de /api/config:")
            print(response.status_code)
            print(response.json())
        except Exception as e:
            print("Error al consultar /api/config:", e)
        
        # 6. Finalizar los procesos de watchers y watchers_wave
        watchers_proc.terminate()
        watchers_wave_proc.terminate()
        watchers_proc.wait()
        watchers_wave_proc.wait()
        print("Test de integración completado.")

if __name__ == "__main__":
    run_integration_test()
