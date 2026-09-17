"""Lectura y validación de instancias de Taillard."""

import os
import sys


def leer_instancia_taillard(ruta_archivo):
    """Lee una instancia de Taillard desde disco.

    Formato del archivo: una primera línea con
    `num_trabajos num_maquinas semilla cota_superior cota_inferior`, seguida de
    `num_maquinas` filas de `num_trabajos` enteros. Ojo con el orden: las filas
    son máquinas y las columnas son trabajos, de modo que el tiempo de proceso
    del trabajo j en la máquina m se lee como `matriz[m][j]`.

    Devuelve (matriz, num_maq, num_job, cota_superior, cota_inferior).
    """
    if not os.path.isfile(ruta_archivo):
        print(f"Error: El archivo de instancia '{ruta_archivo}' no existe.")
        sys.exit(1)

    try:
        with open(ruta_archivo, "r") as f:
            cabecera = f.readline().split()
            num_job = int(cabecera[0])
            num_maq = int(cabecera[1])
            cota_superior = int(cabecera[3])
            cota_inferior = int(cabecera[4])
            matriz = [[int(v) for v in linea.split()] for linea in f if linea.strip()]
    except (ValueError, IndexError):
        print(f"Error: '{ruta_archivo}' no tiene el formato de una instancia de Taillard.")
        sys.exit(1)

    if len(matriz) != num_maq or any(len(fila) != num_job for fila in matriz):
        print(f"Error: '{ruta_archivo}' declara {num_maq} máquinas x {num_job} trabajos, "
              f"pero la matriz leída no calza con esas dimensiones.")
        sys.exit(1)

    return matriz, num_maq, num_job, cota_superior, cota_inferior
