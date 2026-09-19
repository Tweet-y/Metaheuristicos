#!/usr/bin/env python3
"""Genera las figuras del informe a partir de los CSV de la batería experimental.

Cada métrica se dibuja con una función `dibujar_*` que recibe un eje ya creado
y el algoritmo a graficar. Emite figuras individuales por algoritmo y una figura
resumen en columna para cada algoritmo.

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

TAMANO = "Mediana (50x10)"
ALGORITMOS = ["AG", "Memetico"]

# El CSV guarda el identificador sin tilde; las figuras del informe la llevan.
NOMBRE = {"AG": "AG", "Memetico": "Memético"}

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


def corridas_de(resultados, algoritmo):
    return [r for r in resultados
            if r["Tamano_Problema"] == TAMANO and r["Algoritmo"] == algoritmo]


def cota_de(resultados):
    return next(int(r["Upper_Bound"]) for r in resultados
                if r["Tamano_Problema"] == TAMANO)


def semillas_de(resultados, algoritmo):
    return sorted({int(r["Semilla"]) for r in corridas_de(resultados, algoritmo)})


def linea_cota(eje, valor, etiqueta):
    """Referencia horizontal del mejor valor conocido.

    La etiqueta se ancla al borde derecho del panel (x en fracción del eje, y en
    unidades de los datos), no a una coordenada de datos.
    """
    eje.axhline(valor, color=TINTA_TENUE, linewidth=1, zorder=2)
    transformacion = transforms.blended_transform_factory(eje.transAxes, eje.transData)
    eje.annotate(etiqueta, xy=(0.99, valor), xycoords=transformacion,
                 xytext=(0, 3), textcoords="offset points", ha="right", va="bottom",
                 fontsize=8, color=TINTA_TENUE)


def _configurar_xticks_semillas(eje, semillas):
    """Rotula cada 5 semillas para evitar colisión de etiquetas con 30 marcas."""
    eje.set_xticks(semillas)
    etiquetas = [str(s) if s == 1 or s % 5 == 0 else "" for s in semillas]
    eje.set_xticklabels(etiquetas)


# --------------------------------------------------------------------------
# Métricas por algoritmo
# --------------------------------------------------------------------------

def dibujar_secuencia(eje, algoritmo, datos):
    """Trabajo asignado a cada posición, en la mejor solución del método."""
    corridas = corridas_de(datos["resultados"], algoritmo)
    if not corridas:
        return None
    mejor = min(corridas, key=lambda r: int(r["Makespan"]))
    secuencia = [int(t) for t in mejor["Mejor_Secuencia"].split("-")]
    marca = 26 if len(secuencia) <= 20 else (14 if len(secuencia) <= 50 else 7)
    eje.scatter(range(len(secuencia)), secuencia, s=marca, c=COLOR[algoritmo],
                marker=MARCA[algoritmo], edgecolors=SUPERFICIE, linewidths=0.8,
                zorder=3)
    return f"Cmax: {mejor['Makespan']}"


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


def dibujar_hallazgo(eje, algoritmo, datos):
    """Generación en que se halló cada mejora, contra el makespan alcanzado."""
    generaciones = datos["generaciones"]
    semillas = datos["trazas"].get((TAMANO, algoritmo), {})
    if not semillas:
        return None
    curvas = [_curva_mejor_hasta_ahora(sorted(p), generaciones)
              for p in semillas.values()]
    promedio = [sum(v) / len(v) for v in zip(*curvas)]
    eje.step(range(generaciones + 1), promedio, where="post",
             color=COLOR[algoritmo], linewidth=2, zorder=3)
    hallazgos = sorted({g for pares in semillas.values() for g, _ in pares})
    eje.scatter(hallazgos, [promedio[g] for g in hallazgos], s=18,
                c=COLOR[algoritmo], marker=MARCA[algoritmo],
                edgecolors=SUPERFICIE, linewidths=0.8, zorder=4)

    cota = cota_de(datos["resultados"])
    linea_cota(eje, cota, f"UB {cota}")
    return None


def dibujar_tiempo(eje, algoritmo, datos):
    """Tiempo de proceso de cada semilla."""
    resultados = datos["resultados"]
    semillas = semillas_de(resultados, algoritmo)
    tiempos = {int(r["Semilla"]): float(r["Tiempo_Seg"])
               for r in corridas_de(resultados, algoritmo)}
    if not tiempos:
        return None
    ancho = 0.6
    eje.bar(semillas, [tiempos[s] for s in semillas],
            width=ancho, color=COLOR[algoritmo], zorder=3)
    _configurar_xticks_semillas(eje, semillas)
    return None


def dibujar_makespan(eje, algoritmo, datos):
    """Mejor makespan alcanzado por cada semilla."""
    resultados = datos["resultados"]
    semillas = semillas_de(resultados, algoritmo)
    valores = {int(r["Semilla"]): int(r["Makespan"])
               for r in corridas_de(resultados, algoritmo)}
    if not valores:
        return None
    eje.plot(semillas, [valores[s] for s in semillas], color=COLOR[algoritmo],
             marker=MARCA[algoritmo], linestyle="none", markersize=7,
             markeredgecolor=SUPERFICIE, markeredgewidth=1.2, zorder=3)
    cota = cota_de(resultados)
    linea_cota(eje, cota, f"UB {cota}")
    _configurar_xticks_semillas(eje, semillas)
    return None


def _apilar_empates(valores, centro=0, ancho_max=0.24):
    """Reparte los puntos de igual valor a los lados del centro de la categoría.

    Sin azar: el desplazamiento depende solo de cuántos empates hay y del orden.
    El paso se escala por el máximo de empates y además tiene tope: con 30
    semillas hay pilas de hasta doce puntos y, repartidas sobre todo el ancho de
    la caja, dejan de leerse como observaciones y parecen una línea punteada.
    """
    conteo = Counter(valores)
    max_empates = max(conteo.values()) if conteo else 1
    paso = min(0.022, ancho_max / max(max_empates, 1))
    vistos = Counter()
    posiciones = []
    for valor in valores:
        indice = vistos[valor]
        vistos[valor] += 1
        posiciones.append(centro + (indice - (conteo[valor] - 1) / 2) * paso)
    return posiciones


def dibujar_distribucion(eje, algoritmo, datos):
    """RPD de cada semilla con diagrama de caja y las 30 observaciones superpuestas."""
    corridas = corridas_de(datos["resultados"], algoritmo)
    if not corridas:
        return None
    rpds = sorted(float(r["RPD_%"]) for r in corridas)
    media = statistics.mean(rpds)
    desviacion = statistics.stdev(rpds) if len(rpds) > 1 else 0.0

    # Diagrama de caja sin outliers automáticos (mostramos todas las observaciones)
    props_caja = dict(
        boxprops=dict(facecolor=SUPERFICIE, edgecolor=COLOR[algoritmo], linewidth=1.2),
        medianprops=dict(color=TINTA, linewidth=1.6),
        whiskerprops=dict(color=TINTA_SECUNDARIA, linewidth=1.0),
        capprops=dict(color=TINTA_SECUNDARIA, linewidth=1.0),
    )
    eje.boxplot(rpds, positions=[0], widths=0.45, patch_artist=True,
                showfliers=False, **props_caja)

    # 30 puntos apilados
    pos_x = _apilar_empates(rpds, centro=0)
    eje.plot(pos_x, rpds, color=COLOR[algoritmo],
             marker=MARCA[algoritmo], linestyle="none", markersize=6,
             markeredgecolor=SUPERFICIE, markeredgewidth=1.0, zorder=4)

    eje.set_xticks([0])
    eje.set_xticklabels([f"{NOMBRE[algoritmo]}\nmedia {media:.2f}%\nsd {desviacion:.2f}"])
    eje.set_xlim(-0.5, 0.5)
    # El eje se ajusta a los datos: forzar el 0 comprime la caja contra el borde
    # cuando el método está lejos del UB, y la dispersión entre semillas —que es
    # lo que esta figura existe para mostrar— deja de verse. La referencia se
    # dibuja solo si el 0 cae dentro del rango; si no, el eje "RPD (%)" ya dice
    # que el cero es el UB.
    if eje.get_ylim()[0] <= 0:
        linea_cota(eje, 0, "UB (RPD 0%)")
    return None


# --------------------------------------------------------------------------
# Composición de figuras
# --------------------------------------------------------------------------

Metrica = namedtuple(
    "Metrica", "nombre titulo fila ylabel xlabel dibujar en_resumen")

METRICAS = [
    Metrica("secuencia_mejor_solucion",
            "Mejor solución encontrada: trabajo asignado a cada posición",
            "Secuencia", "ID del trabajo", "Posición en la secuencia",
            dibujar_secuencia, True),
    Metrica("generacion_hallazgo",
            "Convergencia: en qué generación se halla cada mejora del makespan",
            "Convergencia", "Makespan (promedio)", "Generación",
            dibujar_hallazgo, True),
    Metrica("makespan_por_semilla",
            "Mejor makespan por semilla",
            "Calidad por semilla", "Makespan", "Semilla",
            dibujar_makespan, True),
    Metrica("tiempo_por_semilla",
            "Tiempo de proceso por semilla",
            "Costo por semilla", "Tiempo (segundos)", "Semilla",
            dibujar_tiempo, True),
    Metrica("distribucion_rpd",
            "Distribución del RPD: cercanía al UB y consistencia entre semillas",
            "Dispersión", "RPD (%)", "",
            dibujar_distribucion, False),
]


def guardar(fig, nombre):
    ruta = os.path.join(CARPETA_SALIDA, nombre)
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    print(f"  [OK] {ruta}")


def figura_individual(metrica, algoritmo, datos):
    """Una métrica en un solo eje para un algoritmo."""
    fig, eje = plt.subplots(1, 1, figsize=(6.0, 3.8), layout="constrained")
    subtitulo = metrica.dibujar(eje, algoritmo, datos)
    titulo = f"{metrica.titulo} — {NOMBRE[algoritmo]}"
    if subtitulo:
        titulo += f" ({subtitulo})"
    eje.set_title(titulo, pad=8)
    eje.set_xlabel(metrica.xlabel)
    eje.set_ylabel(metrica.ylabel)

    slug = algoritmo.lower()
    guardar(fig, f"{metrica.nombre}_{slug}.png")


def figura_resumen(algoritmo, datos):
    """Todas las métricas en una columna para un algoritmo."""
    metricas = [m for m in METRICAS if m.en_resumen]
    fig, ejes = plt.subplots(len(metricas), 1, figsize=(6.5, 2.8 * len(metricas)),
                             layout="constrained")
    fig.suptitle(f"Resumen experimental: {NOMBRE[algoritmo]} — {TAMANO}",
                 fontsize=11, fontweight="bold", color=TINTA)

    for eje, metrica in zip(ejes, metricas):
        subtitulo = metrica.dibujar(eje, algoritmo, datos)
        if metrica.titulo.startswith(f"{metrica.fila}:"):
            titulo_panel = metrica.titulo
        else:
            titulo_panel = f"{metrica.fila}: {metrica.titulo}"
        if subtitulo:
            titulo_panel += f" ({subtitulo})"
        eje.set_title(titulo_panel, pad=6, fontsize=9)
        eje.set_xlabel(metrica.xlabel)
        eje.set_ylabel(metrica.ylabel)

    slug = algoritmo.lower()
    guardar(fig, f"resumen_{slug}.png")


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
        for algoritmo in ALGORITMOS:
            figura_individual(metrica, algoritmo, datos)

    for algoritmo in ALGORITMOS:
        figura_resumen(algoritmo, datos)

    print("Listo.")


if __name__ == "__main__":
    main()
