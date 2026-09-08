"""Experimento pareado AG vs Memético: 50 semillas, dos presupuestos, Wilcoxon sobre RPD pooled."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Permitir ejecución directa como script
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from scipy import stats
from tqdm import tqdm

from pfsp.ga import run as run_ga
from pfsp.instance import load
from pfsp.memetic import run as run_memetic
from pfsp.metrics import rpd

DEFAULT_SIZES = ((20, 5), (50, 10), (100, 10))
POP = 30
PC = 0.8
PM = 0.2
ITER = 100
LS_FREQ = 2
LS_INTENSITY = 1


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
        result = run_memetic(**kwargs, ls_freq=LS_FREQ, ls_intensity=LS_INTENSITY)
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


def plot_convergence(histories: list[dict], out: Path) -> None:
    from matplotlib import pyplot as plt
    import numpy as np

    if not histories:
        return

    df_hist = pd.DataFrame(histories)
    # Agrupar por tamaño (n x m) y algoritmo
    fig, axes = plt.subplots(1, len(df_hist["size"].unique()), figsize=(15, 4), sharey=False)
    if len(df_hist["size"].unique()) == 1:
        axes = [axes]

    sizes = sorted(df_hist["size"].unique())
    for ax, sz in zip(axes, sizes):
        sub = df_hist[df_hist["size"] == sz]
        for alg, color, label in [("genetico", "#1f77b4", "Algoritmo Genético"), ("memetico", "#2ca02c", "Algoritmo Memético")]:
            alg_sub = sub[sub["algoritmo"] == alg]
            if alg_sub.empty:
                continue
            # Obtener matrices de curvas
            curvas = list(alg_sub["curva"])
            max_len = max(len(c) for c in curvas)
            # Rellenar con el último valor para alinear
            padded = np.array([c + [c[-1]] * (max_len - len(c)) for c in curvas])
            mean_c = np.mean(padded, axis=0)
            std_c = np.std(padded, axis=0)
            gens = np.arange(max_len)
            ax.plot(gens, mean_c, label=label, color=color, lw=2)
            ax.fill_between(gens, mean_c - std_c, mean_c + std_c, color=color, alpha=0.15)

        ax.set_title(f"Instancias {sz}")
        ax.set_xlabel("Generación")
        ax.set_ylabel("Makespan (Cmax)")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="upper right")

    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=120)
    plt.close("all")


def generate_summary_tables(df: pd.DataFrame, out_dir: Path) -> None:
    # Agrupar por tamaño y presupuesto
    df["size"] = df["n"].astype(str) + "x" + df["m"].astype(str)
    resumen = []

    for (sz, budget), group in df.groupby(["size", "presupuesto"]):
        ga = group[group["algoritmo"] == "genetico"]["rpd"].dropna()
        ma = group[group["algoritmo"] == "memetico"]["rpd"].dropna()

        # Test wilcoxon si hay pares
        try:
            stat, pval = stats.wilcoxon(ga, ma, alternative="two-sided")
        except Exception:
            pval = 1.0

        resumen.append({
            "Tamaño": sz,
            "Presupuesto": budget,
            "AG RPD Prom (%)": f"{ga.mean():.2f} ± {ga.std():.2f}",
            "AG Min RPD (%)": f"{ga.min():.2f}",
            "AM RPD Prom (%)": f"{ma.mean():.2f} ± {ma.std():.2f}",
            "AM Min RPD (%)": f"{ma.min():.2f}",
            "p-valor Wilcoxon": f"{pval:.4e}" if pval < 0.001 else f"{pval:.4f}",
        })

    sum_df = pd.DataFrame(resumen)
    md_path = out_dir / "tabla_resumen.md"
    tex_path = out_dir / "tabla_resumen.tex"

    # Generar Markdown sin requerir paquete externo tabulate
    headers = list(sum_df.columns)
    md_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in sum_df.iterrows():
        md_lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # Generar LaTeX sin requerir jinja2
    tex_lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Comparación de Desempeño AG vs Algoritmo Memético}",
        r"\begin{tabular}{" + "l" * len(headers) + "}",
        r"\hline",
        " & ".join(headers).replace("%", r"\%") + r" \\",
        r"\hline",
    ]
    for _, row in sum_df.iterrows():
        tex_lines.append(" & ".join(str(row[h]).replace("%", r"\%").replace("±", r"$\pm$") for h in headers) + r" \\")
    tex_lines.extend([
        r"\hline",
        r"\end{tabular}",
        r"\end{table}",
    ])
    tex_path.write_text("\n".join(tex_lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Experimento AG vs Memético")
    parser.add_argument("--replicas", type=int, default=50)
    parser.add_argument("--taillards", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--limit-per-size", type=int, default=None)
    parser.add_argument(
        "--sizes",
        default="20x5,50x10,100x10",
        help="clases n x m separadas por coma",
    )
    args = parser.parse_args(argv)

    taillards_dir = args.taillards
    if taillards_dir is None:
        taillards_dir = Path("taillards") if Path("taillards").exists() else Path("data")

    sizes = []
    for token in args.sizes.split(","):
        n_s, m_s = token.lower().split("x")
        sizes.append((int(n_s), int(m_s)))

    # Ejecutar experimentos pareados y registrar historiales
    instances = list_instances(taillards_dir, sizes, args.limit_per_size)
    rows = []
    histories = []
    seeds = list(range(1, args.replicas + 1))
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
        kwargs = dict(
            p=instance.p,
            seed=seed,
            pop_size=POP,
            pc=PC,
            pm=PM,
            iteraciones=ITER,
            max_evaluations=bval,
        )
        for kind in ("genetico", "memetico"):
            if kind == "memetico":
                res = run_memetic(**kwargs, ls_freq=LS_FREQ, ls_intensity=LS_INTENSITY)
            else:
                res = run_ga(**kwargs)

            gap = rpd(res.cmax, instance.ub)
            rows.append({
                "instancia": inst_path.name,
                "n": instance.n,
                "m": instance.m,
                "semilla": seed,
                "presupuesto": bname,
                "algoritmo": kind,
                "cmax": res.cmax,
                "rpd": gap,
                "evaluaciones": res.evaluaciones,
                "ub": instance.ub,
            })
            if bname == "generaciones":
                histories.append({
                    "size": f"{instance.n}x{instance.m}",
                    "instancia": inst_path.name,
                    "algoritmo": kind,
                    "semilla": seed,
                    "curva": res.historial,
                })

    df = pd.DataFrame(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "paired_rpd.csv"
    df.to_csv(csv_path, index=False)

    summary = wilcoxon_pooled(df)
    (args.out / "wilcoxon.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    plot_box(df, args.out / "rpd_boxplot.png")
    plot_convergence(histories, args.out / "convergence_curves.png")
    generate_summary_tables(df, args.out)

    print("\n[OK] Experimentos completados exitosamente.")
    print(f"Resultados guardados en: {args.out}/")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

