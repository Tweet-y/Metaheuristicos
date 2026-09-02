"""Carga de instancias Taillard: filas = máquinas, columnas = trabajos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class Instance:
    n: int
    m: int
    p: np.ndarray
    ub: int | None
    lb: int | None
    path: Path


def load(path: str | Path) -> Instance:
    path = Path(path)
    raw = path.read_text(encoding="utf-8").split()
    if len(raw) < 2:
        raise ValueError(f"archivo de instancia vacío o incompleto: {path}")

    n = int(raw[0])
    m = int(raw[1])
    ub = int(raw[3]) if len(raw) > 3 else None
    lb = int(raw[4]) if len(raw) > 4 else None

    values = [int(x) for x in raw[5 : 5 + m * n]]
    if len(values) != m * n:
        raise ValueError(
            f"{path}: se esperaban {m * n} tiempos, se leyeron {len(values)}"
        )

    p = np.array(values, dtype=int).reshape(m, n)
    return Instance(n=n, m=m, p=p, ub=ub, lb=lb, path=path)
