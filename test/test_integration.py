#!/usr/bin/env python3
"""
test_integration.py

Suite de pruebas de integración para el proyecto "watchers".
Se valida que el endpoint REST expuesto por malla_watcher (por ejemplo, /api/malla)
devuelva el estado actualizado de la malla y que las claves esperadas estén presentes.

Además, se verifica que la función integrar_estados() del módulo integrador combine
la información de watchers_wave y watcher_focus de forma correcta.
"""

import subprocess
import time
import requests
import pytest
import json

# URL del endpoint REST que expone el estado de la malla.
MALLA_ENDPOINT = "http://localhost:5000/api/malla"


# Fixture que inicia el servidor malla_watcher usando polling para confirmar que esté activo.
@pytest.fixture(scope="session", autouse=True)
def iniciar_servidor_malla():
    """
    Arranca el servidor malla_watcher.py en un proceso separado y espera hasta que
    el endpoint /api/malla responda (200 o 404), para luego ejecutar los tests.
    """
    process = subprocess.Popen(
        ["python", "modulo/malla_watcher.py"]
    )  # Ajusta la ruta según tu estructura
    timeout = 40
    start_time = time.time()
    while True:
        try:
            r = requests.get(MALLA_ENDPOINT, timeout=2)
            # Consideramos el servidor activo si responde 200 o 404 (ya que usamos un endpoint dummy)
            if r.status_code in (200, 404):
                break
        except Exception:
            pass
        if time.time() - start_time > timeout:
            raise TimeoutError(
                "El servidor malla_watcher no se inició en el tiempo esperado."
            )
        time.sleep(1)
    yield
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def estado_malla():
    """Consulta el endpoint REST y devuelve la respuesta JSON."""
    response = requests.get(MALLA_ENDPOINT, timeout=5)
    response.raise_for_status()
    return response.json()


def test_endpoint_status():
    """Verifica que el endpoint /api/malla retorne un código HTTP 200."""
    response = requests.get(MALLA_ENDPOINT, timeout=5)
    assert (
        response.status_code == 200
    ), f"Esperado status 200, obtenido {response.status_code}"


def test_estado_malla_structure(estado_malla):
    """
    Verifica que la respuesta tenga la estructura esperada:
      - Clave "status" con valor "success"
      - Claves "malla_A" y "malla_B" con datos
      - Clave "resonador" con atributos como tipo_onda, lambda_foton, T y R
    """
    assert "status" in estado_malla, "Falta la clave 'status' en la respuesta"
    assert estado_malla["status"] == "success", "El estado no es 'success'"

    for key in ["malla_A", "malla_B", "resonador"]:
        assert key in estado_malla, f"Falta la clave '{key}' en la respuesta"


def test_resonador_atributos(estado_malla):
    """Verifica que el bloque 'resonador' contenga los atributos necesarios."""
    resonador = estado_malla["resonador"]
    for attr in ["tipo_onda", "lambda_foton", "T", "R"]:
        assert attr in resonador, f"El resonador no tiene el atributo '{attr}'"


def test_malla_celdas(estado_malla):
    """
    Verifica que las mallas contengan al menos una celda y que cada celda tenga
    las propiedades 'x', 'y', 'amplitude' y 'phase'.
    """
    for malla_key in ["malla_A", "malla_B"]:
        malla = estado_malla[malla_key]
        assert (
            isinstance(malla, list) and len(malla) > 0
        ), f"La {malla_key} debe ser una lista no vacía."
        primera_fila = malla[0]
        assert (
            isinstance(primera_fila, list) and len(primera_fila) > 0
        ), f"La {malla_key} debe tener filas no vacías."
        celda = primera_fila[0]
        for prop in ["x", "y", "amplitude", "phase"]:
            assert prop in celda, f"La celda no contiene la propiedad '{prop}'"


def test_actualizacion_periodica():
    """
    Verifica que tras dos consultas consecutivas con un breve lapso (por ejemplo, 10 segundos)
    se observe una actualización en el estado (por ejemplo, cambios en las amplitudes).
    """
    estado1 = requests.get(MALLA_ENDPOINT, timeout=5).json()
    time.sleep(10)
    estado2 = requests.get(MALLA_ENDPOINT, timeout=5).json()
    cambio_detectado = False
    for fila1, fila2 in zip(estado1.get("malla_A", []), estado2.get("malla_A", [])):
        for celda1, celda2 in zip(fila1, fila2):
            if celda1.get("amplitude") != celda2.get("amplitude"):
                cambio_detectado = True
                break
        if cambio_detectado:
            break
    assert (
        cambio_detectado
    ), "No se detectó cambio en las amplitudes de malla_A tras el intervalo."


def test_integrador_estados():
    """
    Verifica que la función integrar_estados() del integrador combine la información
    de watchers_wave y watcher_focus en un diccionario que contenga las claves esperadas.
    """
    from integrador import integrar_estados

    estado_global = integrar_estados()

    # Comprobar que se tengan ambas claves
    assert (
        "watchers_wave" in estado_global
    ), "Falta la clave 'watchers_wave' en el estado integrado"
    assert (
        "watcher_focus" in estado_global
    ), "Falta la clave 'watcher_focus' en el estado integrado"

    # Validación adicional para cada bloque
    if estado_global["watchers_wave"]:
        assert (
            "hardware" in estado_global["watchers_wave"]
        ), "El bloque 'watchers_wave' debe contener 'hardware'"
    if estado_global["watcher_focus"]:
        assert (
            "focus_state" in estado_global["watcher_focus"]
        ), "El bloque 'watcher_focus' debe contener 'focus_state'"


if __name__ == "__main__":
    import pytest

    pytest.main()
