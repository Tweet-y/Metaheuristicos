import numpy as np 
import time 
import sys
import csv
import os
import random


def leer_instancia_taillard(ruta_archivo):
    """Lee y parsea una instancia de Taillard."""
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo de instancia '{ruta_archivo}' no existe.")
        sys.exit(1)
    with open(ruta_archivo, "r") as f:
        primera_linea = f.readline().strip().split()
        num_job = int(primera_linea[0])
        num_maq = int(primera_linea[1])
        lim_inf = int(primera_linea[3])
        lim_sup = int(primera_linea[4])
        matriz = np.loadtxt(f, dtype=int).tolist()
    return matriz, num_maq, num_job, lim_inf, lim_sup


def inicializar_poblacion(tam_pobla, num_job):
    """Inicializa la población generando permutaciones aleatorias."""
    pobla = [list(map(int, np.random.permutation(num_job))) for _ in range(tam_pobla)]
    return pobla


def calcular_makespan(individuo, matriz, num_maq):
    """Calcula el makespan (Cmax) para una permutación dada."""
    tiempos_maquinas = [0] * num_maq
    for trabajo in individuo:
        tiempos_maquinas[0] += matriz[0][trabajo]
        for m in range(1, num_maq):
            prev = tiempos_maquinas[m - 1]
            if tiempos_maquinas[m] < prev:
                tiempos_maquinas[m] = prev
            tiempos_maquinas[m] += matriz[m][trabajo]
    return tiempos_maquinas[-1]


def evaluar_poblacion(poblacion, matriz, num_maq):
    """Evalúa el makespan de cada individuo en la población."""
    return [calcular_makespan(ind, matriz, num_maq) for ind in poblacion]


def seleccion_torneo(poblacion, fitness, k=2):
    """Selección por torneo determinista de tamaño k."""
    indices = random.sample(range(len(poblacion)), k)
    mejor_idx = min(indices, key=lambda i: fitness[i])
    return list(poblacion[mejor_idx])


def cruce_ox(padre1, padre2, prob_c):
    """Cruce por orden (Order Crossover - OX)."""
    if random.random() > prob_c:
        return list(padre1), list(padre2)

    n = len(padre1)
    c1, c2 = sorted(random.sample(range(n), 2))

    def generar_hijo(p1, p2):
        hijo = [-1] * n
        hijo[c1:c2 + 1] = p1[c1:c2 + 1]
        en_hijo = set(hijo[c1:c2 + 1])

        pos_hijo = (c2 + 1) % n
        for i in range(n):
            gen = p2[(c2 + 1 + i) % n]
            if gen not in en_hijo:
                hijo[pos_hijo] = gen
                pos_hijo = (pos_hijo + 1) % n
        return hijo

    return generar_hijo(padre1, padre2), generar_hijo(padre2, padre1)


def mutacion_swap(individuo, prob_m):
    """Intercambia dos posiciones al azar con probabilidad prob_m."""
    if random.random() < prob_m:
        mutado = list(individuo)
        n = len(mutado)
        i, j = random.sample(range(n), 2)
        mutado[i], mutado[j] = mutado[j], mutado[i]
        return mutado
    return list(individuo)


def mutacion_insercion(individuo, prob_m):
    """Extrae un trabajo y lo reinserta en otra posición."""
    if random.random() < prob_m:
        mutado = list(individuo)
        n = len(mutado)
        i, j = random.sample(range(n), 2)
        trabajo = mutado.pop(i)
        mutado.insert(j, trabajo)
        return mutado
    return list(individuo)


def mutar_individuo(individuo, prob_m):
    """Aplica swap o inserción probabilísticamente."""
    if random.random() < 0.5:
        return mutacion_swap(individuo, prob_m)
    return mutacion_insercion(individuo, prob_m)


def busqueda_local_insercion(individuo, matriz, num_maq, max_iter=20):
    """Búsqueda local por inserción aplicada a un individuo."""
    mejor_sol = list(individuo)
    mejor_mk = calcular_makespan(mejor_sol, matriz, num_maq)
    n = len(mejor_sol)
    mejora = True
    iter_bl = 0

    while mejora and iter_bl < max_iter:
        mejora = False
        iter_bl += 1
        for i in range(n):
            item = mejor_sol.pop(i)
            mejor_pos = i

            for j in range(n):
                mejor_sol.insert(j, item)
                mk = calcular_makespan(mejor_sol, matriz, num_maq)

                if mk < mejor_mk:
                    mejor_mk = mk
                    mejor_pos = j
                    mejora = True

                mejor_sol.pop(j)

            mejor_sol.insert(mejor_pos, item)
            if mejora:
                break

    return mejor_sol, mejor_mk


def guardar_resultado_csv(ruta_csv, instancia, semilla, tam_pobla, prob_c, prob_m,
                          iteraciones, mejor_mk, cota_ref, rpd, tiempo_seg, mejor_sol):
    """Registra los resultados en un archivo CSV."""
    carpeta = os.path.dirname(ruta_csv)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    existe = os.path.exists(ruta_csv)

    with open(ruta_csv, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        if not existe:
            writer.writerow([
                "Algoritmo", "Instancia", "Semilla", "Poblacion", "Prob_Cruce", "Prob_Mutacion",
                "Iteraciones", "Makespan", "Upper_Bound", "RPD_%", "Tiempo_Seg", "Mejor_Secuencia"
            ])
        secuencia_str = "-".join(map(str, mejor_sol))
        writer.writerow([
            "Memético", instancia, semilla, tam_pobla, prob_c, prob_m,
            iteraciones, mejor_mk, cota_ref, f"{rpd:.2f}", f"{tiempo_seg:.4f}", secuencia_str
        ])
    print(f"\n[OK] Resultado guardado exitosamente en: {ruta_csv}")


def ejecutar_algoritmo_memetico(tam_pobla, prob_c, prob_m, iteraciones, matriz, num_maq, num_job, lim_inf, freq_bl=1):
    """Ciclo principal del Algoritmo Memético con explotación por búsqueda local."""
    poblacion = inicializar_poblacion(tam_pobla, num_job)
    fitness = evaluar_poblacion(poblacion, matriz, num_maq)

    idx_mejor = min(range(len(fitness)), key=lambda i: fitness[i])
    mejor_solucion = list(poblacion[idx_mejor])
    mejor_makespan = fitness[idx_mejor]

    paso_progreso = max(1, iteraciones // 10)

    for gen in range(1, iteraciones + 1):
        nueva_poblacion = []
        nuevo_fitness = []

        # Elitismo + Explotación por Búsqueda Local sobre el Élite
        idx_elite = min(range(len(fitness)), key=lambda i: fitness[i])
        elite = list(poblacion[idx_elite])
        elite_mk = fitness[idx_elite]

        if gen % freq_bl == 0:
            elite, elite_mk = busqueda_local_insercion(elite, matriz, num_maq)

        nueva_poblacion.append(elite)
        nuevo_fitness.append(elite_mk)

        while len(nueva_poblacion) < tam_pobla:
            padre1 = seleccion_torneo(poblacion, fitness)
            padre2 = seleccion_torneo(poblacion, fitness)

            hijo1, hijo2 = cruce_ox(padre1, padre2, prob_c)
            hijo1 = mutar_individuo(hijo1, prob_m)
            hijo2 = mutar_individuo(hijo2, prob_m)

            nueva_poblacion.append(hijo1)
            nuevo_fitness.append(calcular_makespan(hijo1, matriz, num_maq))

            if len(nueva_poblacion) < tam_pobla:
                nueva_poblacion.append(hijo2)
                nuevo_fitness.append(calcular_makespan(hijo2, matriz, num_maq))

        poblacion = nueva_poblacion
        fitness = nuevo_fitness

        min_gen = min(fitness)
        if min_gen < mejor_makespan:
            mejor_makespan = min_gen
            idx_m = min(range(len(fitness)), key=lambda i: fitness[i])
            mejor_solucion = list(poblacion[idx_m])

        if gen % paso_progreso == 0 or gen == iteraciones:
            print(f"Generación {gen}/{iteraciones}: Mejor Makespan = {mejor_makespan}")

        if mejor_makespan <= lim_inf:
            print(f"\n[!] Óptimo global ({lim_inf}) alcanzado anticipadamente en generación {gen}!")
            break

    return mejor_solucion, mejor_makespan


def main():
    if len(sys.argv) < 7:
        print("Error en la entrada de los parametros")
        print("Uso: python algoritmoMemetico.py semilla archivo_instancia tam_poblacion prob_cruza prob_mutacion iteraciones [frecuencia_bl] [salida.csv]")
        print("Donde:")
        print(" - semilla: valor entero positivo [ejem: 1]")
        print(" - archivo_instancia: ruta del archivo de datos [ejem: data/ins_20_5_00.txt]")
        print(" - tam_poblacion: valor entero positivo [ejem: 60]")
        print(" - prob_cruza: valor real positivo entre 0.0 y 1.0 con punto [ejem: 0.85]")
        print(" - prob_mutacion: valor real positivo entre 0.0 y 1.0 con punto [ejem: 0.20]")
        print(" - iteraciones: valor entero positivo [ejem: 300]")
        print(" - frecuencia_bl: (opcional) cada cuántas generaciones aplicar búsqueda local [default: 1]")
        print(" - salida.csv: (opcional) archivo donde registrar resultados")
        sys.exit(1)

    try:
        semilla = int(sys.argv[1])
    except ValueError:
        print("Error: 'semilla' debe ser un número entero.")
        sys.exit(1)

    entrada = sys.argv[2]
    if not os.path.isfile(entrada):
        print(f"Error: El archivo de instancia '{entrada}' no existe.")
        sys.exit(1)

    try:
        tam_pobla = int(sys.argv[3])
        if tam_pobla <= 0:
            raise ValueError()
    except ValueError:
        print("Error: 'tam_poblacion' debe ser un número entero mayor a 0.")
        sys.exit(1)

    if "," in sys.argv[4]:
        print("Error: 'prob_cruza' debe usar punto decimal (ejem: 0.85), no comas.")
        sys.exit(1)
    try:
        prob_c = float(sys.argv[4])
        if not (0.0 <= prob_c <= 1.0):
            raise ValueError()
    except ValueError:
        print("Error: 'prob_cruza' debe ser un número decimal entre 0.0 y 1.0.")
        sys.exit(1)

    if "," in sys.argv[5]:
        print("Error: 'prob_mutacion' debe usar punto decimal (ejem: 0.20), no comas.")
        sys.exit(1)
    try:
        prob_m = float(sys.argv[5])
        if not (0.0 <= prob_m <= 1.0):
            raise ValueError()
    except ValueError:
        print("Error: 'prob_mutacion' debe ser un número decimal entre 0.0 y 1.0.")
        sys.exit(1)

    try:
        iteracion = int(sys.argv[6])
        if iteracion <= 0:
            raise ValueError()
    except ValueError:
        print("Error: 'iteraciones' debe ser un número entero mayor a 0.")
        sys.exit(1)

    # Parámetros opcionales (frecuencia_bl y salida.csv)
    freq_bl = 1
    salida = None

    if len(sys.argv) == 8:
        arg7 = sys.argv[7]
        if arg7.endswith(".csv") or "/" in arg7 or "\\" in arg7:
            salida = arg7
        else:
            try:
                freq_bl = int(arg7)
            except ValueError:
                salida = arg7
    elif len(sys.argv) >= 9:
        try:
            freq_bl = int(sys.argv[7])
        except ValueError:
            print("Error: 'frecuencia_bl' debe ser un entero positivo.")
            sys.exit(1)
        salida = sys.argv[8]

    # Semillas aleatorias para reproducibilidad
    np.random.seed(semilla)
    random.seed(semilla)

    matriz, num_maq, num_job, lim_inf, lim_sup = leer_instancia_taillard(entrada)

    print(f"Parámetros cargados (Memético): semilla={semilla}, archivo={entrada}, Pob={tam_pobla}, Pc={prob_c}, Pm={prob_m}, Iter={iteracion}, FreqBL={freq_bl}")
    print(f"Instancia: {num_job} trabajos, {num_maq} máquinas | Upper Bound: {lim_inf}, Lower Bound: {lim_sup}\n")

    tiempo_inicio = time.time()
    mejor_sol, mejor_mk = ejecutar_algoritmo_memetico(
        tam_pobla, prob_c, prob_m, iteracion, matriz, num_maq, num_job, lim_inf, freq_bl
    )
    tiempo_fin = time.time()
    tiempo_total = tiempo_fin - tiempo_inicio

    rpd = ((mejor_mk - lim_inf) / lim_inf) * 100

    print("\n" + "=" * 50)
    print("RESULTADOS FINALES ALGORITMO MEMÉTICO:")
    print(f"Semilla:                    {semilla}")
    print(f"Instancia:                  {entrada}")
    print(f"Mejor secuencia encontrada: {[int(x) for x in mejor_sol]}")
    print(f"Makespan obtenido:          {mejor_mk}")
    print(f"Upper Bound conocido:       {lim_inf}")
    print(f"RPD (% de error):           {rpd:.2f}%")
    print(f"Tiempo de ejecución:        {tiempo_total:.4f} segundos")
    print("=" * 50)

    if salida:
        guardar_resultado_csv(
            ruta_csv=salida,
            instancia=entrada,
            semilla=semilla,
            tam_pobla=tam_pobla,
            prob_c=prob_c,
            prob_m=prob_m,
            iteraciones=iteracion,
            mejor_mk=mejor_mk,
            cota_ref=lim_inf,
            rpd=rpd,
            tiempo_seg=tiempo_total,
            mejor_sol=mejor_sol
        )


if __name__ == "__main__":
    main()
