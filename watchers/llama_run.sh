#!/bin/bash
# -----------------------------------------------------------
# Script para invocar llama-cli desde un entorno virtual,
# generando sugerencias basadas en un prompt.
# -----------------------------------------------------------

set -euo pipefail  # Falla en errores, variables no definidas y pipes fallidos

# Agregar la ruta del ejecutable llama-cli al PATH
export PATH="/home/gerardo/Documentos/proyectos/watchers/watchers/watchers-env/bin:$PATH"

# Agregar la ruta donde se encuentra libllama.so al LD_LIBRARY_PATH,
# usando la sintaxis ${LD_LIBRARY_PATH:-} para evitar errores si la variable no está definida.
export LD_LIBRARY_PATH="/home/gerardo/Documentos/proyectos/watchers/llama.cpp/build:${LD_LIBRARY_PATH:-}"

# -----------------------------------------------------------
# Configuración
# -----------------------------------------------------------
VENV_PATH="/home/gerardo/Documentos/proyectos/watchers/watchers/watchers-env"
MODEL_PATH="/home/gerardo/.lmstudio/models/lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-Q4_K_M.gguf"
N_PREDICT=32
THREADS=4
CTX_SIZE=1024
TEMP=0.7
TOP_P=0.9
REPEAT_PENALTY=1.2
GPU_LAYERS=8
ERROR_LOG="error.log"

# -----------------------------------------------------------
# Funciones de utilidad
# -----------------------------------------------------------
log_error() {
    echo "[ERROR] $1" >&2
}

validate_file() {
    if [ ! -f "$1" ]; then
        log_error "El archivo $1 no existe."
        exit 1
    fi
}

validate_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "$1 no está instalado o no se encuentra en el PATH."
        exit 1
    fi
}

# -----------------------------------------------------------
# Validaciones iniciales
# -----------------------------------------------------------
if [ "$#" -lt 1 ]; then
    log_error "Uso: $0 'prompt'"
    exit 1
fi

validate_file "$VENV_PATH/bin/activate"
validate_file "$MODEL_PATH"
validate_command "llama-cli"

# -----------------------------------------------------------
# Ejecución
# -----------------------------------------------------------
source "$VENV_PATH/bin/activate"
echo "[INFO] Entorno virtual activado."

# Limpia el archivo de log de errores
> "$ERROR_LOG"

echo "[INFO] Ejecutando llama-cli..."
OUTPUT=$(/home/gerardo/Documentos/proyectos/watchers/watchers/watchers-env/bin/llama-cli \
    --model "$MODEL_PATH" \
    --prompt "$1" \
    --n-predict "$N_PREDICT" \
    --threads "$THREADS" \
    --ctx-size "$CTX_SIZE" \
    --temp "$TEMP" \
    --top-p "$TOP_P" \
    --no-conversation \
    --ignore-eos \
    --repeat-penalty "$REPEAT_PENALTY" \
    --flash-attn \
    --gpu-layers "$GPU_LAYERS" \
    --prio 2 \
    --no-warmup \
    2>> "$ERROR_LOG")
EXIT_CODE=$?

deactivate
echo "[INFO] Entorno virtual desactivado."

if [ $EXIT_CODE -ne 0 ]; then
    log_error "Error al ejecutar llama-cli. Consulta $ERROR_LOG para más detalles."
    exit $EXIT_CODE
fi

echo "$OUTPUT"
