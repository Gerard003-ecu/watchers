#!/usr/bin/env python3
import requests
import json
import time

# Configuración de la URL base de watchers_wave (ajústala según tu entorno)
BASE_URL = "http://localhost:5000"
CONFIG_ENDPOINT = f"{BASE_URL}/api/config"
EVENT_ENDPOINT = f"{BASE_URL}/api/event"
ERROR_ENDPOINT = f"{BASE_URL}/api/error"

def test_send_event():
    event_data = {
        "event_id": "test-event-001",
        "timestamp": "2025-01-01T00:00:00Z",
        "file_path": "/ruta/al/test_file.txt",
        "suggestions": "Test de sugerencia de integración",
        "additional_data": {}
    }
    response = requests.post(EVENT_ENDPOINT, json=event_data)
    print("Test Send Event:", response.status_code, response.json())

def test_send_error():
    error_data = {
        "error_id": "test-error-001",
        "timestamp": "2025-01-01T00:00:00Z",
        "error_code": "TEST_ERROR",
        "description": "Este es un error de prueba para la integración",
        "additional_data": {}
    }
    response = requests.post(ERROR_ENDPOINT, json=error_data)
    print("Test Send Error:", response.status_code, response.json())

def test_get_config():
    response = requests.get(CONFIG_ENDPOINT)
    print("Test Get Config:", response.status_code)
    try:
        config = response.json()
        print(json.dumps(config, indent=4))
    except Exception as e:
        print("Error procesando la respuesta:", e)

if __name__ == "__main__":
    print("Ejecutando test de integración para watchers_wave...")
    test_send_event()
    test_send_error()
    time.sleep(5)  # Espera para que el scheduler de errores (si está activo) haga sus ajustes
    test_get_config()
