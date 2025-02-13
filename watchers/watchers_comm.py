import requests
import uuid
import datetime
import json
import time
import threading
import logging
import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Configuración global por defecto para comunicarse con watchers_wave.
WATCHERS_CONFIG = {
    "watchers_wave_base_url": "http://localhost:5000",
    "endpoints": {
        "event": "/api/event",
        "error": "/api/error",
        "config": "/api/config",
    },
}


def load_local_config(config_file="config.yaml"):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
            if not isinstance(config_data, dict) or "watchers_wave" not in config_data:
                logging.warning(
                    "La configuración local no contiene la sección 'watchers_wave'. Se usarán valores por defecto."
                )
                return
            WATCHERS_CONFIG["watchers_wave_base_url"] = config_data[
                "watchers_wave"
            ].get("base_url", WATCHERS_CONFIG["watchers_wave_base_url"])
            endpoints = config_data["watchers_wave"].get("endpoints", {})
            WATCHERS_CONFIG["endpoints"].update(endpoints)
            logging.info("Configuración local cargada correctamente.")
    except Exception as e:
        logging.warning(
            f"No se pudo cargar la configuración local ({config_file}): {e}"
        )


def send_event(file_path, suggestions):
    url = (
        WATCHERS_CONFIG["watchers_wave_base_url"]
        + WATCHERS_CONFIG["endpoints"]["event"]
    )
    event_data = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "file_path": file_path,
        "suggestions": suggestions,
        "additional_data": {},
    }
    try:
        response = requests.post(url, json=event_data, timeout=5)
        if response.status_code == 200:
            logging.info(f"Evento enviado exitosamente: {event_data['event_id']}")
        else:
            logging.error(
                f"Error al enviar evento: {response.status_code} {response.text}"
            )
    except Exception as e:
        logging.error(f"Excepción al enviar evento: {e}")


def send_error(error_code, description, additional_data=None):
    url = (
        WATCHERS_CONFIG["watchers_wave_base_url"]
        + WATCHERS_CONFIG["endpoints"]["error"]
    )
    error_data = {
        "error_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "error_code": error_code,
        "description": description,
        "additional_data": additional_data or {},
    }
    try:
        response = requests.post(url, json=error_data, timeout=5)
        if response.status_code == 200:
            logging.info(
                f"Reporte de error enviado exitosamente: {error_data['error_id']}"
            )
        else:
            logging.error(
                f"Error al enviar reporte de error: {response.status_code} {response.text}"
            )
    except Exception as e:
        logging.error(f"Excepción al enviar reporte de error: {e}")


def update_config_periodically(interval=60):
    url = (
        WATCHERS_CONFIG["watchers_wave_base_url"]
        + WATCHERS_CONFIG["endpoints"]["config"]
    )
    while True:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                config_json = response.json()
                if config_json.get("status") == "success":
                    new_config = config_json.get("config", {})
                    logging.info(f"Nueva configuración recibida: {new_config}")
                    # Aquí se pueden actualizar parámetros internos si es necesario.
                else:
                    logging.error(
                        "Error en respuesta de configuración: "
                        + config_json.get("message", "")
                    )
            else:
                logging.error(f"Error al obtener configuración: {response.status_code}")
        except Exception as e:
            logging.error(f"Excepción al obtener configuración: {e}")
        time.sleep(interval)


def run_config_updater():
    thread = threading.Thread(target=update_config_periodically, args=(60,))
    thread.daemon = True
    thread.start()
