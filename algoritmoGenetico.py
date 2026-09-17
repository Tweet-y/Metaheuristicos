#!/usr/bin/env python3
"""Algoritmo Genético para el Permutation Flow Shop Scheduling Problem (PFSP).

Uso:
    python algoritmoGenetico.py semilla archivo_instancia tam_poblacion \
prob_cruza prob_mutacion iteraciones [salida.csv]

Ejemplo:
    python algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300

Los operadores viven en el paquete `pfsp/`, escritos de forma genérica para
poder reutilizarlos en otros problemas de permutación:

    Población       pfsp/operators.py     inicializar_poblacion
    Fitness         pfsp/makespan.py      calcular_makespan, evaluar_poblacion
    Selección       pfsp/operators.py     seleccion_torneo
    Cruza           pfsp/operators.py     cruce_ox
    Mutación        pfsp/operators.py     mutacion_swap, mutacion_insercion, mutar_individuo
    Reemplazo       pfsp/operators.py     reemplazo_mu_lambda
    Aleatoriedad    pfsp/rng.py           aleatorio_real, aleatorio_entero
    Ciclo evolutivo pfsp/ga.py            ejecutar_evolutivo
"""

import random
import sys
import time

from pfsp.cli import parsear_argumentos, ruta_traza
from pfsp.ga import ejecutar_evolutivo
from pfsp.instance import leer_instancia_taillard

# Se reexportan aquí para que el programa ofrezca en un solo punto de entrada
# todas las funciones del algoritmo, y para poder probarlas desde los tests.
from pfsp.makespan import calcular_makespan, evaluar_poblacion  # noqa: F401
from pfsp.operators import (  # noqa: F401
    cruce_ox,
    inicializar_poblacion,
    mutacion_insercion,
    mutacion_swap,
    mutar_individuo,
    reemplazo_mu_lambda,
    seleccion_torneo,
)
from pfsp.rng import aleatorio_entero, aleatorio_real  # noqa: F401
from pfsp.salida import guardar_resultado_csv, guardar_traza_csv, imprimir_resultados

ALGORITMO = "AG"


def ejecutar_algoritmo_genetico(tam_pobla, prob_c, prob_m, iteraciones, matriz,
                                num_maq, num_job):
    """Algoritmo Genético puro: el ciclo evolutivo sin etapa de búsqueda local."""
    return ejecutar_evolutivo(tam_pobla, prob_c, prob_m, iteraciones, matriz,
                              num_maq, num_job, usar_bl=False)


def main():
    p = parsear_argumentos(sys.argv, "algoritmoGenetico.py")
    random.seed(p.semilla)

    matriz, num_maq, num_job, cota_superior, cota_inferior = leer_instancia_taillard(p.entrada)

    print(f"Parámetros cargados (AG): semilla={p.semilla}, archivo={p.entrada}, "
          f"Pob={p.tam_pobla}, Pc={p.prob_c}, Pm={p.prob_m}, Iter={p.iteraciones}")
    print(f"Instancia: {num_job} trabajos, {num_maq} máquinas | "
          f"Upper Bound: {cota_superior}, Lower Bound: {cota_inferior}\n")

    inicio = time.perf_counter()
    mejor_sol, mejor_mk, traza = ejecutar_algoritmo_genetico(
        p.tam_pobla, p.prob_c, p.prob_m, p.iteraciones, matriz, num_maq, num_job)
    tiempo_total = time.perf_counter() - inicio

    rpd = (mejor_mk - cota_superior) / cota_superior * 100
    imprimir_resultados(ALGORITMO, p.semilla, p.entrada, mejor_sol, mejor_mk,
                        cota_superior, rpd, tiempo_total, traza[-1][0])

    if p.salida:
        guardar_resultado_csv(p.salida, ALGORITMO, p.entrada, p.semilla, p.tam_pobla,
                              p.prob_c, p.prob_m, p.iteraciones, mejor_mk,
                              cota_superior, rpd, tiempo_total, mejor_sol)
        guardar_traza_csv(ruta_traza(p.salida), ALGORITMO, p.entrada, p.semilla, traza)


if __name__ == "__main__":
    main()
