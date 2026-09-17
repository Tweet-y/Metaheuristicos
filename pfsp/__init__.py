"""Biblioteca de operadores y algoritmos para el Permutation Flow Shop (PFSP).

Los módulos están separados por responsabilidad para que los operadores sean
reutilizables en otros problemas de representación por permutación:

    instance      lectura y validación de instancias de Taillard
    makespan      función de aptitud (Cmax)
    rng           primitivas de números aleatorios
    operators     población, selección, cruza, mutación y reemplazo
    local_search  búsqueda local por inserción (acelerada, Taillard 1990)
    neh           heurística constructiva NEH para sembrar la población
    ga            ciclo evolutivo común al Algoritmo Genético y al Memético
    salida        impresión de resultados y registro en CSV
"""
