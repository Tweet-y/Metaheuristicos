"""Algoritmo memético: AG de clases + búsqueda local por inserción tras mutar."""

from __future__ import annotations

from pfsp.ga import GAResult, run as run_ga
from pfsp.local_search import insertion_search


def run(
    p,
    seed: int,
    pop_size: int,
    pc: float,
    pm: float,
    iteraciones: int,
    max_evaluations: int | None = None,
    ls_freq: int = 1,
    ls_intensity: int | None = None,
    n_elite: int = 1,
) -> GAResult:
    n = int(p.shape[1])
    intensity = n if ls_intensity is None else ls_intensity

    def after_mutate(child, p_mat, rng, generation: int = 0):
        if ls_freq <= 0 or generation % ls_freq != 0:
            return child, 0
        return insertion_search(child, p_mat, rng, intensity)

    return run_ga(
        p,
        seed=seed,
        pop_size=pop_size,
        pc=pc,
        pm=pm,
        iteraciones=iteraciones,
        max_evaluations=max_evaluations,
        n_elite=n_elite,
        after_mutate=after_mutate,
    )
