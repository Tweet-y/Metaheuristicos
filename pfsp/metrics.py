"""Métricas de gap respecto al upper bound de Taillard."""


def rpd(cmax_obtenido: float, ub: float | None) -> float | None:
    if ub is None or ub == 0:
        return None
    return 100.0 * (cmax_obtenido - ub) / ub
