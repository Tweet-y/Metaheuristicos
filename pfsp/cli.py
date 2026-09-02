"""CLI compartido: 7 parámetros del profesor (español + alias en inglés)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pfsp.ga import run as run_ga
from pfsp.instance import load
from pfsp.memetic import run as run_memetic
from pfsp.metrics import rpd


def _positivo_entero(texto: str) -> int:
    try:
        valor = int(texto)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un entero") from exc
    if valor < 1:
        raise argparse.ArgumentTypeError("debe ser un entero positivo (>= 1)")
    return valor


def _probabilidad(texto: str) -> float:
    try:
        valor = float(texto)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("debe ser un número real") from exc
    if not 0.0 < valor <= 1.0:
        raise argparse.ArgumentTypeError("debe estar en (0, 1]")
    return valor


def build_parser(algoritmo: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"PFSP con algoritmo {algoritmo} (material de clases)"
    )
    parser.add_argument("--semilla", "--seed", dest="semilla", type=_positivo_entero, required=True)
    parser.add_argument(
        "--poblacion", "--pop-size", dest="poblacion", type=_positivo_entero, required=True
    )
    parser.add_argument("--cruza", "--pc", dest="cruza", type=_probabilidad, required=True)
    parser.add_argument(
        "--mutacion", "--pm", "--tau", dest="mutacion", type=_probabilidad, required=True
    )
    parser.add_argument(
        "--iteraciones",
        "--generations",
        dest="iteraciones",
        type=_positivo_entero,
        required=True,
    )
    parser.add_argument("--entrada", "--instance", dest="entrada", required=True)
    parser.add_argument("--salida", "--output", dest="salida", required=True)
    if algoritmo == "memetico":
        parser.add_argument("--ls-freq", type=_positivo_entero, default=1)
        parser.add_argument("--ls-intensity", type=_positivo_entero, default=None)
    return parser


def _escribir_salida(path: Path, lineas: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    texto = "".join(f"{k}={v}\n" for k, v in lineas.items())
    path.write_text(texto, encoding="utf-8")
    sys.stdout.write(texto)


def main(algoritmo: str, argv: list[str] | None = None) -> int:
    args = build_parser(algoritmo).parse_args(argv)
    entrada = Path(args.entrada)
    if not entrada.is_file():
        sys.stderr.write(f"no existe el archivo de entrada: {entrada}\n")
        return 2

    instance = load(entrada)
    common = dict(
        p=instance.p,
        seed=args.semilla,
        pop_size=args.poblacion,
        pc=args.cruza,
        pm=args.mutacion,
        iteraciones=args.iteraciones,
    )
    if algoritmo == "memetico":
        result = run_memetic(
            **common,
            ls_freq=args.ls_freq,
            ls_intensity=args.ls_intensity,
        )
    else:
        result = run_ga(**common)

    gap = rpd(result.cmax, instance.ub)
    perm_txt = " ".join(str(job + 1) for job in result.permutacion)
    lineas = {
        "algoritmo": algoritmo,
        "semilla": str(args.semilla),
        "entrada": str(entrada),
        "poblacion": str(args.poblacion),
        "cruza": str(args.cruza),
        "mutacion": str(args.mutacion),
        "iteraciones": str(args.iteraciones),
        "cmax": str(result.cmax),
        "rpd": "NA" if gap is None else f"{gap:.6f}",
        "evaluaciones": str(result.evaluaciones),
        "permutacion": perm_txt,
    }
    _escribir_salida(Path(args.salida), lineas)
    return 0
