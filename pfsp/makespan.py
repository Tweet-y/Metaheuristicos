"""Makespan Cmax de una permutación sobre la matriz p (máquinas × trabajos)."""

from __future__ import annotations

import numpy as np


def as_rows(p) -> list[list[int]]:
    """Convierte p a lista de listas (m × n). Una vez por corrida, no por evaluación.

    Idempotente: si ya es lista de listas la devuelve tal cual (nunca se muta).
    """
    if hasattr(p, "tolist"):
        return p.tolist()
    return p if isinstance(p[0], list) else [list(fila) for fila in p]


def cmax_rows(seq, rows: list[list[int]]) -> int:
    """Cmax de una secuencia (parcial o completa) sobre p ya convertida a listas.

    Ruta caliente del AG. Sin validación y sin indexar ndarray dentro del bucle
    (~5x más rápido). Mantiene solo el vector de estado de m máquinas en lugar de
    la tabla completa n × m, según la recurrencia
    C(j, k) = max(C(j, k-1), C(j-1, k)) + p[j][pi_k].
    """
    m = len(rows)
    t = [0] * m
    for job in seq:
        t[0] += rows[0][job]
        for j in range(1, m):
            if t[j] < t[j - 1]:
                t[j] = t[j - 1]
            t[j] += rows[j][job]
    return t[-1]


def cmax(perm: list[int] | np.ndarray, p) -> int:
    """Cmax de una permutación completa, validando que efectivamente lo sea.

    Frontera de confianza (entrada de usuario, tests). Dentro del ciclo evolutivo
    se usa `cmax_rows`, cuyas permutaciones ya vienen construidas por los operadores.
    """
    rows = as_rows(p)
    n = len(rows[0])
    perm = [int(job) for job in perm]
    if sorted(perm) != list(range(n)):
        raise ValueError("la permutación debe contener cada trabajo exactamente una vez")
    return cmax_rows(perm, rows)
