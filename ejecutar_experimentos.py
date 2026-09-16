#!/usr/bin/env python3
"""
Script de Experimentación Automática para PFSP (Algoritmo Genético)
Permite probar una lista de iteraciones (y múltiples semillas por cada una)
acumulando todos los resultados en un único archivo CSV para el informe.
"""

import subprocess
import sys
import os
import numpy as np

# Configuración del experimento
PYTHON_EXEC = sys.executable  # Usa el mismo python del entorno activo (.venv si existe)
SCRIPT_AG = "algoritmoMemetico.py"

# Archivo de datos a probar (el primero del conjunto de datos)
INSTANCIA = "data/ins_20_5_00.txt"

# Parámetros genéticos
TAM_POBLA = 100
PROB_CRUCE = 0.85
PROB_MUTA = 0.20

# Lista de iteraciones que quieres evaluar para el informe
# Puedes modificar o agregar los valores que necesites
LISTA_ITERACIONES = [100, 250, 500, 1000, 1500, 2000, 3000]

# Semillas para tener significancia estadística (e.g. 5 corridas por cada número de iteraciones)
SEMILLAS = [1, 7, 42, 123, 999]

# Archivo CSV de salida donde se concentrarán todas las ejecuciones
ARCHIVO_SALIDA = "results/experimento_iteraciones.csv"


def main():
    # Asegurar que exista el directorio de resultados
    os.makedirs(os.path.dirname(ARCHIVO_SALIDA) if os.path.dirname(ARCHIVO_SALIDA) else ".", exist_ok=True)

    print("=" * 70)
    print(" INICIANDO BATERÍA DE EXPERIMENTOS PARA EL INFORME")
    print(f" Instancia:          {INSTANCIA}")
    print(f" Población:          {TAM_POBLA}")
    print(f" Cruce / Mutación:   {PROB_CRUCE} / {PROB_MUTA}")
    print(f" Iteraciones:        {LISTA_ITERACIONES}")
    print(f" Semillas ({len(SEMILLAS)}):      {SEMILLAS}")
    print(f" Archivo destino:    {ARCHIVO_SALIDA}")
    print("=" * 70)

    total_corridas = len(LISTA_ITERACIONES) * len(SEMILLAS)
    contador = 0

    for iteracion in LISTA_ITERACIONES:
        print(f"\n>>> Probando {iteracion} iteraciones...")
        for semilla in SEMILLAS:
            contador += 1
            print(f"  [{contador}/{total_corridas}] Ejecutando: Iteraciones={iteracion}, Semilla={semilla} ...", end=" ", flush=True)

            cmd = [
                PYTHON_EXEC,
                SCRIPT_AG,
                INSTANCIA,
                str(TAM_POBLA),
                str(PROB_CRUCE),
                str(PROB_MUTA),
                str(iteracion),
                str(semilla),
                ARCHIVO_SALIDA
            ]

            res = subprocess.run(cmd, capture_output=True, text=True)

            if res.returncode == 0:
                print("✓ Completado")
            else:
                print("✗ Error")
                print(res.stderr)

    print("\n" + "=" * 70)
    print(f" EXPERIMENTOS FINALIZADOS CON ÉXITO")
    print(f" Todos los datos se han guardado en: {ARCHIVO_SALIDA}")
    print("=" * 70)


if __name__ == "__main__":
    main()
