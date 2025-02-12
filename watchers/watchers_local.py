import subprocess
import logging
from pathlib import Path
from .config import LOCAL_SCRIPT_PATH, LOCAL_TIMEOUT, USE_PLACEHOLDER
from .watchers_comm import send_error

# Configurar logger
logger = logging.getLogger(__name__)

PLACEHOLDER_PREFIX = "[LOCAL-LLM] (Placeholder) Sugerencia: "
ERROR_PREFIX = "[ERROR] "
DEFAULT_SUGGESTION = "Revisa la sintaxis y considera mejores prácticas."

# Configuración de placeholders
PLACEHOLDER_RULES = {
    "xml": "Por favor, imprime tu análisis y correcciones.",
    "css": "Optimiza las reglas CSS para mejorar la legibilidad.",
    "html": "Valida la estructura HTML y considera accesibilidad.",
    "python": "Revisa PEP-8 y posibles anti-patrones.",
}

def get_suggestions_local(code_snippet: str) -> str:
    """
    Obtiene sugerencias de mejora para el código proporcionado, usando un LLM local
    o respuestas predefinidas según la configuración.
    """
    if not isinstance(code_snippet, str) or not code_snippet.strip():
        logger.warning("Código recibido vacío o no válido")
        return f"{ERROR_PREFIX}Input inválido para análisis"

    if USE_PLACEHOLDER:
        return _generate_placeholder_suggestion(code_snippet)

    return _invoke_local_llm(code_snippet)

def _generate_placeholder_suggestion(code: str) -> str:
    """
    Genera sugerencias simuladas basadas en patrones en el código.
    """
    code_lower = code.strip().lower()
    for pattern, suggestion in PLACEHOLDER_RULES.items():
        if pattern in code_lower:
            return f"{PLACEHOLDER_PREFIX}{suggestion}"
    return f"{PLACEHOLDER_PREFIX}{DEFAULT_SUGGESTION}"

def _invoke_local_llm(code: str) -> str:
    """
    Ejecuta el LLM local mediante el script configurado.
    """
    prompt = f"Revisa el siguiente código y sugiere mejoras:\n{code}"
    script_path = Path(LOCAL_SCRIPT_PATH)

    try:
        result = subprocess.run(
            [str(script_path), prompt],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=LOCAL_TIMEOUT
        )
        return _process_llm_output(result.stdout)
        
    except subprocess.TimeoutExpired as e:
        logger.error("Tiempo de espera agotado para LLM local")
        send_error("LOCAL_LLM_TIMEOUT", f"Timeout de {LOCAL_TIMEOUT}s al invocar LLM local: {e}")
        return f"{ERROR_PREFIX}Timeout ({LOCAL_TIMEOUT}s)"
        
    except subprocess.CalledProcessError as e:
        logger.error("Error en ejecución de LLM: %s", e.stderr)
        send_error("LOCAL_LLM_ERROR", f"Error en ejecución de LLM local: {e.stderr}")
        return f"{ERROR_PREFIX}{e.stderr.strip() or 'Error desconocido'}"
        
    except Exception as e:
        logger.exception("Error inesperado al invocar LLM local")
        send_error("LOCAL_LLM_EXCEPTION", f"Excepción inesperada al invocar LLM local: {str(e)}")
        return f"{ERROR_PREFIX}{str(e)}"

def _process_llm_output(raw_output: str) -> str:
    """
    Limpia y formatea la salida del LLM.
    """
    cleaned = raw_output.strip()
    if not cleaned:
        return f"{ERROR_PREFIX}Respuesta vacía del LLM"
    if cleaned.startswith(ERROR_PREFIX):
        return cleaned
    return f"[LOCAL-LLM] Sugerencias:\n{cleaned}"
