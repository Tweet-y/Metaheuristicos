"""Experimento pareado AG vs Memético: 50 semillas, dos presupuestos, Wilcoxon sobre RPD pooled."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from scipy import stats
from tqdm import tqdm

from pfsp.ga import run as run_ga
from pfsp.instance import load
from pfsp.memetic import run as run_memetic
from pfsp.metrics import rpd

DEFAULT_SIZES = ((20, 5), (50, 10), (100, 10))
POP = 50
PC = 0.8
PM = 0.2
ITER = 200


def list_instances(root: Path, sizes, limit_per_size: int | None) -> list[Path]:
    files: list[Path] = []
    for n, m in sizes:
        batch = sorted(root.glob(f"ins_{n}_{m}_*.txt"))
        if limit_per_size is not None:
            batch = batch[:limit_per_size]
        files.extend(batch)
    return files


def _run_one(kind: str, instance, seed: int, max_evaluations: int | None):
    kwargs = dict(
        p=instance.p,
        seed=seed,
        pop_size=POP,
        pc=PC,
        pm=PM,
        iteraciones=ITER,
        max_evaluations=max_evaluations,
    )
    if kind == "memetico":
        result = run_memetic(**kwargs)
    else:
        result = run_ga(**kwargs)
    gap = rpd(result.cmax, instance.ub)
    return result.cmax, gap, result.evaluaciones


def paired_table(root: Path, sizes, replicas: int, limit_per_size: int | None) -> pd.DataFrame:
    instances = list_instances(root, sizes, limit_per_size)
    rows = []
    seeds = list(range(1, replicas + 1))
    iso_evals = POP * (ITER + 1)
    budgets = (("generaciones", None), ("evaluaciones", iso_evals))
    jobs = [
        (inst, seed, bname, bval)
        for inst in instances
        for seed in seeds
        for bname, bval in budgets
    ]
    for inst_path, seed, bname, bval in tqdm(jobs, desc="corridas pareadas"):
        instance = load(inst_path)
        for kind in ("genetico", "memetico"):
            cmax_val, gap, evals = _run_one(kind, instance, seed, bval)
            rows.append(
                {
                    "instancia": inst_path.name,
                    "n": instance.n,
                    "m": instance.m,
                    "semilla": seed,
                    "presupuesto": bname,
                    "algoritmo": kind,
                    "cmax": cmax_val,
                    "rpd": gap,
                    "evaluaciones": evals,
                    "ub": instance.ub,
                }
            )
    return pd.DataFrame(rows)


def wilcoxon_pooled(df: pd.DataFrame) -> dict:
    wide = df.pivot_table(
        index=["instancia", "semilla", "presupuesto"],
        columns="algoritmo",
        values="rpd",
    ).dropna()
    ga = wide["genetico"].to_numpy()
    ma = wide["memetico"].to_numpy()
    stat, pvalue = stats.wilcoxon(ga, ma, alternative="two-sided")
    return {
        "n_pares": int(len(ga)),
        "estadistico": float(stat),
        "p_value": float(pvalue),
        "mediana_rpd_genetico": float(pd.Series(ga).median()),
        "mediana_rpd_memetico": float(pd.Series(ma).median()),
        "hipotesis": "mediana(RPD_AG - RPD_MA) = 0",
    }


def plot_box(df: pd.DataFrame, out: Path) -> None:
    import seaborn as sns
    from matplotlib import pyplot as plt

    sns.set_theme(style="whitegrid")
    g = sns.catplot(
        data=df.dropna(subset=["rpd"]),
        x="algoritmo",
        y="rpd",
        col="presupuesto",
        kind="box",
        sharey=True,
    )
    g.set_axis_labels("algoritmo", "RPD (%)")
    out.parent.mkdir(parents=True, exist_ok=True)
    g.savefig(out, dpi=120)
    plt.close("all")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Experimento AG vs Memético")
    parser.add_argument("--replicas", type=int, default=50)
    parser.add_argument("--taillards", type=Path, default=Path("taillards"))
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--limit-per-size", type=int, default=None)
    parser.add_argument(
        "--sizes",
        default="20x5,50x10,100x10",
        help="clases n x m separadas por coma",
    )
    args = parser.parse_args(argv)
    sizes = []
    for token in args.sizes.split(","):
        n_s, m_s = token.lower().split("x")
        sizes.append((int(n_s), int(m_s)))

    df = paired_table(args.taillards, sizes, args.replicas, args.limit_per_size)
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "paired_rpd.csv"
    df.to_csv(csv_path, index=False)
    summary = wilcoxon_pooled(df)
    (args.out / "wilcoxon.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    plot_box(df, args.out / "rpd_boxplot.png")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
