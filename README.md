# Proyecto 1: Permutation Flow Shop Scheduling Problem (PFSP)
## Algoritmos Metaheurísticos — Algoritmo Genético y Algoritmo Memético

Repositorio para la implementación y evaluación experimental de metaheurísticas poblacionales aplicadas al problema de secuenciamiento en taller de flujo (*Permutation Flow Shop Scheduling Problem*, PFSP) con datos de referencia de Taillard.

---

## 1. Instalación y Requisitos

Requisito recomendado: **Python 3.10+**.

Para configurar el entorno virtual e instalar las dependencias necesarias:

```bash
# Crear entorno virtual
python3 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate          # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

---

## 2. Estructura de Carpetas del Proyecto

```text
Metaheuristicos/
├── data/                                # Instancias del problema de Taillard (.txt)
│   ├── ins_20_5_00.txt                  # Instancia pequeña (20 trabajos, 5 máquinas)
│   ├── ins_50_10_00.txt                 # Instancia mediana (50 trabajos, 10 máquinas)
│   ├── ins_100_10_00.txt                # Instancia grande (100 trabajos, 10 máquinas)
│   └── ...
├── results/                             # Salidas de ejecuciones y comparativas (.csv)
│   └── comparativa_ag_vs_memetico.csv   # Resultados experimentales consolidados
├── algoritmoGenetico.py                 # Código fuente del Algoritmo Genético
├── algoritmoMemetico.py                 # Código fuente del Algoritmo Memético (+ Búsqueda Local)
├── ejecutar_comparativa.py              # Script para ejecutar batería completa de pruebas
├── ejecutar_experimentos.py             # Script para corridas múltiples con semillas
├── procesar_resultados.py              # Procesador de resultados y generador de tablas
├── requirements.txt                     # Dependencias (numpy, pandas, etc.)
└── README.md                            # Documentación del proyecto
```

---

## 3. Instrucciones de Ejecución (CLI)

### A. Algoritmo Genético

El programa recibe los parámetros por línea de comandos en el siguiente orden:

```bash
python algoritmoGenetico.py <semilla> <archivo_instancia> <tam_poblacion> <prob_cruza> <prob_mutacion> <iteraciones> [salida_csv]
```

**Parámetros:**
* `semilla`: número entero para la reproducibilidad (ej: `1`).
* `archivo_instancia`: ruta al archivo de la instancia de Taillard (ej: `data/ins_20_5_00.txt`).
* `tam_poblacion`: entero positivo, tamaño de la población (ej: `60`).
* `prob_cruza`: número real entre 0.0 y 1.0 con punto decimal (ej: `0.85`).
* `prob_mutacion`: número real entre 0.0 y 1.0 con punto decimal (ej: `0.20`).
* `iteraciones`: número entero positivo de generaciones (ej: `300`).
* `salida_csv`: *(opcional)* ruta a archivo CSV donde registrar el resultado.

**Ejemplo de ejecución:**
```bash
python algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300
```

Con guardado a CSV:
```bash
python algoritmoGenetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300 results/resultado_ag.csv
```

---

### B. Algoritmo Memético

Incorpora una etapa de explotación mediante búsqueda local por inserción (*Insertion Local Search*) sobre el individuo élite:

```bash
python algoritmoMemetico.py <semilla> <archivo_instancia> <tam_poblacion> <prob_cruza> <prob_mutacion> <iteraciones> [frecuencia_bl] [salida_csv]
```

**Parámetros adicionales:**
* `frecuencia_bl`: *(opcional, default: 1)* frecuencia en generaciones para aplicar la búsqueda local al individuo élite.
* `salida_csv`: *(opcional)* ruta al archivo CSV de resultados.

**Ejemplo de ejecución:**
```bash
python algoritmoMemetico.py 1 data/ins_20_5_00.txt 60 0.85 0.20 300 1 results/resultado_memetico.csv
```

---

### C. Batería Experimental y Tabla Resumen

Para replicar las pruebas experimentales sobre instancias pequeñas, medianas y grandes, y generar la tabla resumen con métricas (Makespan, Upper Bound, RPD % y Tiempo):

```bash
# 1. Ejecutar corridas comparativas (genera results/comparativa_ag_vs_memetico.csv)
python ejecutar_comparativa.py

# 2. Procesar y visualizar tabla consolidada en consola
python procesar_resultados.py
```

---

## 4. Fundamentos Teóricos del Problema (PFSP)

### 4.1. Definición Formal
* Se tienen $n$ trabajos ($J_1, J_2, \dots, J_n$) y $m$ máquinas ($M_1, M_2, \dots, M_m$).
* Cada trabajo debe pasar por todas las máquinas exactamente en el mismo orden: $M_1 \rightarrow M_2 \rightarrow \dots \rightarrow M_m$.
* Cada trabajo $i$ requiere un tiempo de procesamiento conocido $p_{i,j}$ en la máquina $j$.
* **Restricción de permutación:** el orden en que los trabajos ingresan a la primera máquina se mantiene idéntico en todas las máquinas subsiguientes.
* **Objetivo:** encontrar la permutación $\pi = (\pi_1, \pi_2, \dots, \pi_n)$ que minimice el *makespan* ($C_{\max}$), es decir, el instante de finalización del último trabajo en la última máquina.

### 4.2. Cálculo de Makespan (Función de Fitness)
Para una secuencia $\pi$, el tiempo de finalización $C(i, j)$ del trabajo en la posición $i$ en la máquina $j$ se calcula mediante:

$$C(i, j) = \max(C(i-1, j), C(i, j-1)) + p_{\pi_i, j}$$

con condiciones de borde $C(0, j) = 0$ y $C(i, 0) = 0$. El valor a minimizar es $C_{\max} = C(n, m)$.

### 4.3. Métrica de Desempeño: RPD (%)
Para evaluar la calidad de las soluciones respecto al mejor valor conocido (*Upper Bound*, $UB$) de Taillard:

$$\text{RPD}(\%) = \frac{C_{\max}^{\text{obtenido}} - UB}{UB} \times 100$$

---

## 5. Operadores Implementados

* **Representación:** Cromosoma tipo permutación de $n$ enteros (índices de trabajos sin repetición).
* **Población Inicial:** Generación de permutaciones aleatorias uniformes (`inicializar_poblacion`).
* **Selección:** Torneo binario determinista ($k=2$) para favorecer individuos con menor makespan (`seleccion_torneo`).
* **Cruce:** Cruce por Orden (*Order Crossover*, OX) respetando el orden relativo y evitando duplicados (`cruce_ox`).
* **Mutación:** Combinación probabilística de *Swap* (intercambio de dos posiciones) e *Insertion* (extracción e inserción) (`mutacion_swap`, `mutacion_insercion`).
* **Reemplazo:** Reemplazo generacional con elitismo estricto (preserva la mejor solución histórica sin reevaluar).
* **Búsqueda Local (Memético):** Búsqueda local por inserción sobre el individuo élite probando todas las posiciones posibles para cada trabajo hasta convergencia o límite de iteraciones (`busqueda_local_insercion`).

---

## 6. Referencias

* Taillard, E. (1993). *Benchmarks for basic scheduling problems*. European Journal of Operational Research, 64(2), 278-285.
* Reeves, C. R. (1995). *A genetic algorithm for flowshop sequencing*. Computers & Operations Research, 22(1), 5-13.