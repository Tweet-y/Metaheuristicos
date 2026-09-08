"""Biblioteca de operadores genéticos para representación por permutación.

Selección: `torneo_binario` (la que usa el AG) y `ruleta` proporcional a λ=1/Cmax,
conservada como alternativa del material de clases y como término de comparación
en el informe: sobre instancias de Taillard los Cmax de una población difieren
pocos puntos porcentuales, así que la ruleta reparte probabilidades casi uniformes
(presión de selección ≈ 1) y degenera en selección aleatoria.
"""

from __future__ import annotations

from pfsp.rng import rand_float, rand_int


def init_population(rng, n: int, size: int) -> list[list[int]]:
    population = []
    for _ in range(size):
        perm = list(range(n))
        rng.shuffle(perm)
        population.append(perm)
    return population


def aptitud(cmax_val: int | float) -> float:
    """λ = 1/Cmax: mayor aptitud = menor makespan (ruleta maximiza λ)."""
    if cmax_val <= 0:
        raise ValueError("Cmax debe ser positivo")
    return 1.0 / float(cmax_val)


def ruleta(rng, poblacion, lambdas) -> list[int]:
    """p_i = λ_i / Σ λ_j (selección proporcional a la aptitud)."""
    total = sum(lambdas)
    if total <= 0:
        return list(poblacion[rand_int(rng, 0, len(poblacion) - 1)])
    u = rand_float(rng) * total
    acc = 0.0
    for ind, lam in zip(poblacion, lambdas):
        acc += lam
        if u <= acc:
            return list(ind)
    return list(poblacion[-1])


def torneo_binario(rng, poblacion, cmaxs, k: int = 2) -> list[int]:
    """Selección por torneo de tamaño k (minimiza makespan / cmax)."""
    n = len(poblacion)
    aspirantes = [rand_int(rng, 0, n - 1) for _ in range(k)]
    mejor_idx = min(aspirantes, key=lambda i: cmaxs[i])
    return list(poblacion[mejor_idx])


def ox_with_cuts(p1, p2, start: int, end: int) -> tuple[list[int], list[int]]:
    return _ox_child(p1, p2, start, end), _ox_child(p2, p1, start, end)


def ox_crossover(rng, p1, p2) -> tuple[list[int], list[int]]:
    n = len(p1)
    a = rand_int(rng, 0, n - 1)
    b = rand_int(rng, 0, n - 1)
    start, end = (a, b) if a <= b else (b, a)
    return ox_with_cuts(p1, p2, start, end)


def _ox_child(segment_parent, fill_parent, start: int, end: int) -> list[int]:
    n = len(segment_parent)
    child: list[int | None] = [None] * n
    child[start : end + 1] = segment_parent[start : end + 1]
    used = set(segment_parent[start : end + 1])
    write = (end + 1) % n
    for gene in fill_parent[end + 1 :] + fill_parent[: end + 1]:
        if gene in used:
            continue
        child[write] = gene
        write = (write + 1) % n
    return [int(g) for g in child]


def mutar_intercambio(rng, perm) -> list[int]:
    """Mutación por permutación: intercambia dos genes (slide de clases)."""
    child = list(perm)
    n = len(child)
    if n < 2:
        return child
    i = rand_int(rng, 0, n - 1)
    j = rand_int(rng, 0, n - 2)
    if j >= i:
        j += 1
    child[i], child[j] = child[j], child[i]
    return child


def reemplazo_generacional(padres, cmax_padres, hijos, cmax_hijos, n_elite: int = 1):
    """Hijos sustituyen a los padres; elitismo 1 reinserta el mejor padre si es mejor."""
    next_pop = [list(h) for h in hijos]
    next_c = list(cmax_hijos)
    if not next_pop:
        return [list(p) for p in padres], list(cmax_padres)
    if n_elite <= 0:
        return next_pop, next_c
    best_p = min(range(len(padres)), key=lambda i: cmax_padres[i])
    worst_h = max(range(len(next_pop)), key=lambda i: next_c[i])
    if cmax_padres[best_p] < next_c[worst_h]:
        next_pop[worst_h] = list(padres[best_p])
        next_c[worst_h] = cmax_padres[best_p]
    return next_pop, next_c
