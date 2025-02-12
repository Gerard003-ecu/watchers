"""
malla_watcher.py

Este módulo define la estructura de la malla hexagonal (inspirada en grafeno) y 
los módulos que modelan la transmisión de la señal en el sistema:
- PhosWave: el resonador de onda variable (simula un fotón) que ahora incorpora un 
  campo escalar Q para modular la transmisión.
- Electron: el estabilizador que reduce la amplitud, simulando la acción de 
  partículas cargadas que neutralizan la energía excesiva.

La malla se utiliza para representar el flujo de "energía" del código.
"""

import random
import time
import threading
from flask import Flask, jsonify
from enum import Enum

# -----------------------------------------------------------
# Enumerado para definir tipos de onda
# -----------------------------------------------------------
class TipoOnda(Enum):
    FOTON_A = 1
    FOTON_B = 2

# -----------------------------------------------------------
# Clase Cell
# -----------------------------------------------------------
class Cell:
    def __init__(self, x, y, amplitude=0.0, phase=0.0, q=0.0):
        self.x = x
        self.y = y
        self.amplitude = amplitude
        self.phase = phase
        self.q = q

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "amplitude": self.amplitude,
            "phase": self.phase,
            "q": self.q
        }
    
    def __repr__(self):
        return (f"Cell({self.x}, {self.y}, amplitude={self.amplitude:.2f}, "
                f"phase={self.phase:.2f}, q={self.q:.2f})")

# -----------------------------------------------------------
# Clases PhosWave y Electron
# -----------------------------------------------------------
class PhosWave:
    def __init__(self, coef_transmision=0.6, coef_reflexion=0.4, lambda_foton=600):
        self.T = coef_transmision
        self.R = coef_reflexion
        self.lambda_foton = lambda_foton

    def transmitir(self, celda_A, celda_B):
        """
        Simula la transmisión de onda entre celdas de la malla
        """
        factor = 500.0 / self.lambda_foton
        modulador = 1 + celda_A.q
        transmision = self.T * factor * celda_A.amplitude * modulador
        celda_B.amplitude += transmision
        celda_A.amplitude *= self.R

class Electron:
    def __init__(self, coef_interaccion=0.3):
        self.coef_interaccion = coef_interaccion

    def interactuar(self, celda):
        """
        Simula la interacción de electrones con la malla
        """
        celda.amplitude -= self.coef_interaccion * celda.amplitude

# -----------------------------------------------------------
# Inicialización de mallas
# -----------------------------------------------------------
filas, columnas = 5, 5
malla_A = [[Cell(x, y, amplitude=1.0, q=0.1 * (x + y)) for x in range(columnas)] for y in range(filas)]
malla_B = [[Cell(x, y) for x in range(columnas)] for y in range(filas)]

resonador = PhosWave()
electron = Electron()

# -----------------------------------------------------------
# Funciones de actualización de la malla
# -----------------------------------------------------------
def actualizar_malla():
    """
    Aplica la transmisión de onda y la interacción electrónica en la malla
    """
    for i in range(len(malla_A)):
        for j in range(len(malla_A[i])):
            resonador.transmitir(malla_A[i][j], malla_B[i][j])
            electron.interactuar(malla_B[i][j])

def ciclo_actualizacion():
    """
    Inicia la actualización periódica de la malla.
    """
    while True:
        actualizar_malla()
        time.sleep(5)

# Iniciar la actualización en segundo plano
threading.Thread(target=ciclo_actualizacion, daemon=True).start()

# -----------------------------------------------------------
# Servidor Flask para exponer los datos de la malla
# -----------------------------------------------------------
app = Flask(__name__)

@app.route("/api/malla", methods=["GET"])
def obtener_malla():
    """
    Retorna el estado actual de la malla en formato JSON
    """
    return jsonify({
        "status": "success",
        "malla_A": [[celda.to_dict() for celda in fila] for fila in malla_A],
        "malla_B": [[celda.to_dict() for celda in fila] for fila in malla_B],
        "resonador": {
            "tipo_onda": "senoidal",
            "lambda_foton": resonador.lambda_foton,
            "T": resonador.T,
            "R": resonador.R
        }
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # Usa un puerto dinámico si está definido
    print(f"🚀 Iniciando servidor de Malla Watcher en http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

