"""Heurística constructiva NEH (Nawaz, Enscore, Ham, 1983) para PFSP.

Cumple dos roles en este proyecto:
  * línea base de referencia en las tablas del informe,
  * sembrado de la población inicial del AG/AM (`ga.run(use_neh=True)`).
"""

from __future__ import annotations

from pfsp.makespan import as_rows, cmax_rows


def neh(p) -> list[int]:
    """Secuencia construida por NEH sobre p (m máquinas × n trabajos).

    1. Ordena los trabajos por tiempo total de procesamiento decreciente.
    2. Inserta cada trabajo en la posición de la secuencia parcial que minimiza
       el makespan parcial, y fija esa decisión (constructivo, sin retroceso).
    """
    rows = as_rows(p)
    m, n = len(rows), len(rows[0])
    if n <= 1:
        return list(range(n))

    totales = [sum(rows[j][i] for j in range(m)) for i in range(n)]
    orden = sorted(range(n), key=lambda i: -totales[i])

    seq = [orden[0]]
    for job in orden[1:]:
        seq = min(
            (seq[:pos] + [job] + seq[pos:] for pos in range(len(seq) + 1)),
            key=lambda cand: cmax_rows(cand, rows),
        )
    return seq
