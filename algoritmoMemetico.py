#!/usr/bin/env python3
"""Algoritmo Memético para el Permutation Flow Shop Scheduling Problem (PFSP).

Combina Algoritmo Genético con Búsqueda Local por Inserción (Insertion Local Search).

Uso:
    python3 algoritmoMemetico.py DatosEntrada TamanoPobla ProbaCruza ProbaMuta NumIteraciones Semilla Resultado.csv [FreqBL] [IntensidadBL]
"""

import csv
import os
import sys
import time
import numpy as np


# ==============================================================================
# Funciones Mínimas Requeridas (Sección 7 del Enunciado)
# ==============================================================================

def generar_real_aleatorio() -> float:
    """Genera un número real aleatorio en el intervalo [0, 1]."""
    return float(np.random.rand())


def generar_entero_aleatorio(min_val: int, max_val: int) -> int:
    """Genera un número entero aleatorio en el intervalo cerrado [min_val, max_val]."""
    return int(np.random.randint(min_val, max_val + 1))


def leer_instancia_taillard(ruta_archivo: str):
    """Lee y parsea una instancia de Taillard (matriz de tiempos p_{i,j} y cotas).

    Retorna:
        num_job: int
        num_maq: int
        lim_inf: int (Upper Bound / mejor conocido de referencia)
        lim_sup: int (Lower Bound)
        matriz: np.ndarray con dimensiones (num_maq, num_job)
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo de instancia: {ruta_archivo}")

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        primera_linea = f.readline().strip().split()
        num_job = int(primera_linea[0])
        num_maq = int(primera_linea[1])
        lim_inf = int(primera_linea[3])
        lim_sup = int(primera_linea[4])
        matriz = np.loadtxt(f, dtype=int)

    return num_job, num_maq, lim_inf, lim_sup, matriz


def inicializar_poblacion(tam_pobla: int, num_job: int) -> np.ndarray:
    """Inicializa la población generando permutaciones aleatorias de n trabajos."""
    pobla = np.tile(np.arange(num_job), (tam_pobla, 1))
    for i in range(tam_pobla):
        np.random.shuffle(pobla[i])
    return pobla


def calcular_makespan(individuo: np.ndarray | list[int], matriz: np.ndarray, num_maq: int) -> int:
    """Calcula el tiempo de finalización (Cmax / makespan) para una permutación dada.

    matriz: shape (num_maq, num_job) donde fila = máquina, columna = trabajo.
    """
    tiempos_maquinas = np.zeros(num_maq, dtype=int)
    for trabajo in individuo:
        tiempos_maquinas[0] += matriz[0, trabajo]
        for m in range(1, num_maq):
            if tiempos_maquinas[m] < tiempos_maquinas[m - 1]:
                tiempos_maquinas[m] = tiempos_maquinas[m - 1]
            tiempos_maquinas[m] += matriz[m, trabajo]
    return int(tiempos_maquinas[-1])


def evaluar_poblacion(poblacion: np.ndarray, matriz: np.ndarray, num_maq: int) -> np.ndarray:
    """Calcula el fitness (makespan) de cada individuo en la población."""
    fitness = np.zeros(len(poblacion), dtype=int)
    for i, ind in enumerate(poblacion):
        fitness[i] = calcular_makespan(ind, matriz, num_maq)
    return fitness


def seleccion_torneo(poblacion: np.ndarray, fitness: np.ndarray, k: int = 2) -> np.ndarray:
    """Selecciona un individuo usando selección por torneo binario (minimización)."""
    indices_aspirantes = np.random.randint(0, len(poblacion), size=k)
    mejor_idx = indices_aspirantes[np.argmin(fitness[indices_aspirantes])]
    return poblacion[mejor_idx].copy()


def cruce_ox(padre1: np.ndarray, padre2: np.ndarray, prob_c: float):
    """Operador de cruce Order Crossover (OX) para representaciones de permutación."""
    if generar_real_aleatorio() > prob_c:
        return padre1.copy(), padre2.copy()

    n = len(padre1)
    c1, c2 = sorted(np.random.choice(n, size=2, replace=False))

    def generar_hijo(p1, p2):
        hijo = np.full(n, -1, dtype=int)
        hijo[c1:c2 + 1] = p1[c1:c2 + 1]
        en_hijo = set(hijo[c1:c2 + 1])
        pos_hijo = (c2 + 1) % n
        for i in range(n):
            idx_p2 = (c2 + 1 + i) % n
            gen = p2[idx_p2]
            if gen not in en_hijo:
                hijo[pos_hijo] = gen
                pos_hijo = (pos_hijo + 1) % n
        return hijo

    return generar_hijo(padre1, padre2), generar_hijo(padre2, padre1)


def mutacion_swap(individuo: np.ndarray, prob_m: float) -> np.ndarray:
    """Mutación por intercambio de dos posiciones aleatorias."""
    if generar_real_aleatorio() < prob_m:
        mutado = individuo.copy()
        n = len(mutado)
        i, j = np.random.choice(n, size=2, replace=False)
        mutado[i], mutado[j] = mutado[j], mutado[i]
        return mutado
    return individuo.copy()


def busqueda_local_insercion(
    individuo: np.ndarray,
    matriz: np.ndarray,
    num_maq: int,
    intensidad: int | None = None,
) -> np.ndarray:
    """Aplica búsqueda local por inserción (First-Improvement).

    Extrae trabajos y prueba insertarlos en distintas posiciones;
    si encuentra mejora en el makespan, la adopta de inmediato.
    """
    mejor = individuo.copy()
    mejor_cmax = calcular_makespan(mejor, matriz, num_maq)
    n = len(mejor)

    pases = n if intensidad is None else min(intensidad, n)
    indices = list(range(n))
    np.random.shuffle(indices)

    for idx_origen in indices[:pases]:
        trabajo = mejor[idx_origen]
        sin_trabajo = np.delete(mejor, idx_origen)

        hubo_mejora = False
        # Probar posiciones de inserción aleatorias o secuenciales
        posiciones = list(range(n))
        np.random.shuffle(posiciones)

        for pos_destino in posiciones:
            if pos_destino == idx_origen:
                continue
            candidato = np.insert(sin_trabajo, pos_destino, trabajo)
            cmax_cand = calcular_makespan(candidato, matriz, num_maq)
            if cmax_cand < mejor_cmax:
                mejor = candidato
                mejor_cmax = cmax_cand
                hubo_mejora = True
                break

        if hubo_mejora:
            break

    return mejor


def reemplazar_poblacion_elitismo(
    poblacion_padres: np.ndarray,
    fitness_padres: np.ndarray,
    hijos: list[np.ndarray],
    tam_pobla: int,
    n_elite: int = 1,
) -> np.ndarray:
    """Reemplaza la población conservando a los mejores individuos (elitismo)."""
    orden_elite = np.argsort(fitness_padres)
    nueva = [poblacion_padres[idx].copy() for idx in orden_elite[:n_elite]]
    for h in hijos:
        if len(nueva) >= tam_pobla:
            break
        nueva.append(h.copy())
    return np.array(nueva)


# ==============================================================================
# Bucle Principal del Algoritmo Memético
# ==============================================================================

def ejecutar_algoritmo_memetico(
    tam_pobla: int,
    prob_c: float,
    prob_m: float,
    iteraciones: int,
    matriz: np.ndarray,
    num_maq: int,
    num_job: int,
    freq_bl: int = 1,
    intensidad_bl: int | None = None,
    verbose: bool = True,
):
    """Ejecuta el ciclo generacional del Algoritmo Memético (AG + Búsqueda Local).

    Retorna:
        mejor_solucion: np.ndarray
        mejor_makespan: int
        historial_makespan: list[int]
    """
    # 1. Población inicial y evaluación
    poblacion = inicializar_poblacion(tam_pobla, num_job)
    fitness = evaluar_poblacion(poblacion, matriz, num_maq)

    idx_mejor = int(np.argmin(fitness))
    mejor_solucion = poblacion[idx_mejor].copy()
    mejor_makespan = int(fitness[idx_mejor])
    historial = [mejor_makespan]

    if verbose:
        print(f"Generación 0: Mejor Makespan = {mejor_makespan}")

    # 2. Iteraciones generacionales
    for gen in range(1, iteraciones + 1):
        hijos = []
        while len(hijos) < tam_pobla:
            p1 = seleccion_torneo(poblacion, fitness)
            p2 = seleccion_torneo(poblacion, fitness)

            h1, h2 = cruce_ox(p1, p2, prob_c)
            h1 = mutacion_swap(h1, prob_m)
            h2 = mutacion_swap(h2, prob_m)

            # Etapa Memética: Búsqueda local con frecuencia determinada
            if freq_bl > 0 and (gen % freq_bl == 0):
                h1 = busqueda_local_insercion(h1, matriz, num_maq, intensidad=intensidad_bl)
                h2 = busqueda_local_insercion(h2, matriz, num_maq, intensidad=intensidad_bl)

            hijos.append(h1)
            if len(hijos) < tam_pobla:
                hijos.append(h2)

        # 3. Reemplazo generacional con elitismo
        poblacion = reemplazar_poblacion_elitismo(
            poblacion, fitness, hijos, tam_pobla, n_elite=1
        )
        fitness = evaluar_poblacion(poblacion, matriz, num_maq)

        min_gen = int(np.min(fitness))
        if min_gen < mejor_makespan:
            mejor_makespan = min_gen
            mejor_solucion = poblacion[np.argmin(fitness)].copy()

        historial.append(mejor_makespan)

        if verbose and (gen % 10 == 0 or gen == iteraciones):
            print(f"Generación {gen}/{iteraciones}: Mejor Makespan = {mejor_makespan}")

    return mejor_solucion, mejor_makespan, historial


# ==============================================================================
# Entrada/Salida y Guardado de Resultados
# ==============================================================================

def guardar_resultado_csv(
    ruta_csv: str,
    instancia: str,
    semilla: int,
    tam_pobla: int,
    prob_c: float,
    prob_m: float,
    iteraciones: int,
    mejor_mk: int,
    cota_ref: int,
    rpd: float,
    tiempo_seg: float,
    mejor_sol: np.ndarray,
    freq_bl: int = 1,
    intensidad_bl: int | str = "n",
):
    """Guarda una fila de resultado en el archivo CSV especificado (modo append)."""
    directorio = os.path.dirname(ruta_csv)
    if directorio:
        os.makedirs(directorio, exist_ok=True)

    existe = os.path.exists(ruta_csv)
    with open(ruta_csv, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        if not existe:
            writer.writerow([
                "Instancia", "Semilla", "Poblacion", "Prob_Cruce", "Prob_Mutacion",
                "Iteraciones", "Freq_BL", "Intensidad_BL", "Makespan", "Upper_Bound",
                "RPD_%", "Tiempo_Seg", "Mejor_Secuencia"
            ])

        secuencia_str = "-".join(map(str, mejor_sol))
        writer.writerow([
            instancia, semilla, tam_pobla, prob_c, prob_m,
            iteraciones, freq_bl, intensidad_bl, mejor_mk, cota_ref,
            f"{rpd:.2f}", f"{tiempo_seg:.4f}", secuencia_str
        ])
    print(f"\n[OK] Resultado guardado exitosamente en: {ruta_csv}")


def main():
    if len(sys.argv) not in (8, 9, 10):
        print("Error en la entrada de los parametros")
        print("Uso: python3 algoritmoMemetico.py DatosEntrada TamanoPobla ProbaCruza ProbaMuta NumIteraciones Semilla Resultado.csv [FreqBL] [IntensidadBL]")
        print("donde:")
        print(" - DatosEntrada: archivo de la instancia [ejem: taillards/ins_20_5_00.txt]")
        print(" - TamanoPobla: valor entero positivo [ejem: 20]")
        print(" - ProbaCruza: valor real en (0, 1] [ejem: 0.8]")
        print(" - ProbaMuta: valor real en (0, 1] [ejem: 0.1]")
        print(" - NumIteraciones: valor entero positivo [ejem: 100]")
        print(" - Semilla: valor entero positivo [ejem: 1]")
        print(" - Resultado.csv: archivo de salida para los resultados [ejem: results/res_am.csv]")
        print(" - FreqBL (opcional): frecuencia de búsqueda local cada X generaciones [default: 1]")
        print(" - IntensidadBL (opcional): cantidad de intentos de inserción [default: n trabajos]")
        sys.exit(1)

    entrada = sys.argv[1]
    tam_pobla = int(sys.argv[2])
    prob_c = float(sys.argv[3])
    prob_m = float(sys.argv[4])
    iteracion = int(sys.argv[5])
    semilla = int(sys.argv[6])
    salida = sys.argv[7]
    freq_bl = int(sys.argv[8]) if len(sys.argv) >= 9 else 1
    intensidad_bl = int(sys.argv[9]) if len(sys.argv) >= 10 else None

    print(f"Parámetros cargados: {entrada}, {tam_pobla}, {prob_c}, {prob_m}, {iteracion}, {semilla}, FreqBL={freq_bl}, IntensidadBL={intensidad_bl}")

    # Semilla global para reproducibilidad
    np.random.seed(semilla)

    # Carga de la instancia
    num_job, num_maq, lim_inf, lim_sup, matriz = leer_instancia_taillard(entrada)
    print(f"P1: {num_job}, P2: {num_maq}, P3: {lim_inf}, P4: {lim_sup}")

    # Ejecución
    tiempo_inicio = time.time()
    mejor_sol, mejor_mk, _ = ejecutar_algoritmo_memetico(
        tam_pobla, prob_c, prob_m, iteracion, matriz, num_maq, num_job,
        freq_bl=freq_bl, intensidad_bl=intensidad_bl, verbose=True
    )
    tiempo_total = time.time() - tiempo_inicio

    rpd = ((mejor_mk - lim_inf) / lim_inf) * 100

    print("\n" + "=" * 50)
    print("RESULTADOS FINALES ALGORITMO MEMÉTICO:")
    print(f"Mejor secuencia encontrada: {mejor_sol}")
    print(f"Makespan obtenido:          {mejor_mk}")
    print(f"Upper Bound conocido:       {lim_inf}")
    print(f"RPD (% de error):           {rpd:.2f}%")
    print(f"Tiempo de ejecución:        {tiempo_total:.4f} segundos")
    print("=" * 50)

    guardar_resultado_csv(
        ruta_csv=salida,
        instancia=entrada,
        semilla=semilla,
        tam_pobla=tam_pobla,
        prob_c=prob_c,
        prob_m=prob_m,
        iteraciones=iteracion,
        mejor_mk=mejor_mk,
        cota_ref=lim_inf,
        rpd=rpd,
        tiempo_seg=tiempo_total,
        mejor_sol=mejor_sol,
        freq_bl=freq_bl,
        intensidad_bl="n" if intensidad_bl is None else intensidad_bl,
    )


if __name__ == "__main__":
    main()
