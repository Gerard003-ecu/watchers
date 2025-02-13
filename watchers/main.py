#!/usr/bin/env python3
"""
Script para monitorear cambios en archivos y obtener sugerencias
usando procesamiento local o en la nube.
"""

import os
import sys
import time
import hashlib
import logging
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import watchers_local  # Módulo para procesamiento local
import watchers_cloud  # Módulo para procesamiento en la nube
from watchers_comm import load_local_config, run_config_updater, send_event, send_error

# Configuración general: se lee el umbral desde la variable de entorno, con valor por defecto 50
MAX_LINES_LOCAL = int(os.getenv("MAX_LINES_LOCAL", 50))
DEBOUNCE_TIME = 1.0  # Segundos entre procesamientos consecutivos del mismo archivo

# Configurar logging: nivel DEBUG para ver detalles de depuración y mensajes INFO para lo esencial.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ChangeHandler(FileSystemEventHandler):
    """Manejador de eventos con debounce, control de cambios reales y thread safety."""

    def __init__(self):
        super().__init__()
        self.last_processed = (
            {}
        )  # Almacena el último tiempo de procesamiento por archivo
        self.file_hashes = (
            {}
        )  # Almacena el hash MD5 del contenido previo de cada archivo
        self.lock = (
            threading.Lock()
        )  # Lock para garantizar acceso thread-safe a los diccionarios

    def on_modified(self, event):
        """Maneja modificaciones de archivos con verificación de cambios reales."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        current_time = time.time()

        # Verificar debounce de forma thread-safe
        with self.lock:
            if self._recently_processed(filepath, current_time):
                logging.debug(f"Omitiendo {filepath} por debounce.")
                return

        # Leer el contenido del archivo (fuera de la sección crítica para evitar bloqueos prolongados)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Error leyendo {filepath}: {e}")
            send_error("FILE_READ_ERROR", f"Error leyendo {filepath}: {e}")
            return

        # Verificar si el contenido ha cambiado, de forma thread-safe
        with self.lock:
            if not self._content_changed(filepath, content):
                logging.debug(f"No hay cambio en el contenido de {filepath}.")
                return
            # Actualiza el tiempo de último procesamiento
            self.last_processed[filepath] = current_time

        # Procesar el archivo (fuera del lock)
        self._process_file(filepath, content)

    def _recently_processed(self, filepath, current_time):
        """Verifica si el archivo fue procesado recientemente."""
        last_time = self.last_processed.get(filepath, 0)
        return (current_time - last_time) < DEBOUNCE_TIME

    def _content_changed(self, filepath, content):
        """Verifica si el contenido ha cambiado usando hash MD5."""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if self.file_hashes.get(filepath) == content_hash:
            return False
        self.file_hashes[filepath] = content_hash
        return True

    def _process_file(self, filepath, content):
        """Ejecuta el procesamiento del archivo según su tamaño."""
        num_lines = content.count("\n") + 1
        logging.info(f"Procesando: {filepath} ({num_lines} líneas)")

        if num_lines <= MAX_LINES_LOCAL:
            logging.debug("Usando agente local.")
            suggestions = watchers_local.get_suggestions_local(content)
        else:
            logging.debug("Usando agente en la nube.")
            suggestions = watchers_cloud.get_suggestions_cloud(content)

        logging.info(f"Sugerencias para {filepath}:\n{suggestions}\n")
        # Enviar evento a watchers_wave con las sugerencias generadas
        send_event(str(filepath), suggestions)


def main():
    # Construir la ruta absoluta al archivo config.yaml ubicado en la misma carpeta que main.py
    config_path = Path(__file__).parent / "config.yaml"
    load_local_config(str(config_path))
    run_config_updater()

    if len(sys.argv) != 2:
        logging.error("Uso: python main.py /ruta/monitorizar")
        sys.exit(1)

    path_to_watch = Path(sys.argv[1])

    if not path_to_watch.is_dir():
        logging.error(f"La ruta {path_to_watch} no es un directorio válido")
        sys.exit(1)

    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=str(path_to_watch), recursive=True)

    try:
        observer.start()
        logging.info(f"Observando: {path_to_watch} (Presiona Ctrl+C para salir)")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Deteniendo observador...")
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        send_error("OBSERVER_ERROR", f"Error inesperado en el observador: {e}")
        sys.exit(1)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    main()
