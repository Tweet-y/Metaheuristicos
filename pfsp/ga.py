"""Algoritmo genético para PFSP (pasos 1–12 del material de clases)."""

from __future__ import annotations

from dataclasses import dataclass, field

from pfsp.makespan import cmax
from pfsp.operators import (
    aptitud,
    init_population,
    mutar_intercambio,
    ox_crossover,
    reemplazo_generacional,
    ruleta,
)
from pfsp.rng import rand_float, seeded_rng


@dataclass
class GAResult:
    permutacion: list[int]
    cmax: int
    evaluaciones: int
    historial: list[int] = field(default_factory=list)


def _evaluar(poblacion, p):
    cmaxs = [cmax(ind, p) for ind in poblacion]
    lambdas = [aptitud(cm) for cm in cmaxs]
    return cmaxs, lambdas


def run(
    p,
    seed: int,
    pop_size: int,
    pc: float,
    pm: float,
    iteraciones: int,
    max_evaluations: int | None = None,
    n_elite: int = 1,
    after_mutate=None,
) -> GAResult:
    rng = seeded_rng(seed)
    n = int(p.shape[1])

    # 1: Generar una población inicial de individuos
    poblacion = init_population(rng, n, pop_size)

    # 2: Evaluar la aptitud de cada individuo en la población inicial
    cmaxs, lambdas = _evaluar(poblacion, p)
    evaluaciones = pop_size
    best_i = min(range(pop_size), key=lambda i: cmaxs[i])
    best_perm = list(poblacion[best_i])
    best_c = cmaxs[best_i]
    historial = [best_c]

    gen = 0
    # 3: while no se cumpla la condición de término
    while gen < iteraciones:
        if max_evaluations is not None and evaluaciones >= max_evaluations:
            break

        hijos: list[list[int]] = []
        cmax_hijos: list[int] = []

        # 4: for un tamaño predeterminado de población
        while len(hijos) < pop_size:
            if max_evaluations is not None and evaluaciones >= max_evaluations:
                break

            # 5: Seleccionar individuos (ruleta: a mayor aptitud, mayor probabilidad)
            p1 = ruleta(rng, poblacion, lambdas)
            p2 = ruleta(rng, poblacion, lambdas)

            # 6: Aplicar cruza a los padres (no todos cruzan: probabilidad pc)
            if rand_float(rng) < pc:
                c1, c2 = ox_crossover(rng, p1, p2)
            else:
                c1, c2 = list(p1), list(p2)

            # 7: Aplicar mutación a la descendencia (probabilidad pm)
            if rand_float(rng) < pm:
                c1 = mutar_intercambio(rng, c1)
            if rand_float(rng) < pm:
                c2 = mutar_intercambio(rng, c2)

            if after_mutate is not None:
                c1, extra1 = after_mutate(c1, p, rng, generation=gen)
                c2, extra2 = after_mutate(c2, p, rng, generation=gen)
                evaluaciones += extra1 + extra2

            # 8: Evaluar la aptitud de cada individuo en la descendencia
            for child in (c1, c2):
                if len(hijos) >= pop_size:
                    break
                if max_evaluations is not None and evaluaciones >= max_evaluations:
                    break
                cm = cmax(child, p)
                evaluaciones += 1
                hijos.append(child)
                cmax_hijos.append(cm)
                if cm < best_c:
                    best_c = cm
                    best_perm = list(child)

        if not hijos:
            break

        # 9: Generar una nueva población aplicando el operador de reemplazo
        poblacion, cmaxs = reemplazo_generacional(
            poblacion, cmaxs, hijos, cmax_hijos, n_elite=n_elite
        )
        lambdas = [aptitud(cm) for cm in cmaxs]
        gen_best = min(cmaxs)
        if gen_best < best_c:
            best_c = gen_best
            best_perm = list(poblacion[cmaxs.index(gen_best)])
        historial.append(best_c)
        gen += 1

    # 12: return la mejor solución encontrada
    return GAResult(
        permutacion=best_perm,
        cmax=best_c,
        evaluaciones=evaluaciones,
        historial=historial,
    )
