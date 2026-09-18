#!/usr/bin/env python3
"""Genera las figuras del informe a partir de los CSV de la batería experimental.

Cada métrica se dibuja con una función `dibujar_*` que recibe un eje ya creado.
Eso permite emitir la misma métrica como figura suelta (tres paneles, uno por
tamaño de instancia) y como fila de la figura resumen, sin duplicar el código.

Requiere haber corrido antes `python ejecutar_comparativa.py`.
Uso: python generar_graficos.py
"""

import csv
import os
import statistics
from collections import Counter, defaultdict, namedtuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.transforms as transforms  # noqa: E402

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


# --------------------------------------------------------------------------
# Datos
# --------------------------------------------------------------------------

def cargar(ruta):
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def corridas_de(resultados, tamano, algoritmo):
    return [r for r in resultados
            if r["Tamano_Problema"] == tamano and r["Algoritmo"] == algoritmo]


def cota_de(resultados, tamano):
    return next(int(r["Upper_Bound"]) for r in resultados
                if r["Tamano_Problema"] == tamano)


def semillas_de(resultados, tamano):
    return sorted({int(r["Semilla"]) for r in resultados
                   if r["Tamano_Problema"] == tamano})


def linea_cota(eje, valor, etiqueta):
    """Referencia horizontal del mejor valor conocido.

    La etiqueta se ancla al borde derecho del panel (x en fracción del eje, y en
    unidades de los datos), no a una coordenada de datos: así no se mete entre
    las marcas por muy distinto que sea el rango de cada panel.
    """
    eje.axhline(valor, color=TINTA_TENUE, linewidth=1, zorder=2)
    transformacion = transforms.blended_transform_factory(eje.transAxes, eje.transData)
    eje.annotate(etiqueta, xy=(0.99, valor), xycoords=transformacion,
                 xytext=(0, 3), textcoords="offset points", ha="right", va="bottom",
                 fontsize=8, color=TINTA_TENUE)


# --------------------------------------------------------------------------
# Una función por métrica: dibuja un panel (un tamaño de instancia)
# --------------------------------------------------------------------------

def dibujar_secuencia(eje, tamano, datos):
    """Trabajo asignado a cada posición, en la mejor solución de cada método."""
    resultados = datos["resultados"]
    cmax = []
    for algoritmo in ALGORITMOS:
        corridas = corridas_de(resultados, tamano, algoritmo)
        if not corridas:
            continue
        mejor = min(corridas, key=lambda r: int(r["Makespan"]))
        secuencia = [int(t) for t in mejor["Mejor_Secuencia"].split("-")]
        marca = 26 if len(secuencia) <= 20 else (14 if len(secuencia) <= 50 else 7)
        eje.scatter(range(len(secuencia)), secuencia, s=marca, c=COLOR[algoritmo],
                    marker=MARCA[algoritmo], edgecolors=SUPERFICIE, linewidths=0.8,
                    zorder=3)
        cmax.append(f"{algoritmo} {mejor['Makespan']}")
    return "Cmax: " + "  ·  ".join(cmax)


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


def dibujar_hallazgo(eje, tamano, datos):
    """Generación en que se halló cada mejora, contra el makespan alcanzado."""
    generaciones = datos["generaciones"]
    for algoritmo in ALGORITMOS:
        semillas = datos["trazas"].get((tamano, algoritmo), {})
        if not semillas:
            continue
        curvas = [_curva_mejor_hasta_ahora(sorted(p), generaciones)
                  for p in semillas.values()]
        promedio = [sum(v) / len(v) for v in zip(*curvas)]
        eje.step(range(generaciones + 1), promedio, where="post",
                 color=COLOR[algoritmo], linewidth=2, zorder=3)
        hallazgos = sorted({g for pares in semillas.values() for g, _ in pares})
        eje.scatter(hallazgos, [promedio[g] for g in hallazgos], s=18,
                    c=COLOR[algoritmo], marker=MARCA[algoritmo],
                    edgecolors=SUPERFICIE, linewidths=0.8, zorder=4)

    cota = cota_de(datos["resultados"], tamano)
    linea_cota(eje, cota, f"UB {cota}")
    return None


def dibujar_tiempo(eje, tamano, datos):
    """Tiempo de proceso de cada semilla."""
    resultados = datos["resultados"]
    semillas = semillas_de(resultados, tamano)
    ancho = 0.38
    for desplazamiento, algoritmo in zip((-ancho / 2, ancho / 2), ALGORITMOS):
        tiempos = {int(r["Semilla"]): float(r["Tiempo_Seg"])
                   for r in corridas_de(resultados, tamano, algoritmo)}
        if not tiempos:
            continue
        eje.bar([s + desplazamiento for s in semillas], [tiempos[s] for s in semillas],
                width=ancho - 0.04, color=COLOR[algoritmo], zorder=3)
    eje.set_xticks(semillas)
    return None


def dibujar_makespan(eje, tamano, datos):
    """Mejor makespan alcanzado por cada semilla.

    Diagrama de puntos y no de barras: los valores están muy juntos, una barra
    desde cero no dejaría ver la diferencia y una con el eje cortado exageraría
    décimas. Tampoco se unen los puntos: las semillas son categorías nominales.
    """
    resultados = datos["resultados"]
    semillas = semillas_de(resultados, tamano)
    for algoritmo in ALGORITMOS:
        valores = {int(r["Semilla"]): int(r["Makespan"])
                   for r in corridas_de(resultados, tamano, algoritmo)}
        if not valores:
            continue
        eje.plot(semillas, [valores[s] for s in semillas], color=COLOR[algoritmo],
                 marker=MARCA[algoritmo], linestyle="none", markersize=7,
                 markeredgecolor=SUPERFICIE, markeredgewidth=1.2, zorder=3)
    cota = cota_de(resultados, tamano)
    linea_cota(eje, cota, f"UB {cota}")
    eje.set_xticks(semillas)
    return None


def _apilar_empates(valores, centro, paso=0.042):
    """Reparte los puntos de igual valor a los lados del centro de la categoría.

    Sin azar: el desplazamiento depende solo de cuántos empates hay y del orden.
    Hace falta porque con 10 semillas hay muchos valores repetidos y, sin
    separarlos, nueve puntos se dibujarian uno encima de otro y pareceria uno.
    """
    conteo = Counter(valores)
    vistos = Counter()
    posiciones = []
    for valor in valores:
        indice = vistos[valor]
        vistos[valor] += 1
        posiciones.append(centro + (indice - (conteo[valor] - 1) / 2) * paso)
    return posiciones


def dibujar_distribucion(eje, tamano, datos):
    """RPD de cada semilla, con la media y la desviación estándar.

    Reemplaza al diagrama de cajas: con 10 semillas y muchos empates, en varios
    grupos el percentil 25 y el 75 coinciden, la caja queda sin altura ni
    bigotes y las semillas restantes aparecen marcadas como atípicas. Mostrar
    las 10 observaciones evita ese artefacto y deja leer las dos cosas que
    importan: qué tan abajo está la nube (cercanía al UB) y qué tan apretada
    está (consistencia entre semillas).
    """
    resultados = datos["resultados"]
    etiquetas = []
    for centro, algoritmo in enumerate(ALGORITMOS):
        rpds = sorted(float(r["RPD_%"])
                      for r in corridas_de(resultados, tamano, algoritmo))
        if not rpds:
            etiquetas.append(algoritmo)
            continue
        media = statistics.mean(rpds)
        desviacion = statistics.stdev(rpds) if len(rpds) > 1 else 0.0

        # Desviación estándar como barra vertical, detrás de los puntos.
        eje.plot([centro, centro], [media - desviacion, media + desviacion],
                 color=EJE, linewidth=1.4, zorder=2, solid_capstyle="round")
        eje.plot(_apilar_empates(rpds, centro), rpds, color=COLOR[algoritmo],
                 marker=MARCA[algoritmo], linestyle="none", markersize=6,
                 markeredgecolor=SUPERFICIE, markeredgewidth=1.0, zorder=3)
        # Media como trazo horizontal ancho.
        eje.plot([centro - 0.2, centro + 0.2], [media, media], color=TINTA,
                 linewidth=1.6, zorder=4)
        # Los valores van en el rotulo del eje y no como anotacion flotante:
        # dentro del panel chocaban con la nube de puntos.
        etiquetas.append(f"{algoritmo}\nmedia {media:.2f}%\nsd {desviacion:.2f}")

    eje.set_xticks(range(len(ALGORITMOS)))
    eje.set_xticklabels(etiquetas)
    eje.set_xlim(-0.6, len(ALGORITMOS) - 0.4)
    eje.set_ylim(bottom=min(-0.08, eje.get_ylim()[0]))
    linea_cota(eje, 0, "UB (RPD 0%)")
    return None


# --------------------------------------------------------------------------
# Composición de figuras
# --------------------------------------------------------------------------

Metrica = namedtuple(
    "Metrica", "nombre titulo fila ylabel xlabel dibujar leyenda en_resumen")

METRICAS = [
    Metrica("secuencia_mejor_solucion",
            "Mejor solución encontrada: trabajo asignado a cada posición",
            "Secuencia", "ID del trabajo", "Posición en la secuencia",
            dibujar_secuencia, "punto", True),
    Metrica("generacion_hallazgo",
            "Convergencia: en qué generación se halla cada mejora del makespan",
            "Convergencia", "Makespan (promedio)", "Generación",
            dibujar_hallazgo, "linea", True),
    Metrica("makespan_por_semilla",
            "Mejor makespan por semilla",
            "Calidad por semilla", "Makespan", "Semilla",
            dibujar_makespan, "punto", True),
    Metrica("tiempo_por_semilla",
            "Tiempo de proceso por semilla",
            "Costo por semilla", "Tiempo (segundos)", "Semilla",
            dibujar_tiempo, "caja", True),
    # Fuera del resumen: se lee mejor sola, y es la figura que responde cuál
    # metodo es a la vez mas consistente y mas cercano al UB.
    Metrica("distribucion_rpd",
            "Distribución del RPD: cercanía al UB y consistencia entre semillas",
            "Dispersión", "RPD (%)", "",
            dibujar_distribucion, "punto", False),
]


def leyenda(fig, forma, y=-0.09):
    """Leyenda al pie. Con dos series va siempre, así la identidad no es solo color."""
    if forma == "caja":
        manejadores = [plt.Rectangle((0, 0), 1, 1, facecolor=COLOR[a], edgecolor="none",
                                     label=a) for a in ALGORITMOS]
    else:
        estilo = "none" if forma == "punto" else "-"
        manejadores = [plt.Line2D([], [], color=COLOR[a], marker=MARCA[a],
                                  linestyle=estilo, linewidth=2, markersize=6,
                                  markeredgecolor=SUPERFICIE, markeredgewidth=1.2,
                                  label=a) for a in ALGORITMOS]
    fig.legend(handles=manejadores, loc="lower center", ncol=len(ALGORITMOS),
               bbox_to_anchor=(0.5, y))


def guardar(fig, nombre):
    ruta = os.path.join(CARPETA_SALIDA, nombre)
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    print(f"  [OK] {ruta}")


def figura_individual(metrica, datos):
    """Una métrica en tres paneles, uno por tamaño de instancia."""
    fig, ejes = plt.subplots(1, 3, figsize=(11.5, 3.6), layout="constrained")
    fig.suptitle(metrica.titulo, fontsize=11, fontweight="bold", color=TINTA)

    for eje, tamano in zip(ejes, TAMANOS):
        subtitulo = metrica.dibujar(eje, tamano, datos)
        eje.set_title(f"{tamano}\n{subtitulo}" if subtitulo else tamano, pad=8)
        eje.set_xlabel(metrica.xlabel)
    ejes[0].set_ylabel(metrica.ylabel)

    leyenda(fig, metrica.leyenda)
    guardar(fig, f"{metrica.nombre}.png")


def figura_resumen(datos):
    """Todas las métricas en una grilla: una fila por métrica, una columna por tamaño.

    El tamaño de instancia rotula la columna una sola vez, en la fila de arriba;
    la métrica rotula la fila desde el eje y de la primera columna. Así ninguna
    etiqueta se repite doce veces.
    """
    metricas = [m for m in METRICAS if m.en_resumen]
    fig, ejes = plt.subplots(len(metricas), 3, figsize=(11.5, 3.0 * len(metricas)),
                             layout="constrained")
    fig.suptitle("Resumen experimental: Algoritmo Genético vs Algoritmo Memético",
                 fontsize=12, fontweight="bold", color=TINTA)

    for fila, metrica in zip(ejes, metricas):
        for eje, tamano in zip(fila, TAMANOS):
            metrica.dibujar(eje, tamano, datos)
            eje.set_xlabel(metrica.xlabel)
        fila[0].set_ylabel(f"{metrica.fila}\n{metrica.ylabel}")

    for eje, tamano in zip(ejes[0], TAMANOS):
        eje.set_title(tamano, pad=8, fontsize=11)

    leyenda(fig, "punto", y=-0.028)
    guardar(fig, "resumen.png")


def main():
    if not os.path.exists(ARCHIVO_RESULTADOS):
        print(f"Falta {ARCHIVO_RESULTADOS}. Ejecuta primero: python ejecutar_comparativa.py")
        return
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    resultados = cargar(ARCHIVO_RESULTADOS)
    trazas = defaultdict(lambda: defaultdict(list))
    for t in cargar(ARCHIVO_TRAZA):
        trazas[(t["Tamano_Problema"], t["Algoritmo"])][t["Semilla"]].append(
            (int(t["Generacion"]), int(t["Makespan"])))

    datos = {
        "resultados": resultados,
        "trazas": trazas,
        "generaciones": int(resultados[0]["Iteraciones"]),
    }

    print(f"Generando figuras en {CARPETA_SALIDA}/ ...")
    for metrica in METRICAS:
        figura_individual(metrica, datos)
    figura_resumen(datos)
    print("Listo.")


if __name__ == "__main__":
    main()
