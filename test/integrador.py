#!/usr/bin/env python3
"""
integrador.py: Módulo integrador para centralizar la consulta de los estados de watchers_wave y watcher_focus.

Este script realiza lo siguiente:
  - Consulta el endpoint /api/config de watchers_wave (por defecto en http://localhost:5000/api/config).
  - Consulta el endpoint /api/focus de watcher_focus (por defecto en http://localhost:6000/api/focus).
  - Combina la información y la muestra en un JSON consolidado.

Puedes ejecutarlo manualmente o integrarlo en un proceso periódico.
"""

import requests
import json

# Define las URL de los endpoints
WATCHERS_WAVE_CONFIG_URL = "http://localhost:5000/api/config"
WATCHER_FOCUS_URL = "http://localhost:6000/api/focus"


def obtener_config_watchers_wave(timeout=5):
    """
    Consulta el endpoint de watchers_wave y devuelve la configuración en formato JSON.
    """
    try:
        response = requests.get(WATCHERS_WAVE_CONFIG_URL, timeout=timeout)
        response.raise_for_status()  # Lanza excepción si el código de estado HTTP no es 200
        return response.json()
    except Exception as e:
        print(f"Error obteniendo configuración de watchers_wave: {e}")
        return None


def obtener_estado_watcher_focus(timeout=5):
    """
    Consulta el endpoint de watcher_focus y devuelve el estado en formato JSON.
    """
    try:
        response = requests.get(WATCHER_FOCUS_URL, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error obteniendo estado de watcher_focus: {e}")
        return None


def integrar_estados():
    """
    Combina la información obtenida de ambos endpoints en un solo diccionario.
    """
    config_wave = obtener_config_watchers_wave()
    estado_focus = obtener_estado_watcher_focus()
    estado_global = {"watchers_wave": config_wave, "watcher_focus": estado_focus}
    return estado_global


def main():
    estado_global = integrar_estados()
    print(json.dumps(estado_global, indent=4))


if __name__ == "__main__":
    main()
