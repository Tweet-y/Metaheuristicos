"""Búsqueda local por inserción (first-improvement) para el memético."""

from __future__ import annotations

from pfsp.makespan import as_rows, cmax_rows


def insertion_costs(seq: list[int], job: int, rows: list[list[int]]) -> list[int]:
    """Cmax de insertar `job` en cada una de las len(seq)+1 posiciones de `seq`.

    Aceleración de Taillard (1990). Una pasada hacia adelante calcula los tiempos
    de término `e` de la secuencia sin el trabajo, y una pasada hacia atrás calcula
    las colas `q` (tiempo desde que empieza cada posición hasta el fin del
    programa). Con ambas, cada posición de inserción se evalúa en O(m), de modo
    que las len(seq)+1 posiciones cuestan O(len(seq) * m) en total en lugar de
    O(len(seq)^2 * m) al reconstruir y evaluar cada permutación completa.

    El resultado es exactamente el mismo que evaluar cada inserción por separado.
    """
    m = len(rows)
    largo = len(seq)

    # e[i][j]: instante de término del trabajo en posición i sobre la máquina j.
    e = [[0] * m for _ in range(largo)]
    for i in range(largo):
        fila_e = e[i]
        previa = e[i - 1] if i > 0 else None
        izquierda = 0
        for j in range(m):
            arriba = previa[j] if previa is not None else 0
            izquierda = (arriba if arriba > izquierda else izquierda) + rows[j][seq[i]]
            fila_e[j] = izquierda

    # q[i][j]: cola desde que la posición i empieza en la máquina j hasta el final.
    q = [[0] * m for _ in range(largo)]
    for i in range(largo - 1, -1, -1):
        fila_q = q[i]
        siguiente = q[i + 1] if i + 1 < largo else None
        derecha = 0
        for j in range(m - 1, -1, -1):
            abajo = siguiente[j] if siguiente is not None else 0
            derecha = (abajo if abajo > derecha else derecha) + rows[j][seq[i]]
            fila_q[j] = derecha

    # f[j]: término del trabajo insertado en la posición pos sobre la máquina j.
    costos = []
    for pos in range(largo + 1):
        previa = e[pos - 1] if pos > 0 else None
        cola = q[pos] if pos < largo else None
        f = 0
        peor = 0
        for j in range(m):
            arriba = previa[j] if previa is not None else 0
            f = (arriba if arriba > f else f) + rows[j][job]
            total = f + (cola[j] if cola is not None else 0)
            if total > peor:
                peor = total
        costos.append(peor)
    return costos


def insertion_search(perm, p, rng, intensity: int) -> tuple[list[int], int]:
    """Búsqueda local por inserción, first-improvement.

    Recorre `intensity` trabajos en orden aleatorio; para cada uno lo extrae y
    prueba reinsertarlo, adoptando la primera posición que mejore el Cmax. Es
    lamarckiana: la permutación mejorada reemplaza a la original.

    Devuelve (permutación, evaluaciones consumidas). El conteo es el número de
    inserciones examinadas, no el costo interno de la aceleración, de modo que el
    presupuesto iso-evaluaciones mide el mismo trabajo lógico que mediría una
    implementación ingenua.
    """
    rows = as_rows(p)
    current = list(perm)
    best = cmax_rows(current, rows)
    evals = 1
    n = len(current)
    if n < 2 or intensity <= 0:
        return current, evals

    k_jobs = min(intensity, n)
    jobs_to_test = list(range(n))
    rng.shuffle(jobs_to_test)

    for job in jobs_to_test[:k_jobs]:
        idx = current.index(job)
        without = current[:idx] + current[idx + 1 :]
        costos = insertion_costs(without, job, rows)
        for pos in range(n):
            if pos == idx:
                continue
            evals += 1
            if costos[pos] < best:
                current = without[:pos] + [job] + without[pos:]
                best = costos[pos]
                break
    return current, evals
