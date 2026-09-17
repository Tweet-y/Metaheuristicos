#!/usr/bin/env python3
"""
Script de Comparativa Experimental para PFSP: AG Puro vs Algoritmo Memético.
Diseñado para generar la matriz completa de resultados para el informe IEEE.
Evalúa 3 tamaños de problemas (Pequeño, Mediano, Grande) con múltiples semillas.
"""

import subprocess
import sys
import os
import csv
import time

PYTHON_EXEC = sys.executable

# 1. Definición de Instancias (3 tamaños para analizar escalabilidad)
INSTANCIAS = [
    {"nombre": "Pequeña (20x5)",   "archivo": "data/ins_20_5_00.txt"},
    {"nombre": "Mediana (50x10)",  "archivo": "data/ins_50_10_00.txt"},
    {"nombre": "Grande (100x10)",  "archivo": "data/ins_100_10_00.txt"},
]

# 2. Parámetros de los algoritmos
TAM_POBLA = 60
PROB_CRUCE = 0.85
PROB_MUTA = 0.20
ITERACIONES = 300

# 3. Semillas para significancia estadística (5 corridas por combinación)
SEMILLAS = [1, 7, 21, 42, 53]

# 4. Archivos de salida
ARCHIVO_SALIDA = "results/comparativa_ag_vs_memetico.csv"


def ejecutar():
    os.makedirs("results", exist_ok=True)

    # Si el archivo ya existía, lo reiniciamos con su encabezado
    with open(ARCHIVO_SALIDA, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "Algoritmo", "Tamano_Problema", "Instancia", "Semilla", "Poblacion",
            "Prob_Cruce", "Prob_Mutacion", "Iteraciones", "Makespan",
            "Upper_Bound", "RPD_%", "Tiempo_Seg", "Mejor_Secuencia"
        ])

    algoritmos = [
        ("AG_Puro", "algoritmoGenetico.py"),
        ("Memetico", "algoritmoMemetico.py")
    ]

    total_pruebas = len(algoritmos) * len(INSTANCIAS) * len(SEMILLAS)
    contador = 0
    t_global_inicio = time.time()

    print("=" * 80)
    print(" INICIANDO BATERÍA DE EXPERIMENTOS: AG PURO vs ALGORITMO MEMÉTICO")
    print(f" Instancias:    {[ins['nombre'] for ins in INSTANCIAS]}")
    print(f" Población:     {TAM_POBLA} | Iteraciones: {ITERACIONES}")
    print(f" Cruce:         {PROB_CRUCE} | Mutación: {PROB_MUTA}")
    print(f" Semillas:      {SEMILLAS}")
    print(f" Total corridas:{total_pruebas}")
    print(f" Archivo CSV:   {ARCHIVO_SALIDA}")
    print("=" * 80)

    # Archivo temporal para cada corrida individual
    temp_csv = "/tmp/temp_run.csv"

    for algo_nombre, script_py in algoritmos:
        print(f"\n==================== EVALUANDO: {algo_nombre} ====================")

        for inst in INSTANCIAS:
            print(f"\n--- Instancia: {inst['nombre']} ({inst['archivo']}) ---")

            for semilla in SEMILLAS:
                contador += 1
                if os.path.exists(temp_csv):
                    os.remove(temp_csv)

                print(f"[{contador:02d}/{total_pruebas}] {algo_nombre} | Semilla {semilla:2d} ...", end=" ", flush=True)

                cmd = [
                    PYTHON_EXEC,
                    script_py,
                    str(semilla),
                    inst["archivo"],
                    str(TAM_POBLA),
                    str(PROB_CRUCE),
                    str(PROB_MUTA),
                    str(ITERACIONES),
                    temp_csv
                ]

                t0 = time.time()
                res = subprocess.run(cmd, capture_output=True, text=True)
                t1 = time.time()

                if res.returncode == 0 and os.path.exists(temp_csv):
                    # Leer el resultado individual registrado
                    with open(temp_csv, mode="r", encoding="utf-8") as f_temp:
                        reader = list(csv.reader(f_temp, delimiter=";"))
                        if len(reader) >= 2:
                            fila = reader[1]
                            # Estructura del script:
                            # AG:      [Instancia, Semilla, Pob, Pc, Pm, Iter, Mk, UB, RPD, Tiempo, Seq]
                            # Memetico:[Algo, Instancia, Semilla, Pob, Pc, Pm, Iter, Mk, UB, RPD, Tiempo, Seq]
                            if algo_nombre == "Memetico":
                                mk, ub, rpd, seg, seq = fila[7], fila[8], fila[9], fila[10], fila[11]
                            else:
                                mk, ub, rpd, seg, seq = fila[6], fila[7], fila[8], fila[9], fila[10]

                            # Escribir en el CSV maestro consolidado
                            with open(ARCHIVO_SALIDA, mode="a", newline="", encoding="utf-8") as f_master:
                                writer_m = csv.writer(f_master, delimiter=";")
                                writer_m.writerow([
                                    algo_nombre, inst["nombre"], inst["archivo"], semilla,
                                    TAM_POBLA, PROB_CRUCE, PROB_MUTA, ITERACIONES,
                                    mk, ub, rpd, seg, seq
                                ])

                            print(f"✓ Makespan: {mk} (RPD: {rpd}%) | {float(seg):.2f}s")
                        else:
                            print(f"✗ Salida inesperada en CSV")
                else:
                    print(f"✗ Falló la ejecución")
                    print(res.stderr)

    t_global_total = time.time() - t_global_inicio
    print("\n" + "=" * 80)
    print(" EXPERIMENTACIÓN FINALIZADA CON ÉXITO")
    print(f" Tiempo total de experimentación: {t_global_total:.2f} segundos")
    print(f" Matriz completa guardada en:     {ARCHIVO_SALIDA}")
    print("=" * 80)


if __name__ == "__main__":
    ejecutar()
