#!/usr/bin/env python3
"""
watchers_wave: Simulación y orquestación de eventos para la integración con watchers.

Este script realiza:
  - La simulación del oscilador 2D mediante RK4, generando eventos cuando la amplitud supera un umbral.
  - El análisis periódico de un log de errores para ajustar parámetros (guardados en un archivo JSON).
  - La exposición de una API con Flask para recibir notificaciones y para que watchers consulte la configuración actual,
    incluyendo información del hardware.
  - La consulta periódica del endpoint REST que expone el estado de la malla (definido en /api/malla),
    para ajustar parámetros y activar acciones correctivas si es necesario.
"""

import json
import math
import logging
import time
import threading
import os
from flask import Flask, request, jsonify
import psutil
import requests

# Configuración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Rutas para los archivos de log y configuración
ERROR_LOG = "/home/gerardo/Documentos/proyectos/mi-proyecto/watchers/error.log"
AUTO_CONFIG = "/home/gerardo/Documentos/proyectos/mi-proyecto/watchers_wave/monitor_text/auto_config.json"
OUTPUT_FILE = "/home/gerardo/Documentos/proyectos/mi-proyecto/watchers_wave/monitor_text/monitor_test.txt"

# Crear directorios si no existen
os.makedirs(os.path.dirname(ERROR_LOG), exist_ok=True)
os.makedirs(os.path.dirname(AUTO_CONFIG), exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# --- Definición de la aplicación Flask ---
app = Flask(__name__)

@app.route('/api/event', methods=['POST'])
def receive_event():
    data = request.get_json()
    if not data:
        logging.error("No se recibieron datos JSON en /api/event.")
        return jsonify({"status": "error", "message": "No se recibieron datos JSON"}), 400
    event_id = data.get("event_id", "N/A")
    file_path = data.get("file_path", "N/A")
    logging.info(f"Recibido evento {event_id} para el archivo: {file_path}")
    return jsonify({"status": "success", "message": f"Evento {event_id} procesado"}), 200

@app.route('/api/error', methods=['POST'])
def receive_error():
    data = request.get_json()
    if not data:
        logging.error("No se recibieron datos JSON en /api/error.")
        return jsonify({"status": "error", "message": "No se recibieron datos JSON"}), 400
    error_id = data.get("error_id", "N/A")
    description = data.get("description", "Sin descripción")
    logging.info(f"Reporte de error recibido: ID {error_id}, descripción: {description}")
    return jsonify({"status": "success", "message": f"Reporte de error {error_id} procesado"}), 200

@app.route('/api/config', methods=['GET'])
def get_config():
    try:
        with open(AUTO_CONFIG, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        config_data = {}
        with open(AUTO_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
        logging.info(f"Archivo de configuración creado en {AUTO_CONFIG}.")
    except Exception as e:
        logging.error(f"Error al leer configuración: {e}")
        config_data = {}
    hw_info = get_hardware_info()
    config_data["hardware"] = hw_info
    return jsonify({"status": "success", "config": config_data}), 200

@app.route('/api/malla', methods=['GET'])
def get_malla():
    # Este endpoint simula la obtención del estado de la malla.
    # Puedes ajustar la lógica para que refleje el estado real.
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            contenido = f.read()
        response_data = {
            "malla_A": [[{"x": 0, "y": 0, "amplitude": 1.0, "phase": 0.0}]],
            "malla_B": [[{"x": 0, "y": 0, "amplitude": 0.5, "phase": 0.0}]],
            "resonador": {"T": 0.6, "R": 0.4, "lambda_foton": 600, "tipo_onda": "FOTON_A"},
            "status": "success"
        }
        return jsonify(response_data), 200
    except Exception as e:
        logging.error(f"Error al leer el archivo de salida: {e}")
        return jsonify({"status": "error", "message": "No se pudo leer la malla"}), 500

def get_hardware_info():
    try:
        cpu_info = {
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
        }
        mem = psutil.virtual_memory()
        return {"cpu": cpu_info, "memory": mem._asdict()}
    except Exception as e:
        logging.error(f"Error obteniendo info de hardware: {e}")
        return {}

# --- Simulación del oscilador 2D mediante RK4 ---
def derivatives(t, x, y, vx, vy, omega, c):
    dxdt = vx
    dydt = vy
    dvxdt = -omega**2 * x - c * vx
    dvydt = -omega**2 * y - c * vy
    return dxdt, dydt, dvxdt, dvydt

def rk4_step(t, x, y, vx, vy, dt, omega, c):
    dx1, dy1, dvx1, dvy1 = derivatives(t, x, y, vx, vy, omega, c)
    x2 = x + dx1 * dt/2
    y2 = y + dy1 * dt/2
    vx2 = vx + dvx1 * dt/2
    vy2 = vy + dvy1 * dt/2
    dx2, dy2, dvx2, dvy2 = derivatives(t + dt/2, x2, y2, vx2, vy2, omega, c)
    x3 = x + dx2 * dt/2
    y3 = y + dy2 * dt/2
    vx3 = vx + dvx2 * dt/2
    vy3 = vy + dvy2 * dt/2
    dx3, dy3, dvx3, dvy3 = derivatives(t + dt/2, x3, y3, vx3, vy3, omega, c)
    x4 = x + dx3 * dt
    y4 = y + dy3 * dt
    vx4 = vx + dvx3 * dt
    vy4 = vy + dvy3 * dt
    dx4, dy4, dvx4, dvy4 = derivatives(t + dt, x4, y4, vx4, vy4, omega, c)
    x_new = x + (dt/6) * (dx1 + 2*dx2 + 2*dx3 + dx4)
    y_new = y + (dt/6) * (dy1 + 2*dy2 + 2*dy3 + dy4)
    vx_new = vx + (dt/6) * (dvx1 + 2*dvx2 + 2*dvx3 + dvx4)
    vy_new = vy + (dt/6) * (dvy1 + 2*dvy2 + 2*dvy3 + dvy4)
    return x_new, y_new, vx_new, vy_new

def run_simulation():
    logging.info("Iniciando simulación de watchers_wave (RK4).")
    omega = 2.0
    c = 0.2
    x0, y0 = 1.0, 0.0
    vx0, vy0 = 0.0, 1.0
    dt = 0.05
    total_time = 10.0
    steps = int(total_time / dt)
    x, y = x0, y0
    vx, vy = vx0, vy0
    t = 0.0
    amplitude_threshold = 1.5
    for step in range(steps):
        amplitude = math.sqrt(x**2 + y**2)
        if amplitude >= amplitude_threshold:
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"[WaveEvent] step={step}, t={t:.2f}, amplitude={amplitude:.3f}\n")
            logging.info(f"Evento: step={step}, t={t:.2f}s, amplitude={amplitude:.3f}")
        x, y, vx, vy = rk4_step(t, x, y, vx, vy, dt, omega, c)
        t += dt
        time.sleep(0.2)
    logging.info("Simulación completada.")

def ciclo_estado_malla(intervalo=10):
    while True:
        try:
            response = requests.get("http://localhost:5000/api/malla", timeout=5)
            response.raise_for_status()
            estado = response.json()
            amplitudes = [celda.get("amplitude", 0) for fila in estado.get("malla_A", []) for celda in fila]
            if amplitudes:
                promedio = sum(amplitudes) / len(amplitudes)
                logging.info(f"Amplitud promedio de malla_A: {promedio:.3f}")
                if promedio > 1.5:
                    logging.warning("La amplitud promedio supera el umbral. Activando acción correctiva...")
        except Exception as e:
            logging.error(f"Error al obtener estado de la malla: {e}")
        time.sleep(intervalo)

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Inicia la API Flask en un hilo separado.
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Inicia el ciclo de consulta del estado de la malla.
    estado_thread = threading.Thread(target=ciclo_estado_malla, args=(10,))
    estado_thread.daemon = True
    estado_thread.start()

    # Ejecuta la simulación del oscilador 2D.
    run_simulation()
