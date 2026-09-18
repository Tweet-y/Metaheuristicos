"""Presentación de resultados por pantalla y registro en CSV."""

import csv
import os

CABECERA_RESULTADO = [
    "Algoritmo", "Instancia", "Semilla", "Poblacion", "Prob_Cruce", "Prob_Mutacion",
    "Iteraciones", "Makespan", "Upper_Bound", "RPD_%", "Tiempo_Seg", "Mejor_Secuencia",
]

CABECERA_TRAZA = ["Algoritmo", "Instancia", "Semilla", "Generacion", "Makespan"]


def _escribir(ruta_csv, cabecera, filas):
    """Agrega filas al CSV, creando la carpeta y la cabecera si hacen falta."""
    carpeta = os.path.dirname(ruta_csv)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    existe = os.path.exists(ruta_csv)
    with open(ruta_csv, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";", lineterminator="\n")
        if not existe:
            writer.writerow(cabecera)
        writer.writerows(filas)


def guardar_resultado_csv(ruta_csv, algoritmo, instancia, semilla, tam_pobla, prob_c,
                          prob_m, iteraciones, makespan, cota_superior, rpd, tiempo_seg,
                          mejor_sol):
    """Registra el resultado de una corrida."""
    _escribir(ruta_csv, CABECERA_RESULTADO, [[
        algoritmo, instancia, semilla, tam_pobla, prob_c, prob_m, iteraciones,
        makespan, cota_superior, f"{rpd:.2f}", f"{tiempo_seg:.4f}",
        "-".join(str(trabajo) for trabajo in mejor_sol),
    ]])
    print(f"\n[OK] Resultado guardado en: {ruta_csv}")


def guardar_traza_csv(ruta_csv, algoritmo, instancia, semilla, traza):
    """Registra la traza de mejoras: en qué generación se halló cada makespan."""
    _escribir(ruta_csv, CABECERA_TRAZA, [
        [algoritmo, instancia, semilla, generacion, makespan]
        for generacion, makespan in traza
    ])
    print(f"[OK] Traza de convergencia guardada en: {ruta_csv}")


def imprimir_resultados(algoritmo, semilla, instancia, mejor_sol, makespan,
                        cota_superior, rpd, tiempo_seg, generacion_hallazgo):
    """Bloque final de resultados por pantalla."""
    print("\n" + "=" * 50)
    print(f"RESULTADOS FINALES {algoritmo.upper()}:")
    print(f"Semilla:                    {semilla}")
    print(f"Instancia:                  {instancia}")
    print(f"Mejor secuencia encontrada: {mejor_sol}")
    print(f"Makespan obtenido:          {makespan}")
    print(f"Upper Bound conocido:       {cota_superior}")
    print(f"RPD (% de error):           {rpd:.2f}%")
    print(f"Hallado en la generación:   {generacion_hallazgo}")
    print(f"Tiempo de ejecución:        {tiempo_seg:.4f} segundos")
    print("=" * 50)
