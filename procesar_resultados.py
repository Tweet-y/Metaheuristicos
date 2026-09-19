#!/usr/bin/env python3
"""Tabla resumen a partir del CSV de la batería experimental.

Uso: python procesar_resultados.py
"""

import csv
import statistics
from collections import defaultdict

ARCHIVO_CSV = "results/comparativa_ag_vs_memetico.csv"

TAMANOS = ["Mediana (50x10)"]
ALGORITMOS = ["AG", "Memetico"]


def analizar():
    try:
        with open(ARCHIVO_CSV, encoding="utf-8") as f:
            datos = list(csv.DictReader(f, delimiter=";"))
    except FileNotFoundError:
        print(f"No se encontró {ARCHIVO_CSV}. Ejecuta primero: python ejecutar_comparativa.py")
        return

    grupos = defaultdict(list)
    for fila in datos:
        grupos[(fila["Tamano_Problema"], fila["Algoritmo"])].append(fila)

    ancho = 100
    print("\n" + "=" * ancho)
    print(" TABLA RESUMEN: ALGORITMO GENÉTICO Y ALGORITMO MEMÉTICO")
    print(f" RPD(%) = (Makespan - UB) / UB * 100, sobre {len(grupos[(TAMANOS[0], ALGORITMOS[0])])} "
          f"semillas por combinación")
    print("=" * ancho)
    print(f"{'Instancia':<17} | {'Algoritmo':<9} | {'UB':>5} | {'Mejor':>5} | {'RPD min':>8} | "
          f"{'RPD prom':>17} | {'Gen. hallazgo':>13} | {'Tiempo':>8}")
    print("-" * ancho)

    for tamano in TAMANOS:
        for algoritmo in ALGORITMOS:
            corridas = grupos.get((tamano, algoritmo), [])
            if not corridas:
                continue

            cota = corridas[0]["Upper_Bound"]
            makespans = [int(c["Makespan"]) for c in corridas]
            rpds = [float(c["RPD_%"]) for c in corridas]
            tiempos = [float(c["Tiempo_Seg"]) for c in corridas]
            hallazgos = [int(c["Generacion_Hallazgo"]) for c in corridas]

            desviacion = statistics.stdev(rpds) if len(rpds) > 1 else 0.0
            print(f"{tamano:<17} | {algoritmo:<9} | {cota:>5} | {min(makespans):>5} | "
                  f"{min(rpds):>7.2f}% | {statistics.mean(rpds):>9.2f}% ± {desviacion:<5.2f} | "
                  f"{statistics.mean(hallazgos):>13.1f} | {statistics.mean(tiempos):>7.2f}s")
        print("-" * ancho)


if __name__ == "__main__":
    analizar()
