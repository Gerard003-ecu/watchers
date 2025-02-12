#!/usr/bin/env python3
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

from enum import Enum

# Enumerado para definir tipos de onda (si se desea extender)
class TipoOnda(Enum):
    FOTON_A = 1
    FOTON_B = 2

class Cell:
    def __init__(self, x, y, amplitude=0.0, phase=0.0, q=0.0):
        """
        Representa una celda de la malla con coordenadas (x, y).
        - amplitude: Nivel de energía o "problema" en la celda.
        - phase: Fase de la señal (opcional).
        - q: Valor del campo escalar asociado a la celda.
        """
        self.x = x
        self.y = y
        self.amplitude = amplitude
        self.phase = phase
        self.q = q

    def __repr__(self):
        return (f"Cell({self.x}, {self.y}, amplitude={self.amplitude:.2f}, "
                f"phase={self.phase:.2f}, q={self.q:.2f})")
    
    def to_dict(self):
        """Devuelve un diccionario con la representación de la celda."""
        return {
            "x": self.x,
            "y": self.y,
            "amplitude": self.amplitude,
            "phase": self.phase,
            "q": self.q
        }

class PhosWave:
    def __init__(self, coef_transmision=0.5, coef_reflexion=0.5, 
                 tipo_onda=TipoOnda.FOTON_A, lambda_foton=None):
        """
        Inicializa el resonador "PhosWave" con:
          - coef_transmision (T): Fracción de la señal transmitida.
          - coef_reflexion (R): Fracción de la señal retenida/reflejada.
          - tipo_onda: Tipo de onda (por ejemplo, un enumerado).
          - lambda_foton: Longitud de onda del fotón (en nm) que afecta la transmisión.
        Se asume que coef_transmision + coef_reflexion == 1.
        """
        if abs(coef_transmision + coef_reflexion - 1.0) > 1e-6:
            raise ValueError("Los coeficientes deben sumar 1.")
        self.T = coef_transmision
        self.R = coef_reflexion
        self.tipo_onda = tipo_onda
        self.lambda_foton = lambda_foton

    def ajustar_coeficientes(self, nuevos_T, nuevos_R):
        """
        Actualiza los coeficientes y valida que sumen 1.
        """
        if abs(nuevos_T + nuevos_R - 1.0) > 1e-6:
            raise ValueError("Los coeficientes deben sumar 1.")
        self.T = nuevos_T
        self.R = nuevos_R

    def transmitir(self, celda_A, celda_B):
        """
        Transfiere la señal desde celda_A a celda_B, modulada por un factor que depende
        de lambda_foton y del campo escalar Q presente en celda_A.
        """
        factor = 1.0
        if self.lambda_foton:
            factor = 500.0 / self.lambda_foton  # Valor de referencia: 500 nm
        
        modulador = 1 + celda_A.q  # Se incorpora la influencia del campo escalar Q.
        
        transmision = self.T * factor * celda_A.amplitude * modulador
        celda_B.amplitude += transmision
        celda_A.amplitude *= self.R
        return celda_A, celda_B

class Electron:
    def __init__(self, coef_interaccion=0.3):
        """
        Representa el componente estabilizador "Electron".
        - coef_interaccion: Factor que determina cuánto reduce la amplitud en la celda.
        """
        self.coef_interaccion = coef_interaccion

    def interactuar(self, celda):
        """
        Aplica la interacción estabilizadora a la celda, reduciendo la amplitud.
        """
        correccion = self.coef_interaccion * celda.amplitude
        celda.amplitude -= correccion
        return celda

def aplicar_resonador_a_mallas(resonador, malla_A, malla_B):
    """
    Recorre las celdas de ambas mallas y aplica la transmisión del resonador PhosWave
    a cada par de celdas correspondientes.
    Se asume que malla_A y malla_B tienen la misma dimensión.
    """
    for i in range(len(malla_A)):
        for j in range(len(malla_A[i])):
            resonador.transmitir(malla_A[i][j], malla_B[i][j])

def aplicar_electron_a_malla(electron, malla):
    """
    Recorre la malla y aplica la interacción estabilizadora del Electron a cada celda.
    """
    for fila in malla:
        for celda in fila:
            electron.interactuar(celda)

# Ejemplo de uso:
if __name__ == "__main__":
    filas, columnas = 3, 3

    # Creamos la malla A con una amplitud inicial de 1.0 y un valor Q que depende de la posición
    malla_A = [
        [Cell(x, y, amplitude=1.0, phase=0.0, q=0.1 * (x + y)) for x in range(columnas)]
        for y in range(filas)
    ]

    # La malla B se inicializa sin energía y sin campo escalar (q=0)
    malla_B = [
        [Cell(x, y, amplitude=0.0, phase=0.0, q=0.0) for x in range(columnas)]
        for y in range(filas)
    ]

    # Instanciamos el resonador PhosWave con un fotón de 600 nm
    resonador = PhosWave(coef_transmision=0.6, coef_reflexion=0.4, 
                         tipo_onda=TipoOnda.FOTON_A, lambda_foton=600)

    # Instanciamos el estabilizador Electron
    electron = Electron(coef_interaccion=0.3)

    # Aplicamos el resonador a las mallas
    aplicar_resonador_a_mallas(resonador, malla_A, malla_B)
    # Aplicamos la interacción del electron a la malla B para estabilizar la energía transmitida
    aplicar_electron_a_malla(electron, malla_B)

    # Imprimimos el estado final de ambas mallas
    print("Malla A:")
    for fila in malla_A:
        print(fila)

    print("\nMalla B:")
    for fila in malla_B:
        print(fila)
