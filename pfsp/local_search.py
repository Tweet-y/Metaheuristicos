"""Búsqueda local por inserción (first-improvement) para el memético."""

from __future__ import annotations

from pfsp.makespan import cmax


def insertion_search(perm, p, rng, intensity: int) -> tuple[list[int], int]:
    """Un pase recorre trabajos en orden aleatorio; se queda con la primera mejora."""
    current = list(perm)
    best = cmax(current, p)
    evals = 1
    n = len(current)
    if n < 2 or intensity <= 0:
        return current, evals

    for _ in range(intensity):
        order = list(range(n))
        rng.shuffle(order)
        moved = False
        for i in order:
            job = current[i]
            without = current[:i] + current[i + 1 :]
            for pos in range(n):
                if pos == i:
                    continue
                trial = without[:pos] + [job] + without[pos:]
                cm = cmax(trial, p)
                evals += 1
                if cm < best:
                    current = trial
                    best = cm
                    moved = True
                    break
            if moved:
                break
        if not moved:
            break
    return current, evals
