#!/usr/bin/env python3
"""Batería experimental comparando el Algoritmo Genético con el Memético.

Corre los dos algoritmos sobre cada instancia de `INSTANCIAS` y varias semillas.
Por cada instancia deja un archivo con el resultado de cada corrida (incluyendo
la generación en que se halló la mejor solución), que es lo que consumen
`procesar_resultados.py` y `generar_graficos.py`.

Uso: python -m experimentos.ejecutar_comparativa
"""

import csv
import os
import random
import time

from pfsp.ga import ejecutar_evolutivo
from pfsp.instance import leer_instancia_taillard

# (nombre, archivo, prob_mutacion). Las tres instancias más grandes usan 0.50:
# dio mejores resultados que 0.20 en las pocas corridas que alcanzaron a compararse.
INSTANCIAS = [
    ("20x5",    "data/ins_20_5_00.txt",    0.20),
    ("20x10",   "data/ins_20_10_00.txt",   0.20),
    ("20x20",   "data/ins_20_20_00.txt",   0.20),
    ("50x5",    "data/ins_50_5_00.txt",    0.20),
    ("50x10",   "data/ins_50_10_00.txt",   0.20),
    ("50x20",   "data/ins_50_20_00.txt",   0.20),
    ("100x5",   "data/ins_100_5_00.txt",   0.20),
    ("100x10",  "data/ins_100_10_00.txt",  0.20),
    ("100x20",  "data/ins_100_20_00.txt",  0.20),
    ("200x10",  "data/ins_200_10_00.txt",  0.50),
    ("200x20",  "data/ins_200_20_00.txt",  0.50),
    ("500x20",  "data/ins_500_20_00.txt",  0.50),
]

ALGORITMOS = [("AG", False), ("Memetico", True)]

TAM_POBLA = 60
PROB_CRUCE = 0.85
ITERACIONES = 300
SEMILLAS = list(range(1, 31))


def ejecutar():
    os.makedirs("results", exist_ok=True)
    total = len(ALGORITMOS) * len(INSTANCIAS) * len(SEMILLAS)

    print("=" * 78)
    print(" BATERÍA EXPERIMENTAL: ALGORITMO GENÉTICO vs ALGORITMO MEMÉTICO")
    print(f" Instancias:     {[nombre for nombre, _, _ in INSTANCIAS]}")
    print(f" Población:      {TAM_POBLA} | Iteraciones: {ITERACIONES}")
    print(f" Cruce:          {PROB_CRUCE} | Mutación: por instancia")
    print(f" Semillas:       {SEMILLAS}")
    print(f" Total corridas: {total}")
    print("=" * 78)

    contador = 0
    inicio_global = time.perf_counter()

    for tamano, archivo, prob_muta in INSTANCIAS:
        slug = os.path.splitext(os.path.basename(archivo))[0]
        if slug.startswith("ins_"):
            slug = slug[4:]
        archivo_resultados = f"results/comparativa_{slug}.csv"

        matriz, num_maq, num_job, cota_superior, _ = leer_instancia_taillard(archivo)
        print(f"\n==================== {tamano} ({archivo}) | UB conocido: {cota_superior} | Pm: {prob_muta} ====================")

        filas_resultado = []

        for algoritmo, usar_bl in ALGORITMOS:
            print(f"\n--- {algoritmo} ---")
            for semilla in SEMILLAS:
                contador += 1
                random.seed(semilla)

                inicio = time.perf_counter()
                mejor_sol, makespan, traza = ejecutar_evolutivo(
                    TAM_POBLA, PROB_CRUCE, prob_muta, ITERACIONES, matriz,
                    num_maq, num_job, usar_bl=usar_bl, mostrar_progreso=False)
                tiempo = time.perf_counter() - inicio

                rpd = (makespan - cota_superior) / cota_superior * 100
                filas_resultado.append([
                    algoritmo, tamano, archivo, semilla, TAM_POBLA, PROB_CRUCE,
                    prob_muta, ITERACIONES, makespan, cota_superior, f"{rpd:.2f}",
                    f"{tiempo:.4f}", traza[-1][0],
                    "-".join(str(trabajo) for trabajo in mejor_sol),
                ])

                print(f"[{contador:03d}/{total}] {tamano} {algoritmo} semilla {semilla:2d} -> Makespan {makespan} "
                      f"(RPD {rpd:5.2f}%) | hallado en gen {traza[-1][0]:3d} | {tiempo:6.2f}s")

        with open(archivo_resultados, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";", lineterminator="\n")
            writer.writerow([
                "Algoritmo", "Tamano_Problema", "Instancia", "Semilla", "Poblacion",
                "Prob_Cruce", "Prob_Mutacion", "Iteraciones", "Makespan", "Upper_Bound",
                "RPD_%", "Tiempo_Seg", "Generacion_Hallazgo", "Mejor_Secuencia",
            ])
            writer.writerows(filas_resultado)

        print(f"\n[Guardado] {archivo_resultados}")

    print("\n" + "=" * 78)
    print(" EXPERIMENTACIÓN FINALIZADA")
    print(f" Tiempo total:  {time.perf_counter() - inicio_global:.2f} segundos")
    print("=" * 78)


if __name__ == "__main__":
    ejecutar()
