#!/usr/bin/env python3
"""Barrido de parámetros para justificar los valores usados en la batería.

Varía un parámetro a la vez alrededor de la configuración base y deja fijos los
demás, que es lo que permite atribuirle el cambio de desempeño al parámetro
variado. Cada barrido incluye el valor base, así que las filas de una misma
tabla son comparables entre sí.

No reemplaza a `ejecutar_comparativa.py`: aquel compara los dos algoritmos con
los parámetros ya elegidos, este sirve para elegirlos.

Uso: python barrido_parametros.py
"""

import csv
import os
import random
import statistics
import time

from pfsp.ga import ejecutar_evolutivo
from pfsp.instance import leer_instancia_taillard

# Instancia mediana: en la pequeña ambos métodos llegan al óptimo conocido y no
# se distingue nada, y en la grande cada corrida cuesta demasiado para un barrido.
INSTANCIA = "data/ins_50_10_00.txt"
ITERACIONES = 300
SEMILLAS = [1, 2, 3, 4, 5]

BASE = {"tam_pobla": 60, "prob_c": 0.85, "prob_m": 0.20, "k_torneo": 3}

BARRIDOS = {
    "tam_pobla": [20, 40, 60, 100],
    "prob_c": [0.60, 0.75, 0.85, 0.95],
    "prob_m": [0.05, 0.10, 0.20, 0.40],
    "k_torneo": [2, 3, 4, 6],
}

ALGORITMOS = [("AG", False), ("Memetico", True)]

ARCHIVO_SALIDA = "results/barrido_parametros.csv"


def corridas(config, usar_bl, matriz, num_maq, num_job, cache):
    """Resultados de todas las semillas para una configuración.

    La configuración base se repite en los cuatro barridos, así que se memoriza
    para no recalcularla cada vez.
    """
    clave = (usar_bl, tuple(sorted(config.items())))
    if clave in cache:
        return cache[clave]

    resultados = []
    for semilla in SEMILLAS:
        random.seed(semilla)
        inicio = time.perf_counter()
        _, makespan, _ = ejecutar_evolutivo(
            config["tam_pobla"], config["prob_c"], config["prob_m"], ITERACIONES,
            matriz, num_maq, num_job, usar_bl=usar_bl,
            k_torneo=config["k_torneo"], mostrar_progreso=False)
        resultados.append((semilla, makespan, time.perf_counter() - inicio))

    cache[clave] = resultados
    return resultados


def main():
    os.makedirs("results", exist_ok=True)
    matriz, num_maq, num_job, cota_superior, _ = leer_instancia_taillard(INSTANCIA)

    print("=" * 74)
    print(" BARRIDO DE PARÁMETROS (un factor a la vez)")
    print(f" Instancia:  {INSTANCIA} | UB conocido: {cota_superior}")
    print(f" Base:       {BASE}")
    print(f" Semillas:   {SEMILLAS} | Iteraciones: {ITERACIONES}")
    print("=" * 74)

    filas = []
    cache = {}
    inicio_global = time.perf_counter()

    for algoritmo, usar_bl in ALGORITMOS:
        for parametro, valores in BARRIDOS.items():
            print(f"\n--- {algoritmo} | {parametro} (base: {BASE[parametro]}) ---")
            print(f"{'valor':>8} | {'RPD prom':>17} | {'RPD min':>8} | {'tiempo':>8}")
            print("-" * 54)

            for valor in valores:
                config = dict(BASE, **{parametro: valor})
                resultados = corridas(config, usar_bl, matriz, num_maq, num_job, cache)

                rpds = [(mk - cota_superior) / cota_superior * 100
                        for _, mk, _ in resultados]
                tiempos = [t for _, _, t in resultados]
                desviacion = statistics.stdev(rpds) if len(rpds) > 1 else 0.0
                marca = "  <- base" if valor == BASE[parametro] else ""

                print(f"{valor:>8} | {statistics.mean(rpds):>9.2f}% ± {desviacion:<5.2f} | "
                      f"{min(rpds):>7.2f}% | {statistics.mean(tiempos):>7.2f}s{marca}")

                filas.extend(
                    [algoritmo, parametro, valor, semilla, makespan, cota_superior,
                     f"{(makespan - cota_superior) / cota_superior * 100:.2f}", f"{t:.4f}"]
                    for semilla, makespan, t in resultados)

    with open(ARCHIVO_SALIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\n")
        writer.writerow(["Algoritmo", "Parametro", "Valor", "Semilla", "Makespan",
                         "Upper_Bound", "RPD_%", "Tiempo_Seg"])
        writer.writerows(filas)

    print("\n" + "=" * 74)
    print(f" BARRIDO FINALIZADO en {time.perf_counter() - inicio_global:.2f} segundos")
    print(f" Resultados en: {ARCHIVO_SALIDA}")
    print("=" * 74)


if __name__ == "__main__":
    main()
