"""Pipeline experimental paralelo AG vs Algoritmo Memético con línea base NEH.

Ejecuta corridas pareadas (Common Random Numbers), genera tablas LaTeX/Markdown,
curvas de convergencia promedio, boxplots y tests estadísticos de Wilcoxon por tamaño
con corrección de Holm-Bonferroni.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd
from scipy import stats
from tqdm import tqdm

from pfsp.ga import run as run_ga
from pfsp.instance import load
from pfsp.memetic import run as run_memetic
from pfsp.metrics import rpd as calc_rpd
from pfsp.makespan import cmax
from pfsp.neh import neh

DEFAULT_SIZES = ((20, 5), (50, 10), (100, 10))
POP = 30
PC = 0.8
PM = 0.2
ITER = 100
LS_FREQ = 2
LS_INTENSITY = 3
# Búsqueda local sobre cada descendiente, que es lo que documenta el artículo (§2.4).
# `pfsp.memetic` también admite aplicarla solo al mejor de cada generación
# (target_best=True); se fija aquí de forma explícita para que el experimento no
# dependa del valor por defecto de la biblioteca.
LS_TARGET_BEST = False


def list_instances(root: Path, sizes, limit_per_size: int | None) -> list[Path]:
    files: list[Path] = []
    for n, m in sizes:
        batch = sorted(root.glob(f"ins_{n}_{m}_*.txt"))
        if limit_per_size is not None:
            batch = batch[:limit_per_size]
        files.extend(batch)
    return files


def _worker_run(job_args):
    """Ejecuta las corridas de una celda (instancia, semilla, presupuesto).

    Los tres brazos estocásticos comparten semilla, así que arrancan de la misma
    población inicial: Common Random Numbers, que es lo que legitima el test
    pareado. `seed_perm` llega ya calculada para no repetir NEH en cada réplica.
    """
    inst_path_str, seed, bname, bval, seed_perm = job_args
    inst_path = Path(inst_path_str)
    instance = load(inst_path)
    size = f"{instance.n}x{instance.m}"

    common = dict(
        p=instance.p,
        seed=seed,
        pop_size=POP,
        pc=PC,
        pm=PM,
        iteraciones=ITER,
        max_evaluations=bval,
    )

    rows: list[dict] = []
    histories: list[dict] = []

    def registrar(nombre, resultado, tiempo, guardar_curva):
        rows.append({
            "instancia": inst_path.name,
            "n": instance.n,
            "m": instance.m,
            "size": size,
            "semilla": seed,
            "presupuesto": bname,
            "algoritmo": nombre,
            "cmax": resultado.cmax,
            "rpd": calc_rpd(resultado.cmax, instance.ub),
            "evaluaciones": resultado.evaluaciones,
            "tiempo_seg": tiempo,
            "ub": instance.ub,
        })
        if guardar_curva:
            histories.append({
                "size": size,
                "instancia": inst_path.name,
                "algoritmo": nombre,
                "semilla": seed,
                "curva": resultado.historial,
            })

    # Los AG solo se corren bajo 'generaciones': sin búsqueda local consumen
    # exactamente POP*(ITER+1) evaluaciones, así que el presupuesto iso-eval no
    # los recorta y la corrida sería idéntica.
    if bname == "generaciones":
        t0 = time.time()
        res = run_ga(**common, use_neh=False)
        registrar("ag_aleatorio", res, time.time() - t0, True)

        t0 = time.time()
        res = run_ga(**common, seed_perm=seed_perm)
        registrar("genetico", res, time.time() - t0, True)

    t0 = time.time()
    res = run_memetic(
        **common,
        seed_perm=seed_perm,
        ls_freq=LS_FREQ,
        ls_intensity=LS_INTENSITY,
        target_best=LS_TARGET_BEST,
    )
    registrar("memetico", res, time.time() - t0, bname == "generaciones")

    return rows, histories


def compute_neh_baseline(instances: list[Path]) -> tuple[pd.DataFrame, dict[str, list[int]]]:
    """Línea base determinista de NEH, una vez por instancia.

    Devuelve también las secuencias para sembrar con ellas todas las réplicas sin
    recalcular NEH (en 100x10 cuesta ~2 s, y se usaría en cada corrida).
    """
    rows = []
    secuencias: dict[str, list[int]] = {}
    for inst_path in instances:
        instance = load(inst_path)
        t0 = time.time()
        seq = neh(instance.p)
        t_neh = time.time() - t0
        mk = cmax(seq, instance.p)
        secuencias[str(inst_path)] = seq
        rows.append({
            "instancia": inst_path.name,
            "n": instance.n,
            "m": instance.m,
            "size": f"{instance.n}x{instance.m}",
            "cmax_neh": mk,
            "rpd_neh": calc_rpd(mk, instance.ub),
            "tiempo_seg": t_neh,
            "ub": instance.ub,
        })
    return pd.DataFrame(rows), secuencias


# Comparaciones pareadas de interés: (A, B) contrasta RPD_A - RPD_B.
COMPARACIONES = (
    ("genetico", "memetico"),        # aporte de la búsqueda local
    ("ag_aleatorio", "genetico"),    # aporte del sembrado con NEH
)


def wilcoxon_by_size(df: pd.DataFrame) -> dict:
    """Wilcoxon pareado por tamaño, agregando a una media por instancia.

    Se promedian las réplicas dentro de cada instancia antes de testear: las
    semillas de una misma instancia no son observaciones independientes, así que
    agruparlas todas (n = instancias x semillas) infla el n y el p-valor deja de
    significar nada. Aquí el n del test es el número de instancias del tamaño.
    Holm-Bonferroni corrige por la familia de tests.
    """
    inst_means = (
        df.groupby(["size", "instancia", "presupuesto", "algoritmo"])["rpd"]
        .mean()
        .reset_index()
    )
    pivoted = inst_means.pivot_table(
        index=["size", "instancia", "presupuesto"], columns="algoritmo", values="rpd"
    ).reset_index()

    # Los AG solo corren bajo 'generaciones'; su valor vale igual para la fila
    # 'evaluaciones' porque el tope iso-eval no los recorta.
    for alg in ("genetico", "ag_aleatorio"):
        if alg not in pivoted.columns:
            continue
        fijo = (
            inst_means[inst_means["algoritmo"] == alg]
            .set_index(["size", "instancia"])["rpd"]
            .to_dict()
        )
        pivoted[alg] = [
            fijo.get((s, i), v)
            for s, i, v in zip(pivoted["size"], pivoted["instancia"], pivoted[alg])
        ]

    raw_tests = []
    for a, b in COMPARACIONES:
        if a not in pivoted.columns or b not in pivoted.columns:
            continue
        for (sz, budget), group in pivoted.groupby(["size", "presupuesto"]):
            par = group[[a, b]].dropna()
            if len(par) < 5:
                continue
            x, y = par[a].to_numpy(), par[b].to_numpy()

            if np.allclose(x, y):
                stat, pval = 0.0, 1.0
            else:
                stat, pval = stats.wilcoxon(x, y, alternative="two-sided")

            # r = Z / sqrt(N), aproximando Z desde el p-valor de dos colas.
            z = float(abs(stats.norm.ppf(min(max(pval / 2.0, 1e-12), 0.5))))
            raw_tests.append({
                "comparacion": f"{a} vs {b}",
                "size": sz,
                "presupuesto": budget,
                "n_instancias": int(len(par)),
                "stat": float(stat),
                "p_val_raw": float(pval),
                f"media_rpd_{a}": float(np.mean(x)),
                f"media_rpd_{b}": float(np.mean(y)),
                "mediana_diferencia_RPD": float(np.median(x - y)),
                "effect_size_r": float(z / np.sqrt(len(par))),
            })

    # Holm-Bonferroni sobre toda la familia de tests
    raw_tests.sort(key=lambda t: t["p_val_raw"])
    m_tests = len(raw_tests)
    p_previo = 0.0
    for i, t in enumerate(raw_tests):
        p_previo = max(p_previo, min(1.0, t["p_val_raw"] * (m_tests - i)))
        t["p_val_holm"] = p_previo
        t["significativo_alpha_005"] = bool(p_previo < 0.05)

    return {"alpha": 0.05, "correccion": "holm-bonferroni", "tests": raw_tests}


ETIQUETAS = {
    "ag_aleatorio": "AG (inicio aleatorio)",
    "genetico": "AG (sembrado NEH)",
    "memetico": "AM (sembrado NEH)",
}

# Orden de presentación: de menor a mayor esfuerzo, no alfabético.
ORDEN_METODOS = [
    "AG (inicio aleatorio)",
    "AG (sembrado NEH)",
    "AM (sembrado NEH)\n[evaluaciones]",
    "AM (sembrado NEH)\n[generaciones]",
]


def _por_tamano(sizes) -> list[str]:
    """Ordena '20x5' < '50x10' < '100x10' por número de trabajos, no alfabéticamente."""
    return sorted(sizes, key=lambda s: tuple(int(x) for x in s.split("x")))


def generate_summary_tables(df: pd.DataFrame, df_neh: pd.DataFrame, out_dir: Path) -> None:
    """Una fila por (tamaño, presupuesto): NEH y los tres brazos estocásticos."""
    neh_map = df_neh.groupby("size")["rpd_neh"].mean().to_dict()
    # Los AG solo existen bajo 'generaciones'; se repiten en ambas filas porque el
    # presupuesto iso-evaluaciones no los recorta (ver _worker_run).
    fijos = {
        alg: grupo.groupby("size")["rpd"].agg(["mean", "std", "min"]).to_dict("index")
        for alg, grupo in df[df["algoritmo"] != "memetico"].groupby("algoritmo")
    }

    resumen = []
    for (sz, budget), group in df[df["algoritmo"] == "memetico"].groupby(["size", "presupuesto"]):
        fila = {
            "Tamaño": sz,
            "Presupuesto": budget,
            "NEH RPD (%)": f"{neh_map.get(sz, float('nan')):.2f}",
        }
        for alg in ("ag_aleatorio", "genetico"):
            info = fijos.get(alg, {}).get(sz)
            fila[f"{ETIQUETAS[alg]} RPD (%)"] = (
                "NA" if info is None else f"{info['mean']:.2f} ± {info['std']:.2f}"
            )
        fila[f"{ETIQUETAS['memetico']} RPD (%)"] = (
            f"{group['rpd'].mean():.2f} ± {group['rpd'].std():.2f}"
        )
        fila["AM Min RPD (%)"] = f"{group['rpd'].min():.2f}"
        fila["AM Tiempo (s)"] = f"{group['tiempo_seg'].mean():.2f}"
        resumen.append(fila)

    sum_df = pd.DataFrame(resumen)
    md_path = out_dir / "tabla_resumen.md"
    tex_path = out_dir / "tabla_resumen.tex"

    headers = list(sum_df.columns)
    md_lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in sum_df.iterrows():
        md_lines.append("| " + " | ".join(str(row[h]) for h in headers) + " |")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    tex_lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Comparación de Desempeño: NEH, Algoritmo Genético y Algoritmo Memético}",
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


def plot_convergence(histories: list[dict], out: Path, ubs: dict[str, int]) -> None:
    """Convergencia media en RPD, no en Cmax crudo.

    Promediar Cmax entre instancias distintas de un mismo tamaño mezcla escalas
    (una instancia de 100x10 puede rondar 5800 y otra 6300), de modo que la banda
    de dispersión terminaría midiendo la diferencia entre instancias en vez de la
    variabilidad del algoritmo. Normalizar cada curva por el UB de su instancia
    deja las tres curvas y los tres paneles en la misma escala.
    """
    from matplotlib import pyplot as plt
    if not histories:
        return

    df_hist = pd.DataFrame(histories)
    sizes = _por_tamano(df_hist["size"].unique())
    fig, axes = plt.subplots(
        1, len(sizes), figsize=(5 * len(sizes), 4), squeeze=False, sharey=False
    )

    for ax, sz in zip(axes[0], sizes):
        sub = df_hist[df_hist["size"] == sz]
        for alg, color in [
            ("ag_aleatorio", "#d62728"),
            ("genetico", "#1f77b4"),
            ("memetico", "#2ca02c"),
        ]:
            alg_sub = sub[sub["algoritmo"] == alg]
            if alg_sub.empty:
                continue
            curvas = []
            for _, fila in alg_sub.iterrows():
                ub = ubs.get(fila["instancia"])
                if not ub:
                    continue
                curvas.append([100.0 * (c - ub) / ub for c in fila["curva"]])
            if not curvas:
                continue
            largo = max(len(c) for c in curvas)
            padded = np.array([c + [c[-1]] * (largo - len(c)) for c in curvas])
            media = np.mean(padded, axis=0)
            desv = np.std(padded, axis=0)
            gens = np.arange(largo)
            ax.plot(gens, media, label=ETIQUETAS[alg], color=color, lw=2)
            ax.fill_between(gens, media - desv, media + desv, color=color, alpha=0.15)

        ax.set_title(f"Instancias {sz}")
        ax.set_xlabel("Generación")
        ax.set_ylabel("RPD medio (%)")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="upper right")

    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=120)
    plt.close("all")


def plot_box(df: pd.DataFrame, df_neh: pd.DataFrame, out: Path) -> None:
    """Un panel por tamaño; los tres brazos estocásticos y la línea base NEH."""
    import seaborn as sns
    from matplotlib import pyplot as plt

    sns.set_theme(style="whitegrid")
    df_plot = df.dropna(subset=["rpd"]).copy()
    # El memético aparece con sus dos presupuestos como categorías distintas.
    df_plot["metodo"] = df_plot.apply(
        lambda r: ETIQUETAS[r["algoritmo"]]
        + (f"\n[{r['presupuesto']}]" if r["algoritmo"] == "memetico" else ""),
        axis=1,
    )
    df_plot = df_plot.drop_duplicates(
        subset=["instancia", "semilla", "metodo"]
    )

    sizes = _por_tamano(df_plot["size"].unique())
    orden = [m for m in ORDEN_METODOS if m in set(df_plot["metodo"])]
    fig, axes = plt.subplots(1, len(sizes), figsize=(5.5 * len(sizes), 4.5), squeeze=False)
    for ax, sz in zip(axes[0], sizes):
        sub = df_plot[df_plot["size"] == sz]
        sns.boxplot(
            data=sub, x="metodo", y="rpd", ax=ax, order=orden,
            hue="metodo", hue_order=orden, legend=False,
        )
        neh_rpd = df_neh[df_neh["size"] == sz]["rpd_neh"].mean()
        ax.axhline(neh_rpd, color="crimson", ls="--", lw=1.5, label=f"NEH ({neh_rpd:.2f} %)")
        ax.set_title(f"Instancias {sz}")
        ax.set_xlabel("")
        ax.set_ylabel("RPD (%)")
        ax.tick_params(axis="x", labelsize=8)
        ax.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=120)
    plt.close("all")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Experimento AG vs Memético con Baseline NEH")
    # 15 réplicas: el test agrega a una media por instancia, así que las semillas
    # solo reducen ruido dentro de la celda; el n del Wilcoxon son las instancias.
    parser.add_argument("--replicas", type=int, default=15)
    parser.add_argument("--taillards", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path("results"))
    parser.add_argument("--limit-per-size", type=int, default=None)
    parser.add_argument(
        "--sizes",
        default="20x5,50x10,100x10",
        help="clases n x m separadas por coma",
    )
    parser.add_argument("--workers", type=int, default=None, help="número de procesos worker (default: cpu_count)")
    args = parser.parse_args(argv)

    taillards_dir = args.taillards
    if taillards_dir is None:
        taillards_dir = Path("taillards") if Path("taillards").exists() else Path("data")

    sizes = []
    for token in args.sizes.split(","):
        n_s, m_s = token.lower().split("x")
        sizes.append((int(n_s), int(m_s)))

    instances = list_instances(taillards_dir, sizes, args.limit_per_size)
    args.out.mkdir(parents=True, exist_ok=True)

    print(f"Calculando línea base NEH para {len(instances)} instancias...")
    df_neh, neh_seqs = compute_neh_baseline(instances)
    df_neh.to_csv(args.out / "neh_baseline.csv", index=False)

    iso_evals = POP * (ITER + 1)
    budgets = (("generaciones", None), ("evaluaciones", iso_evals))
    seeds = list(range(1, args.replicas + 1))

    jobs = [
        (str(inst), seed, bname, bval, neh_seqs[str(inst)])
        for inst in instances
        for seed in seeds
        for bname, bval in budgets
    ]

    n_workers = args.workers or max(1, os.cpu_count() or 4)
    print(f"Lanzando {len(jobs)} tareas pareadas en paralelo con {n_workers} workers...")

    all_rows = []
    all_histories = []

    with mp.Pool(processes=n_workers) as pool:
        for rows, histories in tqdm(pool.imap_unordered(_worker_run, jobs), total=len(jobs), desc="corridas"):
            all_rows.extend(rows)
            all_histories.extend(histories)

    df = pd.DataFrame(all_rows)
    df["size"] = df["n"].astype(str) + "x" + df["m"].astype(str)
    csv_path = args.out / "paired_rpd.csv"
    df.to_csv(csv_path, index=False)

    # Wilcoxon riguroso por tamaño con corrección de Holm
    wilcoxon_results = wilcoxon_by_size(df)
    (args.out / "wilcoxon.json").write_text(
        json.dumps(wilcoxon_results, indent=2), encoding="utf-8"
    )

    plot_box(df, df_neh, args.out / "rpd_boxplot.png")
    plot_convergence(
        all_histories,
        args.out / "convergence_curves.png",
        ubs=df_neh.set_index("instancia")["ub"].to_dict(),
    )
    generate_summary_tables(df, df_neh, args.out)

    print("\n[OK] Pipeline experimental completado.")
    print(f"Resultados guardados en: {args.out}/")
    print(json.dumps(wilcoxon_results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
