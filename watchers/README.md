# Watchers

Proyecto para observar cambios en archivos (HTML, CSS, etc.) y solicitar 
sugerencias a un LLM, ya sea local (llama.cpp) o en la nube (ChatGPT o3 mini high).

## Requerimientos
- Python 3.7+
- pip install watchdog
- (Opcional) llama.cpp compilado

## Uso
```bash
source venv/bin/activate
python main.py /ruta/a/tu/proyecto

### Estructura del directorio y archivos
watchers_project/
├─ llama_watchers/               # Entorno virtual (¿duplicado?)
├─ watchers/
│   ├─ main.py                   # Punto de entrada principal
│   ├─ watchers_local.py         # Lógica para el modo local (llama.cpp)
│   ├─ watchers_cloud.py         # Lógica para el modo en la nube (OpenAI)
│   ├─ watchers_utils.py         # Funciones auxiliares (observar archivos, etc.)
│   ├─ config.py                 # Configuración global (modo, rutas, API keys, etc.)
│   └─ README.md                 # Documentación del proyecto
├─ watchers-env                  # Entorno virtual principal
└─ requirements.txt              # Archivo con las dependencias del proyecto