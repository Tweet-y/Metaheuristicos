"""Ciclo evolutivo común al Algoritmo Genético y al Memético.

El Memético es el mismo algoritmo más una etapa de explotación: por eso ambos
comparten este motor y se distinguen solo por el argumento `usar_bl`.
"""

from pfsp.local_search import busqueda_local_insercion
from pfsp.makespan import calcular_makespan, evaluar_poblacion
from pfsp.neh import neh, orden_neh
from pfsp.operators import (
    cruce_ox,
    inicializar_poblacion,
    mutar_individuo,
    reemplazo_mu_lambda,
    renovar_poblacion,
    seleccion_torneo,
)

K_TORNEO = 3

# Individuos que, además del mejor, reciben búsqueda local en cada aplicación.
# Medido sobre 5 semillas con 60 individuos y 300 generaciones, el RPD promedio
# baja de 0.83% a 0.46% en 50x10 y de 0.53% a 0.45% en 100x10 al pasar de 0 a 1;
# subir a 3 o 6 sigue mejorando poco pero duplica el tiempo.
BL_MUESTRA = 1


def ejecutar_evolutivo(tam_pobla, prob_c, prob_m, iteraciones, matriz, num_maq, num_job,
                       usar_bl=False, freq_bl=1, bl_muestra=BL_MUESTRA, sembrar_neh=True,
                       cota_superior=None, k_torneo=K_TORNEO, mostrar_progreso=True,
                       paciencia_renovacion=None, frac_renovacion=0.20,
                       reparar_renovados=True, semillas_neh=1):
    """Ejecuta el ciclo evolutivo y devuelve (mejor_solucion, makespan, traza).

    `traza` es la lista de pares (generación, makespan) con cada mejora del mejor
    valor histórico; sirve para graficar en qué generación se halló la solución.

    Con `usar_bl=True` se aplica búsqueda local por inserción sobre el mejor
    individuo cada `freq_bl` generaciones, que es la variante Memética.
    """
    poblacion = inicializar_poblacion(tam_pobla, num_job)
    if sembrar_neh:
        if semillas_neh <= 1:
            poblacion[0] = neh(matriz, num_maq, num_job)
        else:
            orden_base = orden_neh(matriz, num_maq, num_job)
            poblacion[0] = neh(matriz, num_maq, num_job, orden=orden_base)
            for i in range(1, min(semillas_neh, tam_pobla)):
                orden_pert = mutar_individuo(orden_base, 1.0)
                poblacion[i] = neh(matriz, num_maq, num_job, orden=orden_pert)
    fitness = evaluar_poblacion(poblacion, matriz, num_maq)

    idx_mejor = min(range(tam_pobla), key=lambda i: fitness[i])
    mejor_solucion = list(poblacion[idx_mejor])
    mejor_makespan = fitness[idx_mejor]
    traza = [(0, mejor_makespan)]

    # Secuencias que ya quedaron en óptimo local. Como la búsqueda local es
    # determinista, relanzarla sobre una de ellas devolvería exactamente lo mismo:
    # saltarla no cambia el resultado y evita repetir una pasada completa del
    # vecindario en cada generación, que era donde se iba casi todo el tiempo.
    ya_optimizados = set()
    paso_progreso = max(1, iteraciones // 10)
    gen_sin_mejora = 0

    for gen in range(1, iteraciones + 1):
        if usar_bl and gen % freq_bl == 0:
            # Se explota al mejor y, tras él, a los siguientes mejores. Estos
            # últimos son descendientes de una cruza estocástica, así que hacen
            # que la corrida dependa de la semilla; y por venir ya de buena
            # calidad, la búsqueda local converge en pocas pasadas, bastante más
            # barato que explotar individuos tomados al azar.
            explotados = 0
            for idx in range(len(poblacion)):
                if explotados > bl_muestra:
                    break
                if tuple(poblacion[idx]) in ya_optimizados:
                    continue
                poblacion[idx], fitness[idx] = busqueda_local_insercion(
                    poblacion[idx], matriz, num_maq)
                ya_optimizados.add(tuple(poblacion[idx]))
                explotados += 1

        hijos = []
        fitness_hijos = []
        while len(hijos) < tam_pobla:
            padre1 = seleccion_torneo(poblacion, fitness, k_torneo)
            padre2 = seleccion_torneo(poblacion, fitness, k_torneo)
            for hijo in cruce_ox(padre1, padre2, prob_c):
                if len(hijos) < tam_pobla:
                    hijo = mutar_individuo(hijo, prob_m)
                    hijos.append(hijo)
                    fitness_hijos.append(calcular_makespan(hijo, matriz, num_maq))

        poblacion, fitness = reemplazo_mu_lambda(poblacion, fitness, hijos, fitness_hijos)

        # El reemplazo devuelve la población ordenada, así que la posición 0 es la mejor.
        if fitness[0] < mejor_makespan:
            mejor_makespan = fitness[0]
            mejor_solucion = list(poblacion[0])
            traza.append((gen, mejor_makespan))
            gen_sin_mejora = 0
        else:
            gen_sin_mejora += 1

        if paciencia_renovacion is not None and gen_sin_mejora >= paciencia_renovacion:
            reparador = (lambda ind: busqueda_local_insercion(ind, matriz, num_maq)[0]) if (usar_bl and reparar_renovados) else None
            poblacion, fitness = renovar_poblacion(
                poblacion, fitness, num_job,
                lambda ind: calcular_makespan(ind, matriz, num_maq),
                frac_renovacion=frac_renovacion,
                reparador=reparador,
            )
            gen_sin_mejora = 0
            if fitness[0] < mejor_makespan:
                mejor_makespan = fitness[0]
                mejor_solucion = list(poblacion[0])
                traza.append((gen, mejor_makespan))

        if mostrar_progreso and (gen % paso_progreso == 0 or gen == iteraciones):
            print(f"Generación {gen}/{iteraciones}: Mejor Makespan = {mejor_makespan}")

        if cota_superior is not None and mejor_makespan <= cota_superior:
            print(f"\n[!] Se alcanzó la cota superior conocida ({cota_superior}) "
                  f"en la generación {gen}.")
            break

    return mejor_solucion, mejor_makespan, traza
