"""Algoritmo genético para PFSP (pasos 1–12 del material de clases)."""

from __future__ import annotations

from dataclasses import dataclass, field

from pfsp.makespan import as_rows, cmax_rows
from pfsp.neh import neh
from pfsp.operators import (
    init_population,
    mutar_intercambio,
    ox_crossover,
    reemplazo_generacional,
    torneo_binario,
)
from pfsp.rng import rand_float, seeded_rng


@dataclass
class GAResult:
    permutacion: list[int]
    cmax: int
    evaluaciones: int
    historial: list[int] = field(default_factory=list)


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
    after_generation=None,
    use_neh: bool = True,
    seed_perm: list[int] | None = None,
) -> GAResult:
    """Ciclo generacional del AG.

    `seed_perm`: secuencia ya construida con NEH. Si se omite y `use_neh`, se
    calcula aquí; pasarla evita recalcular NEH en cada réplica de una misma
    instancia (el experimento lo hace una vez por instancia).
    """
    rng = seeded_rng(seed)
    rows = as_rows(p)
    n = len(rows[0])

    # 1: Generar una población inicial de individuos
    poblacion = init_population(rng, n, pop_size)
    if pop_size > 0 and (seed_perm is not None or use_neh):
        poblacion[0] = list(seed_perm) if seed_perm is not None else neh(rows)

    # 2: Evaluar la aptitud de cada individuo en la población inicial
    cmaxs = [cmax_rows(ind, rows) for ind in poblacion]
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

            # 5: Seleccionar individuos (torneo binario: gana el de menor Cmax)
            p1 = torneo_binario(rng, poblacion, cmaxs)
            p2 = torneo_binario(rng, poblacion, cmaxs)

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

            # 7b: Gancho del memético (búsqueda local lamarckiana sobre el hijo)
            if after_mutate is not None:
                c1, extra1 = after_mutate(c1, rows, rng, generation=gen)
                c2, extra2 = after_mutate(c2, rows, rng, generation=gen)
                evaluaciones += extra1 + extra2

            # 8: Evaluar la aptitud de cada individuo en la descendencia
            for child in (c1, c2):
                if len(hijos) >= pop_size:
                    break
                if max_evaluations is not None and evaluaciones >= max_evaluations:
                    break
                cm = cmax_rows(child, rows)
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
        gen_best = min(cmaxs)
        if after_generation is not None:
            best_idx = cmaxs.index(gen_best)
            mej_ind, extra = after_generation(poblacion[best_idx], rows, rng, generation=gen)
            evaluaciones += extra
            mej_c = cmax_rows(mej_ind, rows)
            evaluaciones += 1
            if mej_c < cmaxs[best_idx]:
                poblacion[best_idx] = mej_ind
                cmaxs[best_idx] = mej_c
                gen_best = mej_c

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
