"""Generadores acotados sobre random.Random para operadores reproducibles."""

from __future__ import annotations

import random


def seeded_rng(seed: int) -> random.Random:
    return random.Random(seed)


def rand_float(rng: random.Random) -> float:
    """Número real en [0, 1]."""
    return rng.random()


def rand_int(rng: random.Random, low: int, high: int) -> int:
    """Entero uniforme en [low, high], ambos inclusive."""
    return rng.randint(low, high)
