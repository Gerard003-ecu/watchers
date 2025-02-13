#!/usr/bin/env python3
"""
watcher_focus: Módulo para la simulación del oscilador extendido en un espacio vectorial R^3,
basado en un modelo modificado de Van der Pol con una variable adaptativa (z).

Este módulo:
  - Integra un sistema de ecuaciones diferenciales:
      dx/dt = y
      dy/dt = μ(z) * (1 - x²) * y - x,   donde μ(z) = μ₀ + k * z
      dz/dt = -α*(z - z_target) + β*(|x|+|y| - threshold)
  - Calcula indicadores adicionales:
      • phase: el ángulo de la fase (atan2(y, x))
      • z_error: la desviación de z respecto a z_target
  - Ejecuta la simulación en un hilo de fondo, actualizando un estado global.
  - Consulta periódicamente el endpoint REST que expone el estado de la malla (definido en malla_watcher.py)
    para detectar áreas críticas y ajustar el enfoque o activar alertas.
  - Expone un endpoint Flask (/api/focus) para consultar el estado actual e indicadores.
  
Se incluye también una función dummy "some_focus_function" para facilitar las pruebas unitarias.
"""

import math
import time
import threading
import logging
import requests
import json
from flask import Flask, jsonify

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


# Función dummy para pruebas unitarias
def some_focus_function(input_data):
    """
    Función dummy para pruebas en watcher_focus.
    Toma un input y retorna un diccionario con un resultado simulado.
    """
    return {"result": f"Input procesado: {input_data}"}


# Parámetros del modelo
MU0 = 2.0  # Valor base de μ
K = 0.5  # Sensibilidad de μ respecto a z
ALPHA = 1.0  # Tasa de retorno de z al valor objetivo
BETA = 0.1  # Factor de corrección para z
THRESHOLD = 1.0  # Umbral para activar la corrección
Z_TARGET = 0.0  # Valor objetivo para z

# Estado global del oscilador extendido
current_state = {
    "t": 0.0,
    "x": None,
    "y": None,
    "z": None,
    "phase": None,
    "z_error": None,
}

state_lock = threading.Lock()


# --- Simulación del oscilador extendido (RK4 en R^3) ---
def derivatives(t, x, y, z, mu0=MU0):
    mu = mu0 + K * z
    dxdt = y
    dydt = mu * (1 - x**2) * y - x
    dzdt = -ALPHA * (z - Z_TARGET) + BETA * (abs(x) + abs(y) - THRESHOLD)
    return dxdt, dydt, dzdt


def rk4_step(t, x, y, z, dt, mu0=MU0):
    dx1, dy1, dz1 = derivatives(t, x, y, z, mu0)
    x2 = x + dx1 * dt / 2
    y2 = y + dy1 * dt / 2
    z2 = z + dz1 * dt / 2
    dx2, dy2, dz2 = derivatives(t + dt / 2, x2, y2, z2, mu0)
    x3 = x + dx2 * dt / 2
    y3 = y + dy2 * dt / 2
    z3 = z + dz2 * dt / 2
    dx3, dy3, dz3 = derivatives(t + dt / 2, x3, y3, z3, mu0)
    x4 = x + dx3 * dt
    y4 = y + dy3 * dt
    z4 = z + dz3 * dt
    dx4, dy4, dz4 = derivatives(t + dt, x4, y4, z4, mu0)
    x_new = x + (dt / 6) * (dx1 + 2 * dx2 + 2 * dx3 + dx4)
    y_new = y + (dt / 6) * (dy1 + 2 * dy2 + 2 * dy3 + dy4)
    z_new = z + (dt / 6) * (dz1 + 2 * dz2 + 2 * dz3 + dz4)
    return x_new, y_new, z_new


def update_indicators(t, x, y, z):
    phase = math.atan2(y, x)
    z_error = abs(z - Z_TARGET)
    return {"t": t, "x": x, "y": y, "z": z, "phase": phase, "z_error": z_error}


def simulate_watcher_focus(dt=0.01, total_time=30.0):
    logging.info("Iniciando simulación de watcher_focus (oscilador extendido en R^3).")
    t = 0.0
    x, y, z = 1.0, 0.0, 0.5  # Condiciones iniciales
    while t < total_time:
        x, y, z = rk4_step(t, x, y, z, dt)
        t += dt
        if int(t * 100) % 10 == 0:
            indicators = update_indicators(t, x, y, z)
            with state_lock:
                current_state.update(indicators)
            logging.info(
                f"t={t:.2f} | x={x:.3f} | y={y:.3f} | z={z:.3f} | phase={indicators['phase']:.3f} | z_error={indicators['z_error']:.3f}"
            )
        time.sleep(dt)
    logging.info("Simulación de watcher_focus completada.")


# --- Consulta al endpoint REST de la malla ---
MALLA_ENDPOINT = "http://localhost:5000/api/malla"


def obtener_estado_malla(timeout=5):
    try:
        response = requests.get(MALLA_ENDPOINT, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error al obtener el estado de la malla: {e}")
        return None


def actualizar_estado_watcher_focus():
    estado = obtener_estado_malla()
    if estado:
        celdas_criticas = []
        for fila in estado.get("malla_A", []):
            for celda in fila:
                if celda.get("amplitude", 0) > 1.5:
                    celdas_criticas.append(celda)
        logging.info(
            "Celdas críticas detectadas:\n" + json.dumps(celdas_criticas, indent=4)
        )
    else:
        logging.warning("No se pudo obtener el estado de la malla.")


def ciclo_watcher_focus(intervalo=10):
    while True:
        actualizar_estado_watcher_focus()
        time.sleep(intervalo)


# --- API con Flask para exponer el estado Focus ---
app_focus = Flask(__name__)


@app_focus.route("/api/focus", methods=["GET"])
def get_focus():
    with state_lock:
        state_copy = current_state.copy()
    return jsonify({"status": "success", "focus_state": state_copy}), 200


def run_focus_api():
    app_focus.run(host="0.0.0.0", port=6000)


# --- Programa Principal ---
def main():
    # Inicia la simulación en un hilo de fondo
    sim_thread = threading.Thread(
        target=simulate_watcher_focus, kwargs={"dt": 0.01, "total_time": 30.0}
    )
    sim_thread.daemon = True
    sim_thread.start()
    # Inicia la API Flask para exponer el estado de focus
    api_thread = threading.Thread(target=run_focus_api)
    api_thread.daemon = True
    api_thread.start()
    # Inicia el ciclo para consultar periódicamente el estado de la malla
    malla_thread = threading.Thread(target=ciclo_watcher_focus, args=(10,))
    malla_thread.daemon = True
    malla_thread.start()
    sim_thread.join()


if __name__ == "__main__":
    main()
