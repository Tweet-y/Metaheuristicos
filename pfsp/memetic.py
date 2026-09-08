"""Algoritmo memético: AG de clases + búsqueda local por inserción tras mutar."""

from __future__ import annotations

from pfsp.ga import GAResult, run as run_ga
from pfsp.local_search import insertion_search
from pfsp.makespan import as_rows


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
    use_neh: bool = True,
    seed_perm: list[int] | None = None,
    target_best: bool = True,
) -> GAResult:
    """AG idéntico al de `pfsp.ga` más búsqueda local por inserción.

    `target_best`: aplicar la búsqueda local sobre el mejor individuo de la generación
    (recomendado en README §4 y literatura; evita explosión de cómputo sobre descendencia
    no prometedora).
    `ls_freq`: aplicar la búsqueda local cada X generaciones (1 = siempre).
    `ls_intensity`: cuántos trabajos se intentan reinsertar por llamada (None = n).
    """
    intensity = len(as_rows(p)[0]) if ls_intensity is None else ls_intensity

    def ls_hook(ind, rows, rng, generation: int = 0):
        if ls_freq <= 0 or generation % ls_freq != 0:
            return ind, 0
        return insertion_search(ind, rows, rng, intensity)

    return run_ga(
        p,
        seed=seed,
        pop_size=pop_size,
        pc=pc,
        pm=pm,
        iteraciones=iteraciones,
        max_evaluations=max_evaluations,
        n_elite=n_elite,
        after_mutate=None if target_best else ls_hook,
        after_generation=ls_hook if target_best else None,
        use_neh=use_neh,
        seed_perm=seed_perm,
    )
