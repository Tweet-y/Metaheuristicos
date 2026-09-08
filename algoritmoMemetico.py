#!/usr/bin/env python3
"""Algoritmo Memético para PFSP — interfaz de línea de comandos.

AG con búsqueda local por inserción (lamarckiana) aplicada a la descendencia.

Uso:
    python3 algoritmoMemetico.py DatosEntrada TamanoPobla ProbaCruza ProbaMuta \
NumIteraciones Semilla Resultado.csv [FreqBL] [IntensidadBL]
"""

import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from algoritmoGenetico import _entero, _probabilidad, guardar_resultado_csv
from pfsp.instance import load
from pfsp.local_search import insertion_search
from pfsp.makespan import cmax
from pfsp.memetic import run as ejecutar_algoritmo_memetico
from pfsp.metrics import rpd as calcular_rpd
from pfsp.neh import neh
from pfsp.operators import (
    init_population,
    mutar_intercambio,
    ox_crossover,
    reemplazo_generacional,
    torneo_binario,
)
from pfsp.rng import rand_float, rand_int, seeded_rng

# ==============================================================================
# Funciones mínimas del enunciado (§7)
# Viven en la biblioteca reutilizable pfsp/; aquí solo se exponen con el nombre
# del enunciado. La última es la que distingue al memético del AG.
# ==============================================================================
generar_real_aleatorio = rand_float             # pfsp.rng          real en [0, 1]
generar_entero_aleatorio = rand_int             # pfsp.rng          entero en [a, b]
leer_instancia_taillard = load                  # pfsp.instance     parser p_ij + cotas
inicializar_poblacion = init_population         # pfsp.operators    población inicial
calcular_makespan = cmax                        # pfsp.makespan     fitness Cmax
seleccionar_individuo = torneo_binario          # pfsp.operators    selección
cruzar_individuos = ox_crossover                # pfsp.operators    cruce OX
mutar_individuo = mutar_intercambio             # pfsp.operators    mutación swap
reemplazar_poblacion = reemplazo_generacional   # pfsp.operators    reemplazo + elitismo
heuristica_neh = neh                            # pfsp.neh          sembrado inicial
crear_generador = seeded_rng                    # pfsp.rng          RNG reproducible
busqueda_local_insercion = insertion_search     # pfsp.local_search etapa memética


def validar_argumentos():
    """Valida los 7 argumentos obligatorios y los 2 opcionales de búsqueda local."""
    if len(sys.argv) not in (8, 9, 10):
        print("Error en la entrada de los parametros")
        print("Uso: python3 algoritmoMemetico.py DatosEntrada TamanoPobla ProbaCruza "
              "ProbaMuta NumIteraciones Semilla Resultado.csv [FreqBL] [IntensidadBL]")
        print("donde:")
        print(" - DatosEntrada: archivo de la instancia [ejem: taillards/ins_20_5_00.txt]")
        print(" - TamanoPobla: valor entero positivo >= 2 [ejem: 20]")
        print(" - ProbaCruza: valor real en (0, 1] [ejem: 0.8]")
        print(" - ProbaMuta: valor real en (0, 1] [ejem: 0.1]")
        print(" - NumIteraciones: valor entero positivo >= 1 [ejem: 100]")
        print(" - Semilla: valor entero positivo [ejem: 1]")
        print(" - Resultado.csv: archivo de salida [ejem: results/res_am.csv]")
        print(" - FreqBL (opcional): aplicar busqueda local cada X generaciones [def: 1]")
        print(" - IntensidadBL (opcional): trabajos a reinsertar por llamada [def: n]")
        sys.exit(1)

    import os
    entrada = sys.argv[1]
    if not os.path.isfile(entrada):
        print(f"Error: No existe el archivo de entrada '{entrada}'")
        sys.exit(1)

    return (
        entrada,
        _entero(sys.argv[2], "TamanoPobla", minimo=2),
        _probabilidad(sys.argv[3], "ProbaCruza"),
        _probabilidad(sys.argv[4], "ProbaMuta"),
        _entero(sys.argv[5], "NumIteraciones", minimo=1),
        _entero(sys.argv[6], "Semilla", minimo=1),
        sys.argv[7],
        _entero(sys.argv[8], "FreqBL", minimo=1) if len(sys.argv) >= 9 else 1,
        _entero(sys.argv[9], "IntensidadBL", minimo=1) if len(sys.argv) >= 10 else None,
    )


def main():
    (entrada, tam_pobla, prob_c, prob_m, iteracion, semilla, salida,
     freq_bl, intensidad_bl) = validar_argumentos()

    print(f"Parámetros cargados: {entrada}, {tam_pobla}, {prob_c}, {prob_m}, "
          f"{iteracion}, {semilla}, FreqBL={freq_bl}, IntensidadBL={intensidad_bl}")

    try:
        instancia = leer_instancia_taillard(entrada)
    except ValueError as exc:
        print(f"Error: instancia mal formada. {exc}")
        sys.exit(1)

    print(f"Trabajos: {instancia.n}, Máquinas: {instancia.m}, "
          f"UB: {instancia.ub}, LB: {instancia.lb}")

    inicio = time.time()
    resultado = ejecutar_algoritmo_memetico(
        p=instancia.p,
        seed=semilla,
        pop_size=tam_pobla,
        pc=prob_c,
        pm=prob_m,
        iteraciones=iteracion,
        ls_freq=freq_bl,
        ls_intensity=intensidad_bl,
        use_neh=True,
    )
    tiempo_total = time.time() - inicio

    gap = calcular_rpd(resultado.cmax, instancia.ub)
    gap_txt = "NA" if gap is None else f"{gap:.2f}"

    print("\n" + "=" * 50)
    print("RESULTADOS FINALES ALGORITMO MEMÉTICO:")
    print(f"Mejor secuencia encontrada: {resultado.permutacion}")
    print(f"Makespan obtenido:          {resultado.cmax}")
    print(f"Upper Bound conocido:       {instancia.ub}")
    print(f"RPD (% de error):           {gap_txt}%")
    print(f"Evaluaciones de Cmax:       {resultado.evaluaciones}")
    print(f"Tiempo de ejecución:        {tiempo_total:.4f} segundos")
    print("=" * 50)

    guardar_resultado_csv(salida, {
        "Instancia": entrada,
        "Semilla": semilla,
        "Poblacion": tam_pobla,
        "Prob_Cruce": prob_c,
        "Prob_Mutacion": prob_m,
        "Iteraciones": iteracion,
        "Freq_BL": freq_bl,
        "Intensidad_BL": "n" if intensidad_bl is None else intensidad_bl,
        "Makespan": resultado.cmax,
        "Upper_Bound": instancia.ub,
        "RPD_%": gap_txt,
        "Evaluaciones": resultado.evaluaciones,
        "Tiempo_Seg": f"{tiempo_total:.4f}",
        "Mejor_Secuencia": "-".join(map(str, resultado.permutacion)),
    })


if __name__ == "__main__":
    main()
