# Proyecto 1: Permutation Flow Shop Scheduling Problem (PFSP)
## Algoritmos Metaheurísticos — Algoritmo Genético y Algoritmo Memético

Implementación y evaluación experimental de metaheurísticas poblacionales sobre el problema de secuenciamiento en taller de flujo (*Permutation Flow Shop Scheduling Problem*, PFSP), con instancias de referencia de Taillard.

---

## 1. Instalación

Requisito: **Python 3.9 o superior** (probado en 3.9 y 3.13).

Los algoritmos no usan ninguna dependencia externa: corren con Python a secas.

```bash
python3 algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300
```

Solo `generar_graficos.py` necesita matplotlib:

```bash
python3 -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Estructura del proyecto

```text
Metaheuristicos/
├── pfsp/                            # Biblioteca de operadores, reutilizable
│   ├── instance.py                  # Lectura y validación de instancias de Taillard
│   ├── makespan.py                  # Función de aptitud (Cmax)
│   ├── rng.py                       # Primitivas de números aleatorios
│   ├── operators.py                 # Población, selección, cruza, mutación, reemplazo
│   ├── local_search.py              # Búsqueda local por inserción (acelerada)
│   ├── neh.py                       # Heurística constructiva NEH
│   ├── ga.py                        # Ciclo evolutivo común al AG y al Memético
│   ├── cli.py                       # Validación de parámetros de entrada
│   └── salida.py                    # Impresión de resultados y registro en CSV
├── data/                            # Instancias de Taillard (.txt)
├── results/
│   ├── comparativa_ag_vs_memetico.csv
│   ├── traza_convergencia.csv       # Generación en que se halló cada mejora
│   ├── barrido_parametros.csv       # Barrido para justificar los parámetros
│   └── graficos/                    # Figuras del informe (.png)
├── algoritmoGenetico.py             # Programa del Algoritmo Genético
├── algoritmoMemetico.py             # Programa del Algoritmo Memético
├── ejecutar_comparativa.py          # Batería experimental completa
├── barrido_parametros.py            # Barrido de parámetros (un factor a la vez)
├── procesar_resultados.py           # Tabla resumen en consola
├── generar_graficos.py              # Figuras del informe
├── test_makespan.py                 # Chequeos de correctitud
└── requirements.txt
```

### Dónde está cada función pedida

| Requerimiento | Archivo | Función |
|---|---|---|
| Número real aleatorio en [0,1] | `pfsp/rng.py` | `aleatorio_real` |
| Entero aleatorio en un rango | `pfsp/rng.py` | `aleatorio_entero` |
| Leer instancia de Taillard | `pfsp/instance.py` | `leer_instancia_taillard` |
| Inicializar población | `pfsp/operators.py` | `inicializar_poblacion` |
| Calcular fitness | `pfsp/makespan.py` | `calcular_makespan`, `evaluar_poblacion` |
| Seleccionar individuo | `pfsp/operators.py` | `seleccion_torneo` |
| Cruzar dos individuos | `pfsp/operators.py` | `cruce_ox` |
| Mutar individuo | `pfsp/operators.py` | `mutacion_swap`, `mutacion_insercion`, `mutar_individuo` |
| Reemplazo con elitismo | `pfsp/operators.py` | `reemplazo_mu_lambda` |
| Búsqueda local (Memético) | `pfsp/local_search.py` | `busqueda_local_insercion` |

Los dos programas principales reexportan todas estas funciones, así que también se llegan como `algoritmoGenetico.seleccion_torneo`, etc.

---

## 3. Ejecución

### A. Algoritmo Genético

```bash
python algoritmoGenetico.py <semilla> <archivo_instancia> <tam_poblacion> <prob_cruza> <prob_mutacion> <iteraciones> [salida.csv]
```

* `semilla`: entero no negativo (ej: `1`).
* `archivo_instancia`: ruta a la instancia (ej: `data/ins_20_5_00.txt`).
* `tam_poblacion`: entero positivo (ej: `60`).
* `prob_cruza`: real entre 0.0 y 1.0, con punto decimal (ej: `0.85`).
* `prob_mutacion`: real entre 0.0 y 1.0, con punto decimal (ej: `0.20`).
* `iteraciones`: entero positivo de generaciones (ej: `300`).
* `salida.csv`: *(opcional)* archivo donde registrar el resultado.

```bash
python algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300
python algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300 results/resultado_ag.csv
```

### B. Algoritmo Memético

Agrega un parámetro opcional antes del CSV:

```bash
python algoritmoMemetico.py <semilla> <archivo_instancia> <tam_poblacion> <prob_cruza> <prob_mutacion> <iteraciones> [frecuencia_bl] [salida.csv]
```

* `frecuencia_bl`: *(opcional, por defecto 1)* cada cuántas generaciones aplicar la búsqueda local.

```bash
python algoritmoMemetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300 1 results/resultado_memetico.csv
```

Cuando se entrega un CSV de salida, también se escribe uno con el sufijo `_traza` que registra en qué generación se halló cada mejora.

### C. Batería experimental, tabla y figuras

```bash
python ejecutar_comparativa.py    # 3 tamaños x 10 semillas x 2 algoritmos
python procesar_resultados.py     # tabla resumen en consola
python generar_graficos.py        # figuras en results/graficos/
```

### D. Barrido de parámetros

```bash
python barrido_parametros.py       # ~6 minutos
```

Varía un parámetro a la vez alrededor de la configuración base, dejando fijos los demás. Sirve para justificar los valores elegidos; `ejecutar_comparativa.py` los usa una vez ya elegidos.

### E. Chequeos de correctitud

```bash
python test_makespan.py
```

Verifica, entre otras cosas, que el makespan reportado sea el de la secuencia devuelta, y que la búsqueda local acelerada entregue exactamente lo mismo que recalcular cada inserción desde cero.

---

## 4. El problema

### 4.1. Definición

* $n$ trabajos y $m$ máquinas. Cada trabajo pasa por todas las máquinas en el mismo orden $M_1 \rightarrow \dots \rightarrow M_m$.
* Cada trabajo $i$ tarda $p_{i,j}$ en la máquina $j$.
* **Restricción de permutación:** el orden de entrada a la primera máquina se mantiene en todas las demás.
* **Objetivo:** hallar la permutación que minimice el *makespan* $C_{\max}$.

En los archivos de Taillard las **filas son máquinas y las columnas son trabajos**.

### 4.2. Makespan

$$C(i, j) = \max(C(i-1, j), C(i, j-1)) + p_{\pi_i, j}$$

con $C(0,j) = C(i,0) = 0$; el valor a minimizar es $C_{\max} = C(n, m)$. Basta mantener el vector de términos de las $m$ máquinas, así que evaluar una secuencia cuesta $O(nm)$ y el espacio extra es $O(m)$.

### 4.3. Métrica: RPD (%)

$$\text{RPD}(\%) = \frac{C_{\max}^{\text{obtenido}} - UB}{UB} \times 100$$

donde $UB$ es el mejor valor conocido de la instancia.

---

## 5. Decisiones de implementación

* **Representación:** permutación de $n$ enteros sin repetición.
* **Población inicial:** permutaciones aleatorias uniformes, con un individuo sembrado por **NEH**.
* **Selección:** torneo determinista de tamaño $k=3$. Con $k=2$ la presión selectiva resulta insuficiente y la población deriva sin converger.
* **Cruce:** *Order Crossover* (OX), que preserva el orden relativo sin producir repetidos.
* **Mutación:** *swap* o inserción, elegidas con igual probabilidad.
* **Reemplazo:** $(\mu+\lambda)$ **sin duplicados**. Padres e hijos compiten y sobreviven los $\mu$ mejores distintos. El filtro de duplicados es necesario: sin él, la mejor solución se copia a sí misma hasta llenar la población (en la generación 10 quedaban 2 individuos distintos y 56 copias del mismo) y la cruza pasa a combinar solo clones.
* **Búsqueda local (Memético):** inserción con *first improvement*, aplicada al mejor individuo y al siguiente mejor que aún no esté en óptimo local. Se recuerdan las secuencias ya optimizadas: como la búsqueda es determinista, relanzarla sobre una de ellas devolvería lo mismo, así que el presupuesto se gasta siempre en alguien que todavía puede mejorar.
* **Aceleración de Taillard (1990):** evaluar el vecindario de inserción de un trabajo reconstruyendo cada permutación cuesta $O(n^2m)$; con una pasada hacia adelante y otra hacia atrás, cada posición se evalúa en $O(m)$ y el vecindario completo en $O(nm)$. El resultado es idéntico, y está verificado en `test_makespan.py`.

---

## 6. Resultados

10 semillas por combinación, población 60, $P_c = 0.85$, $P_m = 0.20$, 300 generaciones.

| Instancia | Algoritmo | UB | Mejor | RPD mín | RPD prom | Tiempo |
|---|---|---|---|---|---|---|
| Pequeña (20x5) | AG | 1278 | 1278 | 0.00% | 0.57% ± 0.20 | 0.36 s |
| Pequeña (20x5) | Memético | 1278 | **1278** | **0.00%** | **0.06% ± 0.20** | 0.48 s |
| Mediana (50x10) | AG | 3025 | 3105 | 2.64% | 3.26% ± 0.24 | 1.23 s |
| Mediana (50x10) | Memético | 3025 | **3034** | **0.30%** | **0.60% ± 0.36** | 3.96 s |
| Grande (100x10) | AG | 5770 | 5820 | 0.87% | 1.28% ± 0.14 | 2.42 s |
| Grande (100x10) | Memético | 5770 | **5779** | **0.16%** | **0.45% ± 0.20** | 11.06 s |

Figuras en `results/graficos/`:

| Archivo | Qué muestra |
|---|---|
| `resumen.png` | Las cuatro figuras siguientes en una grilla: una fila por métrica, una columna por tamaño de instancia. |
| `secuencia_mejor_solucion.png` | Trabajo asignado a cada posición, en la mejor solución de cada método. |
| `generacion_hallazgo.png` | En qué generación se halla cada mejora del makespan. |
| `makespan_por_semilla.png` | Mejor makespan alcanzado por cada semilla. |
| `tiempo_por_semilla.png` | Tiempo de proceso de cada semilla. |
| `distribucion_rpd.png` | RPD de las 10 semillas, con media y desviación estándar. |

`distribucion_rpd.png` es la que responde cuál método conviene, porque muestra a la vez las dos cosas que lo definen: **qué tan abajo** está la nube de puntos, o sea cuánto se acerca al mejor valor conocido, y **qué tan apretada** está, o sea qué tan poco depende de la semilla con que se lo ejecute. El Memético gana en ambas en los tres tamaños.

Dibuja las 10 semillas una por una en lugar de un diagrama de cajas. Con 10 observaciones y muchos valores repetidos —en 20x5 y en 100x10 el AG entrega el mismo makespan en 9 de las 10 semillas— el percentil 25 y el 75 coinciden, así que la caja queda sin altura ni bigotes y las semillas restantes aparecen marcadas como atípicas sin serlo. El diagrama de puntos evita ese artefacto.

### 6.1. Justificación de los parámetros

Del barrido en 50x10 con 5 semillas (`results/barrido_parametros.csv`). Conviene leerlo con cuidado: con 5 semillas la mayoría de las diferencias cae dentro de una desviación estándar, así que lo que muestra es que la configuración base está en una zona plana razonable, no que sea un óptimo. Las señales que sí se distinguen del ruido:

* **Torneo $k$:** en el AG, $k=2$ es el peor valor probado (3.36% frente a 2.87-3.17% del resto), que es la observación que motivó abandonarlo. En el Memético, $k=4$ y $k=6$ empeoran claramente (1.00% y 1.04% frente a 0.46%): demasiada presión selectiva sobre una población que ya converge rápido por la búsqueda local.
* **Probabilidad de cruce:** en el Memético, $P_c = 0.95$ empeora a 1.07%. Entre 0.60 y 0.85 no hay diferencia apreciable.
* **Probabilidad de mutación:** en el Memético, bajarla a 0.05 o 0.10 empeora (0.95% y 0.85%); hace falta mutación para escapar de los óptimos locales que introduce la búsqueda local.
* **Tamaño de población:** el efecto es pequeño y el costo crece de forma lineal. 60 es un punto intermedio razonable.

---

## 7. Referencias

* Taillard, E. (1993). *Benchmarks for basic scheduling problems*. European Journal of Operational Research, 64(2), 278-285.
* Taillard, E. (1990). *Some efficient heuristic methods for the flow shop sequencing problem*. European Journal of Operational Research, 47(1), 65-74.
* Nawaz, M., Enscore, E. E., y Ham, I. (1983). *A heuristic algorithm for the m-machine, n-job flow-shop sequencing problem*. Omega, 11(1), 91-95.
* Reeves, C. R. (1995). *A genetic algorithm for flowshop sequencing*. Computers & Operations Research, 22(1), 5-13.
