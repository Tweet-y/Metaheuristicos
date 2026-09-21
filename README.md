# Proyecto 1: Permutation Flow Shop Scheduling Problem (PFSP)

## Algoritmos Metaheurísticos — Algoritmo Genético y Algoritmo Memético

Implementación y evaluación experimental de metaheurísticas poblacionales sobre el problema de secuenciamiento en taller de flujo (_Permutation Flow Shop Scheduling Problem_, PFSP), con instancias de referencia de Taillard.

---

## 1. Instalación

Requisito: **Python 3.9 o superior** (probado en 3.9 y 3.13).

Los algoritmos no usan ninguna dependencia externa: corren con Python a secas.

```bash
python3 algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300
```

Solo `experimentos/generar_graficos.py` necesita matplotlib:

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
├── experimentos/                    # Scripts de la evaluación experimental
│   ├── ejecutar_comparativa.py      # Batería experimental completa
│   ├── barrido_parametros.py        # Barrido de parámetros (un factor a la vez)
│   ├── procesar_resultados.py       # Tabla resumen en consola
│   └── generar_graficos.py          # Figuras del informe
├── data/                            # Instancias de Taillard (.txt)
├── results/
│   ├── comparativa_{slug}.csv       # Resultados por instancia (ej. 50_10_00)
│   ├── barrido_parametros.csv       # Barrido para justificar los parámetros
│   └── graficos/                    # Figuras del informe por tamaño (ej. 20x5/, 100x5/)
├── algoritmoGenetico.py             # Programa del Algoritmo Genético
├── algoritmoMemetico.py             # Programa del Algoritmo Memético
├── test_makespan.py                 # Chequeos de correctitud
└── requirements.txt
```

### Dónde está cada función pedida

| Requerimiento                  | Archivo                | Función                                                  |
| ------------------------------ | ---------------------- | -------------------------------------------------------- |
| Número real aleatorio en [0,1] | `pfsp/rng.py`          | `aleatorio_real`                                         |
| Entero aleatorio en un rango   | `pfsp/rng.py`          | `aleatorio_entero`                                       |
| Leer instancia de Taillard     | `pfsp/instance.py`     | `leer_instancia_taillard`                                |
| Inicializar población          | `pfsp/operators.py`    | `inicializar_poblacion`                                  |
| Calcular fitness               | `pfsp/makespan.py`     | `calcular_makespan`, `evaluar_poblacion`                 |
| Seleccionar individuo          | `pfsp/operators.py`    | `seleccion_torneo`                                       |
| Cruzar dos individuos          | `pfsp/operators.py`    | `cruce_ox`                                               |
| Mutar individuo                | `pfsp/operators.py`    | `mutacion_swap`, `mutacion_insercion`, `mutar_individuo` |
| Reemplazo con elitismo         | `pfsp/operators.py`    | `reemplazo_mu_lambda`                                    |
| Búsqueda local (Memético)      | `pfsp/local_search.py` | `busqueda_local_insercion`                               |

Los dos programas principales reexportan todas estas funciones, así que también se llegan como `algoritmoGenetico.seleccion_torneo`, etc.

---

## 3. Ejecución

### A. Algoritmo Genético

```bash
python algoritmoGenetico.py <semilla> <archivo_instancia> <tam_poblacion> <prob_cruza> <prob_mutacion> <iteraciones> [salida.csv]
```

- `semilla`: entero no negativo (ej: `1`).
- `archivo_instancia`: ruta a la instancia (ej: `data/ins_20_5_00.txt`).
- `tam_poblacion`: entero positivo (ej: `60`).
- `prob_cruza`: real entre 0.0 y 1.0, con punto decimal (ej: `0.85`).
- `prob_mutacion`: real entre 0.0 y 1.0, con punto decimal (ej: `0.20`).
- `iteraciones`: entero positivo de generaciones (ej: `300`).
- `salida.csv`: _(opcional)_ archivo donde registrar el resultado.

```bash
python algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300
python algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300 results/resultado_ag.csv
```

### B. Algoritmo Memético

Agrega un parámetro opcional antes del CSV:

```bash
python algoritmoMemetico.py <semilla> <archivo_instancia> <tam_poblacion> <prob_cruza> <prob_mutacion> <iteraciones> [frecuencia_bl] [salida.csv]
```

- `frecuencia_bl`: _(opcional, por defecto 1)_ cada cuántas generaciones aplicar la búsqueda local.

```bash
python algoritmoMemetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300 1 results/resultado_memetico.csv
```

Cuando se entrega un CSV de salida, también se escribe uno con el sufijo `_traza` que registra en qué generación se halló cada mejora.

### C. Batería experimental, tabla y figuras

```bash
python -m experimentos.ejecutar_comparativa    # 12 instancias x 30 semillas x 2 algoritmos = 720 corridas
python -m experimentos.procesar_resultados     # tabla resumen en consola
python -m experimentos.generar_graficos        # figuras de 20x5, 100x5 y 500x20 en results/graficos/
```

### D. Barrido de parámetros

```bash
python -m experimentos.barrido_parametros       # ~6 minutos
```

Varía un parámetro a la vez alrededor de la configuración base, dejando fijos los demás. Sirve para justificar los valores elegidos; `experimentos/ejecutar_comparativa.py` los usa una vez ya elegidos.

### E. Chequeos de correctitud

```bash
python test_makespan.py
```

Verifica, entre otras cosas, que el makespan reportado sea el de la secuencia devuelta, y que la búsqueda local acelerada entregue exactamente lo mismo que recalcular cada inserción desde cero.

---

## 4. El problema

### 4.1. Definición

- $n$ trabajos y $m$ máquinas. Cada trabajo pasa por todas las máquinas en el mismo orden $M_1 \rightarrow \dots \rightarrow M_m$.
- Cada trabajo $i$ tarda $p_{i,j}$ en la máquina $j$.
- **Restricción de permutación:** el orden de entrada a la primera máquina se mantiene en todas las demás.
- **Objetivo:** hallar la permutación que minimice el _makespan_ $C_{\max}$.

En los archivos de Taillard las **filas son máquinas y las columnas son trabajos**.

### 4.2. Makespan

$$C(i, j) = \max(C(i-1, j), C(i, j-1)) + p_{\pi_i, j}$$

con $C(0,j) = C(i,0) = 0$; el valor a minimizar es $C_{\max} = C(n, m)$. Basta mantener el vector de términos de las $m$ máquinas, así que evaluar una secuencia cuesta $O(nm)$ y el espacio extra es $O(m)$.

### 4.3. Métrica: RPD (%)

$$\text{RPD} = \frac{C_{\max}^{\text{obtenido}} - UB}{UB} \times 100$$

donde $UB$ es el mejor valor conocido de la instancia; el resultado queda expresado en porcentaje.

---

## 5. Decisiones de implementación

- **Representación:** permutación de $n$ enteros sin repetición.
- **Población inicial:** permutaciones aleatorias uniformes, con un individuo sembrado por **NEH**.
- **Selección:** torneo determinista de tamaño $k=3$. Con $k=2$ la presión selectiva resulta insuficiente y la población deriva sin converger.
- **Cruce:** _Order Crossover_ (OX), que preserva el orden relativo sin producir repetidos.
- **Mutación:** _swap_ o inserción, elegidas con igual probabilidad.
- **Reemplazo:** $(\mu+\lambda)$ **sin duplicados**. Padres e hijos compiten y sobreviven los $\mu$ mejores distintos. El filtro de duplicados es necesario: sin él, la mejor solución se copia a sí misma hasta llenar la población (en la generación 10 quedaban 2 individuos distintos y 56 copias del mismo) y la cruza pasa a combinar solo clones.
- **Búsqueda local (Memético):** inserción con _first improvement_, aplicada al mejor individuo y al siguiente mejor que aún no esté en óptimo local. Se recuerdan las secuencias ya optimizadas: como la búsqueda es determinista, relanzarla sobre una de ellas devolvería lo mismo, así que el presupuesto se gasta siempre en alguien que todavía puede mejorar.
- **Aceleración de Taillard (1990):** evaluar el vecindario de inserción de un trabajo reconstruyendo cada permutación cuesta $O(n^2m)$; con una pasada hacia adelante y otra hacia atrás, cada posición se evalúa en $O(m)$ y el vecindario completo en $O(nm)$. El resultado es idéntico, y está verificado en `test_makespan.py`.

---

## 6. Resultados

30 semillas por combinación, población 60, $P_c = 0.85$, 300 generaciones. La mutación es $P_m = 0.20$, salvo en las tres instancias más grandes (200x10, 200x20 y 500x20), corridas con $P_m = 0.50$.

**Por qué $P_m$ sube en las instancias grandes.** El operador de mutación aplica *una sola* transposición o inserción por individuo (`mutar_individuo` en `pfsp/operators.py`), no una por posición. La cantidad esperada de posiciones alteradas es entonces constante, del orden de $2P_m$, y no depende de $n$: la **fracción** perturbada del cromosoma es $\approx 2P_m / n$ y decae linealmente con el tamaño del problema. Con $P_m = 0.20$ eso equivale a alterar cerca del 2% de una permutación de 20 trabajos, pero menos del 0.1% de una de 500, unas 25 veces menos perturbación relativa bajo el mismo parámetro.

A eso se suma que el presupuesto es fijo —60 individuos, 300 generaciones— mientras el espacio de búsqueda crece como $n!$. En las instancias grandes la población se homogeneiza antes de agotar las generaciones y la cruza OX, aplicada sobre padres cada vez más parecidos, deja de aportar variación: la mutación queda como única fuente real de exploración. Subir $P_m$ a 0.50 compensa parcialmente ese desbalance. Conviene leerlo como lo que es: una compensación en la dirección correcta, no un valor ajustado. Igualar la tasa de perturbación relativa de las instancias chicas exigiría valores de $P_m$ fuera del rango admisible, y la comparación que respalda el 0.50 se hizo entre dos valores y con pocas repeticiones, porque cada corrida sobre 200 y 500 trabajos es cara.

| Instancia       | Algoritmo | UB   | Mejor | RPD mín | RPD prom     | Tiempo |
| --------------- | --------- | ---- | ----- | ------- | ------------ | ------ |
| Mediana (50x10) | AG        | 3025 | 3091  | 2.18%   | 3.24% ± 0.28 | 1.95 s |
| Mediana (50x10) | Memético  | 3025 | 3025  | 0.00%   | 0.65% ± 0.39 | 6.54 s |

Las figuras van a `results/graficos/{tamano}/` (ej. `20x5/`), una carpeta por instancia y un archivo `{metrica}_{algoritmo}.png` por cada una:

| Archivo                                | Qué muestra                                                                                |
| -------------------------------------- | ------------------------------------------------------------------------------------------ |
| `resumen_{algoritmo}.png`              | Las tres métricas siguientes en una columna para el algoritmo e instancia correspondiente. |
| `generacion_hallazgo_{algoritmo}.png`  | Generación en que se halló el mejor makespan por cada semilla (con promedio).              |
| `makespan_por_semilla_{algoritmo}.png` | Mejor makespan alcanzado por cada una de las 30 semillas.                                  |
| `tiempo_por_semilla_{algoritmo}.png`   | Tiempo de proceso de cada semilla.                                                         |
| `distribucion_rpd_{algoritmo}.png`     | RPD con diagrama de caja y las 30 observaciones superpuestas.                              |

`distribucion_rpd_{algoritmo}.png` muestra el diagrama de cajas con las 30 semillas superpuestas. Permite observar tanto la dispersión como el número de semillas que empatan en cada valor de RPD respecto al UB.

No se grafican todas las instancias del barrido: `experimentos/generar_graficos.py` solo procesa las de `INSTANCIAS_GRAFICAS`, que son las que el informe necesita. Del resto queda el CSV y la fila en la tabla resumen.

### 6.1. Justificación de los parámetros

Del barrido en 50x10 con 5 semillas (`results/barrido_parametros.csv`). Conviene leerlo con cuidado: con 5 semillas la mayoría de las diferencias cae dentro de una desviación estándar, así que lo que muestra es que la configuración base está en una zona plana razonable, no que sea un óptimo. Las señales que sí se distinguen del ruido:

- **Torneo $k$:** en el AG, $k=2$ es el peor valor probado (3.36% frente a 2.87-3.17% del resto), que es la observación que motivó abandonarlo. En el Memético, $k=4$ y $k=6$ empeoran claramente (1.00% y 1.04% frente a 0.46%): demasiada presión selectiva sobre una población que ya converge rápido por la búsqueda local.
- **Probabilidad de cruce:** en el Memético, $P_c = 0.95$ empeora a 1.07%. Entre 0.60 y 0.85 no hay diferencia apreciable.
- **Probabilidad de mutación:** en el Memético, bajarla a 0.05 o 0.10 empeora (0.95% y 0.85%); hace falta mutación para escapar de los óptimos locales que introduce la búsqueda local.
- **Tamaño de población:** el efecto es pequeño y el costo crece de forma lineal. 60 es un punto intermedio razonable.
