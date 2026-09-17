"""Validación de los parámetros de línea de comandos.

Los dos programas reciben los mismos parámetros en el mismo orden posicional; el
Memético agrega uno opcional al final. Validar aquí mantiene idénticos los
mensajes de error de ambos.
"""

import os
import sys
from collections import namedtuple

Parametros = namedtuple(
    "Parametros",
    "semilla entrada tam_pobla prob_c prob_m iteraciones freq_bl salida",
)


def _uso(script, con_busqueda_local):
    extra = " [frecuencia_bl]" if con_busqueda_local else ""
    print("Error en la entrada de los parametros")
    print(f"Uso: python {script} semilla archivo_instancia tam_poblacion prob_cruza "
          f"prob_mutacion iteraciones{extra} [salida.csv]")
    print("Donde:")
    print(" - semilla: valor entero no negativo [ejem: 1]")
    print(" - archivo_instancia: ruta del archivo de datos [ejem: data/ins_20_5_00.txt]")
    print(" - tam_poblacion: valor entero positivo [ejem: 60]")
    print(" - prob_cruza: valor real entre 0.0 y 1.0 con punto [ejem: 0.85]")
    print(" - prob_mutacion: valor real entre 0.0 y 1.0 con punto [ejem: 0.20]")
    print(" - iteraciones: valor entero positivo [ejem: 300]")
    if con_busqueda_local:
        print(" - frecuencia_bl: (opcional) cada cuántas generaciones aplicar la "
              "búsqueda local [ejem: 1]")
    print(" - salida.csv: (opcional) archivo donde registrar resultados")


def _entero(texto, nombre, minimo):
    try:
        valor = int(texto)
    except ValueError:
        print(f"Error: '{nombre}' debe ser un número entero.")
        sys.exit(1)
    if valor < minimo:
        print(f"Error: '{nombre}' debe ser un número entero mayor o igual a {minimo}.")
        sys.exit(1)
    return valor


def _probabilidad(texto, nombre, ejemplo):
    if "," in texto:
        print(f"Error: '{nombre}' debe usar punto decimal (ejem: {ejemplo}), no comas.")
        sys.exit(1)
    try:
        valor = float(texto)
    except ValueError:
        print(f"Error: '{nombre}' debe ser un número decimal entre 0.0 y 1.0.")
        sys.exit(1)
    if not 0.0 <= valor <= 1.0:
        print(f"Error: '{nombre}' debe estar entre 0.0 y 1.0.")
        sys.exit(1)
    return valor


def _parece_ruta(texto):
    return texto.endswith(".csv") or "/" in texto or "\\" in texto


def parsear_argumentos(argv, script, con_busqueda_local=False):
    """Valida argv y devuelve los parámetros ya convertidos.

    Ante cualquier parámetro inválido imprime el motivo y termina con código 1.
    """
    if len(argv) < 7:
        _uso(script, con_busqueda_local)
        sys.exit(1)

    semilla = _entero(argv[1], "semilla", minimo=0)

    entrada = argv[2]
    if not os.path.isfile(entrada):
        print(f"Error: El archivo de instancia '{entrada}' no existe.")
        sys.exit(1)

    tam_pobla = _entero(argv[3], "tam_poblacion", minimo=1)
    prob_c = _probabilidad(argv[4], "prob_cruza", "0.85")
    prob_m = _probabilidad(argv[5], "prob_mutacion", "0.20")
    iteraciones = _entero(argv[6], "iteraciones", minimo=1)

    # Los dos últimos son opcionales: `frecuencia_bl` es un entero y `salida.csv`
    # una ruta, así que se distinguen por su forma.
    freq_bl = 1
    salida = None
    opcionales = list(argv[7:])
    if con_busqueda_local and opcionales and not _parece_ruta(opcionales[0]):
        freq_bl = _entero(opcionales.pop(0), "frecuencia_bl", minimo=1)
    if opcionales:
        salida = opcionales[0]

    return Parametros(semilla, entrada, tam_pobla, prob_c, prob_m, iteraciones,
                      freq_bl, salida)


def ruta_traza(salida):
    """Ruta donde dejar la traza de convergencia, derivada del CSV de resultados."""
    base, extension = os.path.splitext(salida)
    return f"{base}_traza{extension or '.csv'}"
