"""Función de aptitud: makespan (Cmax) de una permutación."""


def calcular_makespan(individuo, matriz, num_maq):
    """Cmax de la permutación `individuo`.

    Aplica la recurrencia C(i, j) = max(C(i-1, j), C(i, j-1)) + p[j][pi_i]. Como
    cada trabajo solo necesita la columna anterior, basta mantener el vector de
    términos de las `num_maq` máquinas: el costo es O(n*m) y el espacio O(m).
    """
    tiempos = [0] * num_maq
    for trabajo in individuo:
        tiempos[0] += matriz[0][trabajo]
        for m in range(1, num_maq):
            previo = tiempos[m - 1]
            if tiempos[m] < previo:
                tiempos[m] = previo
            tiempos[m] += matriz[m][trabajo]
    return tiempos[-1]


def evaluar_poblacion(poblacion, matriz, num_maq):
    """Makespan de cada individuo de la población."""
    return [calcular_makespan(individuo, matriz, num_maq) for individuo in poblacion]
