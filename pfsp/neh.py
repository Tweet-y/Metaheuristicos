"""Heurística constructiva NEH (Nawaz, Enscore y Ham, 1983)."""

from pfsp.local_search import costos_insercion


def orden_neh(matriz, num_maq, num_job):
    """Ordena los trabajos por tiempo total de proceso decreciente."""
    totales = [sum(matriz[m][j] for m in range(num_maq)) for j in range(num_job)]
    return sorted(range(num_job), key=lambda j: -totales[j])


def neh(matriz, num_maq, num_job, orden=None):
    """Secuencia construida por NEH.

    1. Ordena los trabajos por tiempo total de proceso decreciente, de modo que
       los trabajos más largos se coloquen primero, cuando aún queda libertad
       para acomodarlos.
    2. Inserta cada trabajo en la posición de la secuencia parcial que minimiza
       el makespan parcial, y fija esa decisión sin retroceder.

    Reutiliza `costos_insercion`, así que evaluar las posiciones candidatas de
    cada trabajo cuesta O(n*m) y la construcción completa O(n^2 * m).

    Sirve para sembrar un individuo de la población inicial: partir de una
    solución razonable en vez de puro azar acorta mucho la búsqueda.
    """
    if orden is None:
        orden = orden_neh(matriz, num_maq, num_job)

    secuencia = [orden[0]]
    for trabajo in orden[1:]:
        costos = costos_insercion(secuencia, trabajo, matriz, num_maq)
        mejor_pos = min(range(len(costos)), key=lambda pos: costos[pos])
        secuencia = secuencia[:mejor_pos] + [trabajo] + secuencia[mejor_pos:]
    return secuencia
