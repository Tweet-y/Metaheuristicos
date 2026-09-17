#!/usr/bin/env python3
"""Genera las figuras del informe a partir de los CSV de la batería experimental.

Requiere haber corrido antes `python ejecutar_comparativa.py`.
Uso: python generar_graficos.py
"""

import csv
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ARCHIVO_RESULTADOS = "results/comparativa_ag_vs_memetico.csv"
ARCHIVO_TRAZA = "results/traza_convergencia.csv"
CARPETA_SALIDA = "results/graficos"

TAMANOS = ["Pequeña (20x5)", "Mediana (50x10)", "Grande (100x10)"]
ALGORITMOS = ["AG", "Memetico"]

# Paleta categórica validada para daltonismo (ΔE 24.7 protan, 33.6 visión normal).
# El color va con el algoritmo, nunca con su posición en el ranking.
COLOR = {"AG": "#2a78d6", "Memetico": "#eb6834"}
MARCA = {"AG": "o", "Memetico": "s"}  # la forma duplica la identidad, no solo el color

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
REJILLA = "#e1e0d9"
EJE = "#c3c2b7"

plt.rcParams.update({
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "savefig.facecolor": SUPERFICIE,
    "savefig.bbox": "tight",
    "font.family": "sans-serif",
    "font.size": 9,
    "axes.edgecolor": EJE,
    "axes.linewidth": 0.8,
    "axes.labelcolor": TINTA_SECUNDARIA,
    "axes.titlecolor": TINTA,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": REJILLA,
    "grid.linewidth": 0.7,
    "grid.linestyle": "-",
    "text.color": TINTA,
    "xtick.color": EJE,
    "ytick.color": EJE,
    "xtick.labelcolor": TINTA_SECUNDARIA,
    "ytick.labelcolor": TINTA_SECUNDARIA,
    "legend.frameon": False,
    "legend.fontsize": 9,
})


def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def paneles(titulo, ylabel, xlabel, y_titulo=1.02):
    """Figura de tres paneles, uno por tamaño de instancia (small multiples)."""
    fig, ejes = plt.subplots(1, 3, figsize=(11.5, 3.5))
    fig.suptitle(titulo, fontsize=11, fontweight="bold", color=TINTA, y=y_titulo)
    for eje, tamano in zip(ejes, TAMANOS):
        eje.set_title(tamano, pad=8)
        eje.set_xlabel(xlabel)
    ejes[0].set_ylabel(ylabel)
    return fig, ejes


def leyenda(fig, forma="linea"):
    """Leyenda al pie. Para >= 2 series va siempre, así la identidad no es solo color."""
    if forma == "caja":
        manejadores = [plt.Rectangle((0, 0), 1, 1, facecolor=COLOR[a], edgecolor="none",
                                     label=a) for a in ALGORITMOS]
    else:
        estilo = "none" if forma == "punto" else "-"
        manejadores = [plt.Line2D([], [], color=COLOR[a], marker=MARCA[a], linestyle=estilo,
                                  linewidth=2, markersize=6, markeredgecolor=SUPERFICIE,
                                  markeredgewidth=1.2, label=a) for a in ALGORITMOS]
    fig.legend(handles=manejadores, loc="lower center", ncol=len(ALGORITMOS),
               bbox_to_anchor=(0.5, -0.09))


def guardar(fig, nombre):
    ruta = os.path.join(CARPETA_SALIDA, nombre)
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    print(f"  [OK] {ruta}")


def grafico_secuencia(resultados):
    """Trabajo vs posición en la secuencia, para la mejor solución de cada método."""
    # y_titulo más alto porque cada panel lleva un subtítulo de dos líneas.
    fig, ejes = paneles("Mejor solución encontrada: trabajo asignado a cada posición",
                        "ID del trabajo", "Posición en la secuencia", y_titulo=1.12)

    for eje, tamano in zip(ejes, TAMANOS):
        cmax_por_algoritmo = []
        for algoritmo in ALGORITMOS:
            corridas = [r for r in resultados
                        if r["Tamano_Problema"] == tamano and r["Algoritmo"] == algoritmo]
            if not corridas:
                continue
            mejor = min(corridas, key=lambda r: int(r["Makespan"]))
            secuencia = [int(t) for t in mejor["Mejor_Secuencia"].split("-")]
            tamano_marca = 26 if len(secuencia) <= 20 else (14 if len(secuencia) <= 50 else 7)
            eje.scatter(range(len(secuencia)), secuencia, s=tamano_marca,
                        c=COLOR[algoritmo], marker=MARCA[algoritmo],
                        edgecolors=SUPERFICIE, linewidths=0.8, zorder=3)
            cmax_por_algoritmo.append(f"{algoritmo} {mejor['Makespan']}")
        # El Cmax va en el título y no en una leyenda dentro del panel, que tapaba puntos.
        eje.set_title(f"{tamano}\nCmax: {'  ·  '.join(cmax_por_algoritmo)}", pad=8)

    leyenda(fig, forma="punto")
    guardar(fig, "secuencia_mejor_solucion.png")


def _curva_mejor_hasta_ahora(pares, generaciones):
    """Expande [(gen, makespan), ...] al mejor valor conocido en cada generación."""
    curva = []
    actual = pares[0][1]
    i = 0
    for gen in range(generaciones + 1):
        while i < len(pares) and pares[i][0] == gen:
            actual = pares[i][1]
            i += 1
        curva.append(actual)
    return curva


def grafico_hallazgo(resultados, trazas):
    """Generación en que se halló cada mejora, contra el makespan alcanzado."""
    generaciones = int(resultados[0]["Iteraciones"])
    por_grupo = defaultdict(lambda: defaultdict(list))
    for t in trazas:
        por_grupo[(t["Tamano_Problema"], t["Algoritmo"])][t["Semilla"]].append(
            (int(t["Generacion"]), int(t["Makespan"])))

    cotas = {r["Tamano_Problema"]: int(r["Upper_Bound"]) for r in resultados}

    fig, ejes = paneles("Convergencia: en qué generación se halla cada mejora del makespan",
                        "Makespan (promedio de 10 semillas)", "Generación")

    for eje, tamano in zip(ejes, TAMANOS):
        for algoritmo in ALGORITMOS:
            semillas = por_grupo.get((tamano, algoritmo), {})
            if not semillas:
                continue
            curvas = [_curva_mejor_hasta_ahora(sorted(p), generaciones)
                      for p in semillas.values()]
            promedio = [sum(valores) / len(valores) for valores in zip(*curvas)]
            eje.step(range(generaciones + 1), promedio, where="post",
                     color=COLOR[algoritmo], linewidth=2, zorder=3)

            # Marca solo las generaciones donde de verdad hubo un hallazgo.
            hallazgos = sorted({g for pares in semillas.values() for g, _ in pares})
            eje.scatter(hallazgos, [promedio[g] for g in hallazgos], s=18,
                        c=COLOR[algoritmo], marker=MARCA[algoritmo],
                        edgecolors=SUPERFICIE, linewidths=0.8, zorder=4)

        cota = cotas[tamano]
        eje.axhline(cota, color=TINTA_TENUE, linewidth=1, zorder=2)
        eje.annotate(f"UB {cota}", xy=(generaciones, cota), xytext=(-4, 4),
                     textcoords="offset points", ha="right", va="bottom",
                     fontsize=8, color=TINTA_TENUE)

    leyenda(fig)
    guardar(fig, "generacion_hallazgo.png")


def grafico_tiempo_por_semilla(resultados):
    """Distribución del tiempo de proceso según la semilla."""
    fig, ejes = paneles("Tiempo de proceso por semilla",
                        "Tiempo (segundos)", "Semilla")

    for eje, tamano in zip(ejes, TAMANOS):
        semillas = sorted({int(r["Semilla"]) for r in resultados
                           if r["Tamano_Problema"] == tamano})
        ancho = 0.38
        for desplazamiento, algoritmo in zip((-ancho / 2, ancho / 2), ALGORITMOS):
            tiempos = {int(r["Semilla"]): float(r["Tiempo_Seg"]) for r in resultados
                       if r["Tamano_Problema"] == tamano and r["Algoritmo"] == algoritmo}
            if not tiempos:
                continue
            eje.bar([s + desplazamiento for s in semillas],
                    [tiempos[s] for s in semillas],
                    width=ancho - 0.04, color=COLOR[algoritmo], zorder=3)
        eje.set_xticks(semillas)

    leyenda(fig, forma="caja")
    guardar(fig, "tiempo_por_semilla.png")


def grafico_makespan_por_semilla(resultados):
    """Mejor makespan alcanzado por cada semilla.

    Va como diagrama de puntos y no de barras: los valores están muy juntos, así
    que una barra desde cero no dejaría ver la diferencia, y una barra con el eje
    cortado exageraría visualmente diferencias de décimas.
    """
    fig, ejes = paneles("Mejor makespan por semilla", "Makespan", "Semilla")

    for eje, tamano in zip(ejes, TAMANOS):
        semillas = sorted({int(r["Semilla"]) for r in resultados
                           if r["Tamano_Problema"] == tamano})
        for algoritmo in ALGORITMOS:
            valores = {int(r["Semilla"]): int(r["Makespan"]) for r in resultados
                       if r["Tamano_Problema"] == tamano and r["Algoritmo"] == algoritmo}
            if not valores:
                continue
            # Sin línea que una las semillas: son categorías nominales, unirlas
            # sugeriría una tendencia entre semilla 1 y semilla 2 que no existe.
            eje.plot(semillas, [valores[s] for s in semillas],
                     color=COLOR[algoritmo], marker=MARCA[algoritmo], linestyle="none",
                     markersize=7, markeredgecolor=SUPERFICIE,
                     markeredgewidth=1.2, zorder=3)

        cota = next(int(r["Upper_Bound"]) for r in resultados
                    if r["Tamano_Problema"] == tamano)
        eje.axhline(cota, color=TINTA_TENUE, linewidth=1, zorder=2)
        eje.annotate(f"UB {cota}", xy=(semillas[-1], cota), xytext=(0, 4),
                     textcoords="offset points", ha="right", va="bottom",
                     fontsize=8, color=TINTA_TENUE)
        eje.set_xticks(semillas)

    leyenda(fig, forma="punto")
    guardar(fig, "makespan_por_semilla.png")


def grafico_boxplot_rpd(resultados):
    """Dispersión del RPD por método y tamaño de instancia.

    Va en tres paneles con escala propia y no en un eje único: el RPD del AG en
    50x10 es un orden de magnitud mayor que el resto, y en un solo eje aplastaba
    las cajas del 20x5 hasta volverlas invisibles.
    """
    fig, ejes = paneles("Dispersión del RPD sobre 10 semillas", "RPD (%)", "")

    for eje, tamano in zip(ejes, TAMANOS):
        datos = []
        colores = []
        etiquetas = []
        for algoritmo in ALGORITMOS:
            rpds = [float(r["RPD_%"]) for r in resultados
                    if r["Tamano_Problema"] == tamano and r["Algoritmo"] == algoritmo]
            if not rpds:
                continue
            datos.append(rpds)
            colores.append(COLOR[algoritmo])
            etiquetas.append(algoritmo)

        cajas = eje.boxplot(datos, positions=range(len(datos)), widths=0.45,
                            patch_artist=True,
                            medianprops={"color": SUPERFICIE, "linewidth": 1.6},
                            flierprops={"marker": ".", "markersize": 5,
                                        "markerfacecolor": TINTA_TENUE,
                                        "markeredgecolor": "none"})
        for caja, color in zip(cajas["boxes"], colores):
            caja.set(facecolor=color, edgecolor=color, linewidth=1)
        for parte in ("whiskers", "caps"):
            for linea in cajas[parte]:
                linea.set(color=EJE, linewidth=1)

        eje.set_xticks(range(len(etiquetas)))
        eje.set_xticklabels(etiquetas)
        eje.set_ylim(bottom=min(-0.05, eje.get_ylim()[0]))
        eje.axhline(0, color=TINTA_TENUE, linewidth=1, zorder=2)
        eje.annotate("UB", xy=(len(etiquetas) - 0.5, 0), xytext=(0, 3),
                     textcoords="offset points", ha="right", va="bottom",
                     fontsize=8, color=TINTA_TENUE)

    leyenda(fig, forma="caja")
    guardar(fig, "boxplot_rpd.png")


def main():
    if not os.path.exists(ARCHIVO_RESULTADOS):
        print(f"Falta {ARCHIVO_RESULTADOS}. Ejecuta primero: python ejecutar_comparativa.py")
        return
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    resultados = cargar(ARCHIVO_RESULTADOS)
    trazas = cargar(ARCHIVO_TRAZA)

    print(f"Generando figuras en {CARPETA_SALIDA}/ ...")
    grafico_secuencia(resultados)
    grafico_hallazgo(resultados, trazas)
    grafico_tiempo_por_semilla(resultados)
    grafico_makespan_por_semilla(resultados)
    grafico_boxplot_rpd(resultados)
    print("Listo.")


if __name__ == "__main__":
    main()
