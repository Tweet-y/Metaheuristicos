#!/usr/bin/env python3
"""Tabla resumen a partir de los CSV de la batería experimental.

Uso: python procesar_resultados.py
"""

import csv
import glob
import statistics
from collections import defaultdict

ALGORITMOS = ["AG", "Memetico"]


def analizar():
    archivos = sorted(glob.glob("results/comparativa_*.csv"))
    if not archivos:
        print("No se encontraron archivos results/comparativa_*.csv. Ejecuta primero: python ejecutar_comparativa.py")
        return

    ancho = 110
    print("\n" + "=" * ancho)
    print(" TABLA RESUMEN: ALGORITMO GENÉTICO Y ALGORITMO MEMÉTICO")
    print(" RPD(%) = (Makespan - UB) / UB * 100 (* indica UB alcanzado)")
    print("=" * ancho)
    print(f"{'Instancia':<17} | {'Algoritmo':<9} | {'UB':>5} | {'Mejor':>5} | {'Semilla':>7} | {'RPD min':>8} | "
          f"{'RPD prom':>17} | {'Gen. hallazgo':>13} | {'Tiempo':>8}")
    print("-" * ancho)

    for ruta in archivos:
        try:
            with open(ruta, encoding="utf-8") as f:
                datos = list(csv.DictReader(f, delimiter=";"))
        except Exception as e:
            print(f"Error al leer {ruta}: {e}")
            continue

        if not datos:
            continue

        grupos = defaultdict(list)
        for fila in datos:
            grupos[fila["Algoritmo"]].append(fila)

        tamano = datos[0]["Tamano_Problema"]

        for algoritmo in ALGORITMOS:
            corridas = grupos.get(algoritmo, [])
            if not corridas:
                continue

            cota = corridas[0]["Upper_Bound"]
            mejor_corrida = min(corridas, key=lambda c: int(c["Makespan"]))
            mejor_makespan = int(mejor_corrida["Makespan"])
            mejor_semilla = mejor_corrida["Semilla"]

            rpds = [float(c["RPD_%"]) for c in corridas]
            tiempos = [float(c["Tiempo_Seg"]) for c in corridas]
            hallazgos = [int(c["Generacion_Hallazgo"]) for c in corridas]

            min_rpd = min(rpds)
            # Los UB de Taillard son cotas superiores, no óptimos: una corrida puede
            # bajar del UB y dar RPD negativo, que también cuenta como alcanzado.
            marca = "*" if min_rpd <= 0.0 else " "
            rpd_min_str = f"{min_rpd:>6.2f}%{marca}"

            desviacion = statistics.stdev(rpds) if len(rpds) > 1 else 0.0
            print(f"{tamano:<17} | {algoritmo:<9} | {cota:>5} | {mejor_makespan:>5} | {mejor_semilla:>7} | "
                  f"{rpd_min_str:>8} | {statistics.mean(rpds):>9.2f}% ± {desviacion:<5.2f} | "
                  f"{statistics.mean(hallazgos):>13.1f} | {statistics.mean(tiempos):>7.2f}s")
        print("-" * ancho)


if __name__ == "__main__":
    analizar()
