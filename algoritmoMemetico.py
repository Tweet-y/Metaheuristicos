#!/usr/bin/env python3
"""Algoritmo Memético para el Permutation Flow Shop Scheduling Problem (PFSP).

Es el Algoritmo Genético más una etapa de explotación: cada `frecuencia_bl`
generaciones se aplica búsqueda local por inserción sobre el mejor individuo.

Uso:
    python algoritmoMemetico.py semilla archivo_instancia tam_poblacion \
prob_cruza prob_mutacion iteraciones [frecuencia_bl] [salida.csv]

Ejemplo:
    python algoritmoMemetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300 1

Los operadores viven en el paquete `pfsp/`, escritos de forma genérica para
poder reutilizarlos en otros problemas de permutación:

    Población       pfsp/operators.py     inicializar_poblacion
    Fitness         pfsp/makespan.py      calcular_makespan, evaluar_poblacion
    Selección       pfsp/operators.py     seleccion_torneo
    Cruza           pfsp/operators.py     cruce_ox
    Mutación        pfsp/operators.py     mutacion_swap, mutacion_insercion, mutar_individuo
    Reemplazo       pfsp/operators.py     reemplazo_mu_lambda
    Búsqueda local  pfsp/local_search.py  busqueda_local_insercion
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
from pfsp.local_search import busqueda_local_insercion, costos_insercion  # noqa: F401
from pfsp.makespan import calcular_makespan, evaluar_poblacion  # noqa: F401
from pfsp.neh import neh  # noqa: F401
from pfsp.operators import (  # noqa: F401
    cruce_ox,
    inicializar_poblacion,
    mutacion_insercion,
    mutacion_swap,
    mutar_individuo,
    reemplazo_mu_lambda,
    renovar_poblacion,
    seleccion_torneo,
)
from pfsp.rng import aleatorio_entero, aleatorio_real  # noqa: F401
from pfsp.salida import guardar_resultado_csv, guardar_traza_csv, imprimir_resultados

ALGORITMO = "Memetico"


def ejecutar_algoritmo_memetico(tam_pobla, prob_c, prob_m, iteraciones, matriz,
                                num_maq, num_job, cota_superior=None, freq_bl=1,
                                paciencia_renovacion=None, frac_renovacion=0.20,
                                reparar_renovados=True):
    """Algoritmo Memético: el ciclo evolutivo con búsqueda local por inserción."""
    return ejecutar_evolutivo(tam_pobla, prob_c, prob_m, iteraciones, matriz,
                              num_maq, num_job, usar_bl=True, freq_bl=freq_bl,
                              cota_superior=cota_superior,
                              paciencia_renovacion=paciencia_renovacion,
                              frac_renovacion=frac_renovacion,
                              reparar_renovados=reparar_renovados)


def main():
    p = parsear_argumentos(sys.argv, "algoritmoMemetico.py", con_busqueda_local=True)
    random.seed(p.semilla)

    matriz, num_maq, num_job, cota_superior, cota_inferior = leer_instancia_taillard(p.entrada)

    print(f"Parámetros cargados (Memético): semilla={p.semilla}, archivo={p.entrada}, "
          f"Pob={p.tam_pobla}, Pc={p.prob_c}, Pm={p.prob_m}, Iter={p.iteraciones}, "
          f"FreqBL={p.freq_bl}")
    print(f"Instancia: {num_job} trabajos, {num_maq} máquinas | "
          f"Upper Bound: {cota_superior}, Lower Bound: {cota_inferior}\n")

    inicio = time.perf_counter()
    mejor_sol, mejor_mk, traza = ejecutar_algoritmo_memetico(
        p.tam_pobla, p.prob_c, p.prob_m, p.iteraciones, matriz, num_maq, num_job,
        cota_superior, p.freq_bl)
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
