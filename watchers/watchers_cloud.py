import os
import openai
import logging
from typing import Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential

# Excepciones de OpenAI
Timeout = openai.APITimeoutError
APIError = openai.APIError
AuthenticationError = openai.AuthenticationError
RateLimitError = openai.RateLimitError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4")
MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "512"))
TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))

openai.api_key = os.getenv("API_key")
openai.timeout = TIMEOUT

ERROR_MESSAGES = {
    "no_api_key": (
        "[Cloud Error] La clave API de OpenAI no está configurada. "
        "Asegúrate de establecer la variable de entorno OPENAI_API_KEY."
    ),
    "empty_response": "[Cloud Error] La respuesta del agente en la nube está vacía o no contiene sugerencias.",
    "timeout": "[Cloud Error] La solicitud a la API ha excedido el tiempo de espera.",
    "rate_limit": "[Cloud Error] Límite de tasa excedido. Por favor, inténtalo de nuevo más tarde.",
    "auth_error": "[Cloud Error] Error de autenticación. Verifica tu clave API.",
    "generic_error": "[Cloud Error] Ocurrió un error al llamar al agente en la nube: {error}",
    "invalid_code": "El código proporcionado no parece ser válido.",
}


def get_suggestions_cloud(code_snippet: str) -> str:
    """
    Envía el código a la API de OpenAI y devuelve sugerencias de mejora.
    """
    logger.info("Iniciando solicitud a la API de OpenAI...")

    if (
        not code_snippet
        or not isinstance(code_snippet, str)
        or not code_snippet.strip()
    ):
        logger.warning("Código recibido vacío o no válido.")
        return ERROR_MESSAGES["invalid_code"]

    if not openai.api_key:
        logger.error("Clave API no configurada.")
        return ERROR_MESSAGES["no_api_key"]

    try:
        messages = _build_messages(code_snippet)
        response = _call_openai_api(messages)
        return _process_api_response(response)
    except Timeout:
        logger.error("Timeout en la solicitud a la API")
        return ERROR_MESSAGES["timeout"]
    except RateLimitError:
        logger.error("Límite de tasa excedido")
        return ERROR_MESSAGES["rate_limit"]
    except AuthenticationError:
        logger.error("Error de autenticación")
        return ERROR_MESSAGES["auth_error"]
    except APIError as e:
        logger.error(f"Error en la API: {e}")
        return ERROR_MESSAGES["generic_error"].format(error=str(e))
    except Exception as e:
        logger.exception("Error inesperado")
        return ERROR_MESSAGES["generic_error"].format(error=str(e))


def _build_messages(code: str) -> List[Dict[str, str]]:
    """
    Construye los mensajes para la API de OpenAI.
    """
    return [
        {
            "role": "system",
            "content": (
                "Eres un asistente experto en revisión de código. "
                "Proporciona sugerencias concisas y útiles para mejorar el código."
            ),
        },
        {"role": "user", "content": f"Revisa este código y sugiere mejoras:\n{code}"},
    ]


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=(Timeout | RateLimitError),
)
def _call_openai_api(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Realiza la llamada a la API de OpenAI con reintentos en caso de Timeout o RateLimit.
    """
    return openai.ChatCompletion.create(
        model=DEFAULT_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        request_timeout=TIMEOUT,
        top_p=0.9,
        frequency_penalty=0.3,
        presence_penalty=0.3,
    )


def _process_api_response(response: Dict[str, Any]) -> str:
    """
    Procesa la respuesta de la API y extrae las sugerencias.
    """
    choices = response.get("choices")
    if not choices or not isinstance(choices, list) or len(choices) == 0:
        logger.error("Respuesta vacía de la API")
        return ERROR_MESSAGES["empty_response"]

    message = choices[0].get("message", {})
    content = message.get("content", "").strip()
    if not content:
        logger.error("Respuesta de la API sin contenido")
        return ERROR_MESSAGES["empty_response"]

    logger.info("Sugerencias recibidas exitosamente")
    return content
