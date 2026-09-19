"""Operadores genéticos para representación por permutación.

Son genéricos respecto del problema: ninguno consulta la matriz de tiempos, solo
manipulan listas de enteros sin repetición y, cuando necesitan comparar, reciben
los valores de aptitud ya calculados. Eso los hace reutilizables en cualquier
problema cuya solución sea una permutación (TSP, QAP, secuenciamiento en general).
"""

import random

from pfsp.rng import aleatorio_entero, aleatorio_real


def _dos_posiciones_distintas(n):
    """Par de índices distintos en [0, n-1], sin sesgo hacia ningún par."""
    i = aleatorio_entero(0, n - 1)
    j = aleatorio_entero(0, n - 2)
    if j >= i:
        j += 1
    return i, j


def inicializar_poblacion(tam_pobla, num_job):
    """Población inicial de permutaciones aleatorias uniformes."""
    poblacion = []
    for _ in range(tam_pobla):
        individuo = list(range(num_job))
        random.shuffle(individuo)
        poblacion.append(individuo)
    return poblacion


def seleccion_torneo(poblacion, fitness, k=3):
    """Torneo determinista de tamaño k: gana el de menor makespan.

    k regula la presión selectiva. Con k=2 la presión resulta demasiado baja para
    este problema y la población deriva sin converger, así que el valor por
    defecto es 3.
    """
    n = len(poblacion)
    aspirantes = [aleatorio_entero(0, n - 1) for _ in range(k)]
    ganador = min(aspirantes, key=lambda i: fitness[i])
    return list(poblacion[ganador])


def cruce_ox(padre1, padre2, prob_c):
    """Cruce por orden (Order Crossover, OX).

    Copia un segmento contiguo del primer padre y completa las posiciones libres
    con los genes del segundo en su orden relativo, empezando justo después del
    segmento. Preserva el orden relativo y nunca produce repetidos.
    """
    if aleatorio_real() > prob_c:
        return list(padre1), list(padre2)

    n = len(padre1)
    corte1 = aleatorio_entero(0, n - 1)
    corte2 = aleatorio_entero(0, n - 1)
    if corte1 > corte2:
        corte1, corte2 = corte2, corte1

    def generar_hijo(donante_segmento, donante_relleno):
        hijo = [None] * n
        hijo[corte1:corte2 + 1] = donante_segmento[corte1:corte2 + 1]
        usados = set(hijo[corte1:corte2 + 1])
        escritura = (corte2 + 1) % n
        for i in range(n):
            gen = donante_relleno[(corte2 + 1 + i) % n]
            if gen not in usados:
                hijo[escritura] = gen
                escritura = (escritura + 1) % n
        return hijo

    return generar_hijo(padre1, padre2), generar_hijo(padre2, padre1)


def mutacion_swap(individuo, prob_m):
    """Intercambia dos trabajos de posición, con probabilidad prob_m."""
    if aleatorio_real() >= prob_m:
        return list(individuo)
    mutado = list(individuo)
    i, j = _dos_posiciones_distintas(len(mutado))
    mutado[i], mutado[j] = mutado[j], mutado[i]
    return mutado


def mutacion_insercion(individuo, prob_m):
    """Extrae un trabajo y lo reinserta en otra posición, con probabilidad prob_m."""
    if aleatorio_real() >= prob_m:
        return list(individuo)
    mutado = list(individuo)
    i, j = _dos_posiciones_distintas(len(mutado))
    mutado.insert(j, mutado.pop(i))
    return mutado


def mutar_individuo(individuo, prob_m):
    """Aplica swap o inserción, eligiendo entre ambos con igual probabilidad."""
    if aleatorio_real() < 0.5:
        return mutacion_swap(individuo, prob_m)
    return mutacion_insercion(individuo, prob_m)


def reemplazo_mu_lambda(padres, fitness_padres, hijos, fitness_hijos, sin_duplicados=True):
    """Reemplazo (mu+lambda): padres e hijos compiten y sobreviven los mu mejores.

    Es elitista por construcción, así que la mejor solución encontrada nunca se
    pierde y no hace falta un caso especial para el élite. Sustituye al reemplazo
    generacional con un solo élite, bajo el cual los hijos peores que sus padres
    entraban igual a la población y anulaban la presión selectiva.

    Con `sin_duplicados` la población se queda con los mejores *distintos*. Hace
    falta: un elitismo tan fuerte deja que la mejor solución se copie a sí misma
    hasta llenar la población (medido sin este filtro, en la generación 10 había
    2 individuos distintos y 56 copias del mismo), con lo cual la cruza solo
    combina clones y el algoritmo deja de explorar. Si no hay mu individuos
    distintos se completa con los repetidos, para no achicar la población.

    Empata a favor del padre (el orden es estable), lo que evita que la población
    derive entre individuos de igual makespan. Devuelve la población ordenada por
    makespan ascendente, de modo que la posición 0 es siempre la mejor solución.
    """
    mu = len(padres)
    combinados = list(zip(fitness_padres, padres)) + list(zip(fitness_hijos, hijos))
    combinados.sort(key=lambda par: par[0])

    if not sin_duplicados:
        sobrevivientes = combinados[:mu]
    else:
        sobrevivientes = []
        repetidos = []
        vistos = set()
        for valor, individuo in combinados:
            clave = tuple(individuo)
            if clave in vistos:
                repetidos.append((valor, individuo))
            else:
                vistos.add(clave)
                sobrevivientes.append((valor, individuo))
                if len(sobrevivientes) == mu:
                    break
        sobrevivientes.extend(repetidos[:mu - len(sobrevivientes)])

    return [list(individuo) for _, individuo in sobrevivientes], [f for f, _ in sobrevivientes]


def renovar_poblacion(poblacion, fitness, num_job, evaluador, frac_renovacion=0.20, reparador=None):
    """Reemplaza los peores individuos tras estancamiento, preservando el élite.

    Genera mitad perturbaciones del élite y mitad soluciones aleatorias uniformes.
    Si se pasa `reparador`, se aplica únicamente sobre los mutantes del élite.
    Inserta directamente en la población evaluando con `evaluador(individuo)`.
    Si la población tiene tamaño <= 1 o frac_renovacion <= 0, no modifica nada.
    Devuelve (poblacion, fitness) con el mismo tamaño y ordenados por fitness.
    """
    n = len(poblacion)
    if n <= 1 or frac_renovacion <= 0:
        return [list(ind) for ind in poblacion], list(fitness)

    num_renovar = int(round(n * frac_renovacion))
    if num_renovar >= n:
        num_renovar = n - 1
    if num_renovar <= 0:
        return [list(ind) for ind in poblacion], list(fitness)

    pob_nueva = [list(ind) for ind in poblacion]
    fit_nuevo = list(fitness)

    elite = poblacion[0]
    nuevos = []
    n_mutados = num_renovar // 2
    for _ in range(n_mutados):
        mut = mutar_individuo(elite, 1.0)
        if reparador is not None:
            mut = reparador(mut)
        nuevos.append(mut)
    for _ in range(num_renovar - n_mutados):
        ind = list(range(num_job))
        random.shuffle(ind)
        nuevos.append(ind)

    idx_inicio = n - num_renovar
    for i, ind in enumerate(nuevos):
        pob_nueva[idx_inicio + i] = ind
        fit_nuevo[idx_inicio + i] = evaluador(ind)

    ordenados = sorted(zip(fit_nuevo, pob_nueva), key=lambda par: par[0])
    return [list(ind) for _, ind in ordenados], [f for f, _ in ordenados]

