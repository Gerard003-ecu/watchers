#!/bin/bash

# Script para ejecutar LLaMA en Watchers

# Definir la ruta del binario de LLaMA
LLAMA_BIN="/home/gerardo/Documentos/proyectos/mi-proyecto/llama.cpp/main"

# Verificar si el binario existe
if [ ! -f "$LLAMA_BIN" ]; then
    echo "⚠️ Error: No se encontró el binario de LLaMA en $LLAMA_BIN. Verifica la instalación."
    exit 1
fi

# Definir los parámetros por defecto
MODEL_PATH="/home/gerardo/Documentos/proyectos/mi-proyecto/llama.cpp/models/7B/ggml-model-q4_0.bin"
INPUT_TEXT="Hola, soy Watchers."
N_TOKENS=50

# Ejecutar LLaMA con los parámetros definidos
echo "🚀 Ejecutando LLaMA con el modelo en $MODEL_PATH"
$LLAMA_BIN -m "$MODEL_PATH" -p "$INPUT_TEXT" -n $N_TOKENS
