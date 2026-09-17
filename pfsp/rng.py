"""Primitivas de números aleatorios.

Toda la aleatoriedad del proyecto pasa por aquí, sobre el generador Mersenne
Twister del módulo `random` de la biblioteca estándar. Fijar la semilla una vez
con `random.seed(semilla)` en el punto de entrada hace que una corrida completa
sea reproducible de forma exacta.
"""

import random


def aleatorio_real():
    """Número real aleatorio uniforme en [0, 1)."""
    return random.random()


def aleatorio_entero(minimo, maximo):
    """Entero aleatorio uniforme en [minimo, maximo], ambos extremos incluidos."""
    return random.randint(minimo, maximo)
