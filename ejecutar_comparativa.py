#!/usr/bin/env python3
"""Batería experimental comparando el Algoritmo Genético con el Memético.

Corre los dos algoritmos sobre tres tamaños de instancia y varias semillas, y
deja dos archivos: uno con el resultado de cada corrida y otro con la traza de
convergencia (en qué generación se halló cada mejora), que es lo que consume
`generar_graficos.py`.

Uso: python ejecutar_comparativa.py
"""

import csv
import os
import random
import time

from pfsp.ga import ejecutar_evolutivo
from pfsp.instance import leer_instancia_taillard

INSTANCIAS = [
    ("Mediana (50x10)",  "data/ins_50_10_00.txt"),
]

ALGORITMOS = [("AG", False), ("Memetico", True)]

TAM_POBLA = 60
PROB_CRUCE = 0.85
PROB_MUTA = 0.20
ITERACIONES = 300
SEMILLAS = list(range(1, 31))

ARCHIVO_RESULTADOS = "results/comparativa_ag_vs_memetico.csv"
ARCHIVO_TRAZA = "results/traza_convergencia.csv"


def ejecutar():
    os.makedirs("results", exist_ok=True)
    total = len(ALGORITMOS) * len(INSTANCIAS) * len(SEMILLAS)

    print("=" * 78)
    print(" BATERÍA EXPERIMENTAL: ALGORITMO GENÉTICO vs ALGORITMO MEMÉTICO")
    print(f" Instancias:     {[nombre for nombre, _ in INSTANCIAS]}")
    print(f" Población:      {TAM_POBLA} | Iteraciones: {ITERACIONES}")
    print(f" Cruce:          {PROB_CRUCE} | Mutación: {PROB_MUTA}")
    print(f" Semillas:       {SEMILLAS}")
    print(f" Total corridas: {total}")
    print("=" * 78)

    filas_resultado = []
    filas_traza = []
    contador = 0
    inicio_global = time.perf_counter()

    for algoritmo, usar_bl in ALGORITMOS:
        print(f"\n==================== {algoritmo} ====================")
        for tamano, archivo in INSTANCIAS:
            matriz, num_maq, num_job, cota_superior, _ = leer_instancia_taillard(archivo)
            print(f"\n--- {tamano} ({archivo}) | UB conocido: {cota_superior} ---")

            for semilla in SEMILLAS:
                contador += 1
                random.seed(semilla)

                inicio = time.perf_counter()
                mejor_sol, makespan, traza = ejecutar_evolutivo(
                    TAM_POBLA, PROB_CRUCE, PROB_MUTA, ITERACIONES, matriz,
                    num_maq, num_job, usar_bl=usar_bl, mostrar_progreso=False)
                tiempo = time.perf_counter() - inicio

                rpd = (makespan - cota_superior) / cota_superior * 100
                filas_resultado.append([
                    algoritmo, tamano, archivo, semilla, TAM_POBLA, PROB_CRUCE,
                    PROB_MUTA, ITERACIONES, makespan, cota_superior, f"{rpd:.2f}",
                    f"{tiempo:.4f}", traza[-1][0],
                    "-".join(str(trabajo) for trabajo in mejor_sol),
                ])
                filas_traza.extend(
                    [algoritmo, tamano, semilla, generacion, mk] for generacion, mk in traza)

                print(f"[{contador:02d}/{total}] semilla {semilla:2d} -> Makespan {makespan} "
                      f"(RPD {rpd:5.2f}%) | hallado en gen {traza[-1][0]:3d} | {tiempo:6.2f}s")

    with open(ARCHIVO_RESULTADOS, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\n")
        writer.writerow([
            "Algoritmo", "Tamano_Problema", "Instancia", "Semilla", "Poblacion",
            "Prob_Cruce", "Prob_Mutacion", "Iteraciones", "Makespan", "Upper_Bound",
            "RPD_%", "Tiempo_Seg", "Generacion_Hallazgo", "Mejor_Secuencia",
        ])
        writer.writerows(filas_resultado)

    with open(ARCHIVO_TRAZA, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\n")
        writer.writerow(["Algoritmo", "Tamano_Problema", "Semilla", "Generacion", "Makespan"])
        writer.writerows(filas_traza)

    print("\n" + "=" * 78)
    print(" EXPERIMENTACIÓN FINALIZADA")
    print(f" Tiempo total:  {time.perf_counter() - inicio_global:.2f} segundos")
    print(f" Resultados en: {ARCHIVO_RESULTADOS}")
    print(f" Trazas en:     {ARCHIVO_TRAZA}")
    print("=" * 78)


if __name__ == "__main__":
    ejecutar()
