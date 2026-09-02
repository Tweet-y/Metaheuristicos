"""Makespan Cmax de una permutación sobre la matriz p (máquinas × trabajos)."""

from __future__ import annotations

import numpy as np


def cmax(perm: list[int] | np.ndarray, p: np.ndarray) -> int:
    perm = [int(job) for job in perm]
    m, n = p.shape
    if sorted(perm) != list(range(n)):
        raise ValueError("la permutación debe contener cada trabajo exactamente una vez")

    completion = np.zeros((len(perm), m), dtype=int)
    for i, job in enumerate(perm):
        for j in range(m):
            prev_job = completion[i - 1, j] if i > 0 else 0
            prev_machine = completion[i, j - 1] if j > 0 else 0
            completion[i, j] = max(prev_job, prev_machine) + int(p[j, job])
    return int(completion[-1, -1])
