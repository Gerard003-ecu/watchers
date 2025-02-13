import os
from pathlib import Path

# -----------------------------------------------------------
# Configuración para la interacción con llama.cpp
# -----------------------------------------------------------

# Ruta al script bash para interactuar con llama.cpp
LOCAL_SCRIPT_PATH: Path = (
    Path(
        os.getenv(
            "LOCAL_SCRIPT_PATH",
            "/home/gerardo/Documentos/proyectos/mi-proyecto/watchers/llama_run.sh",
        )
    )
    .expanduser()
    .resolve()
)

# Tiempo máximo de espera (en segundos) para la llamada al modelo local.
try:
    LOCAL_TIMEOUT: int = int(os.getenv("LOCAL_TIMEOUT", "60"))
except ValueError as e:
    raise ValueError(
        f"LOCAL_TIMEOUT debe ser un número entero válido. Error: {e}"
    ) from e

# Modo de ejecución:
# - True: usar placeholder (simulación)
# - False: usar la versión real que invoca el script bash.
USE_PLACEHOLDER: bool = os.getenv("USE_PLACEHOLDER", "False").strip().lower() == "true"

# Detectar si estamos en GitHub Actions
RUNNING_IN_CI = os.getenv("GITHUB_ACTIONS") == "true"


# -----------------------------------------------------------
# Validación de la configuración
# -----------------------------------------------------------
def _validate_config() -> None:
    """
    Valida la configuración del módulo:
      - Verifica que el script exista y tenga permisos de ejecución si no se usa el placeholder.
      - Asegura que LOCAL_TIMEOUT sea mayor que 0.
    """
    if not USE_PLACEHOLDER and not RUNNING_IN_CI:
        if not LOCAL_SCRIPT_PATH.is_file():
            print(
                f"⚠️ Advertencia: El script {LOCAL_SCRIPT_PATH} no existe. Algunas funciones pueden no estar disponibles."
            )
        elif not os.access(LOCAL_SCRIPT_PATH, os.X_OK):
            print(
                f"⚠️ Advertencia: El script {LOCAL_SCRIPT_PATH} no tiene permisos de ejecución."
            )

    if LOCAL_TIMEOUT <= 0:
        raise ValueError(
            f"LOCAL_TIMEOUT debe ser mayor que 0. Valor actual: {LOCAL_TIMEOUT}"
        )


# Validar la configuración al importar el módulo
_validate_config()
