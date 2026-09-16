#!/usr/bin/env python3
"""
Script para procesar el CSV de resultados y generar la tabla resumen
formateada para el artículo científico IEEE y Markdown.
"""

import csv
from collections import defaultdict
import statistics

ARCHIVO_CSV = "results/comparativa_ag_vs_memetico.csv"

def analizar():
    try:
        with open(ARCHIVO_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            datos = list(reader)
    except FileNotFoundError:
        print(f"No se encontró el archivo: {ARCHIVO_CSV}. Ejecuta primero ejecutar_comparativa.py")
        return

    # Estructura: {(Instancia, Algoritmo): list of dicts}
    grupos = defaultdict(list)
    for fila in datos:
        clave = (fila["Tamano_Problema"], fila["Algoritmo"])
        grupos[clave].append(fila)

    print("\n" + "=" * 85)
    print(" TABLA RESUMEN PARA EL INFORME IEEE (MEDIA Y MEJOR VALOR)")
    print("=" * 85)
    print(f"{'Instancia':<18} | {'Algoritmo':<10} | {'UB':<6} | {'Mejor Mk':<8} | {'RPD Min %':<10} | {'RPD Prom %':<10} | {'Tiempo (s)':<10}")
    print("-" * 85)

    instancias = ["Pequeña (20x5)", "Mediana (50x10)", "Grande (100x10)"]
    algoritmos = ["AG_Puro", "Memetico"]

    for inst in instancias:
        for algo in algoritmos:
            corridas = grupos.get((inst, algo), [])
            if not corridas:
                continue

            ub = corridas[0]["Upper_Bound"]
            makespans = [int(c["Makespan"]) for c in corridas]
            rpds = [float(c["RPD_%"].replace(",", ".")) for c in corridas]
            tiempos = [float(c["Tiempo_Seg"].replace(",", ".")) for c in corridas]

            mejor_mk = min(makespans)
            rpd_min = min(rpds)
            rpd_prom = statistics.mean(rpds)
            tiempo_prom = statistics.mean(tiempos)

            print(f"{inst:<18} | {algo:<10} | {ub:<6} | {mejor_mk:<8} | {rpd_min:<10.2f} | {rpd_prom:<10.2f} | {tiempo_prom:<10.2f}")
        print("-" * 85)

if __name__ == "__main__":
    analizar()
