#!/usr/bin/env python3
"""Chequeos de correctitud del AG y del Memético.

Lo que realmente protege este archivo: que el makespan reportado corresponda a la
secuencia devuelta, y que la búsqueda local acelerada con Taillard entregue
exactamente lo mismo que recalcular cada inserción desde cero.

Uso: python test_makespan.py
"""

import itertools
import random

import algoritmoGenetico as ag
import algoritmoMemetico as am
from pfsp.local_search import busqueda_local_insercion, costos_insercion
from pfsp.neh import neh, orden_neh
from pfsp.operators import reemplazo_mu_lambda, renovar_poblacion

INSTANCIA = "data/ins_20_5_00.txt"


def makespan_referencia(perm, matriz, num_maq):
    """Oráculo independiente: construye la tabla completa C(i, j) sin optimizar."""
    n = len(perm)
    C = [[0] * (num_maq + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, num_maq + 1):
            C[i][j] = max(C[i - 1][j], C[i][j - 1]) + matriz[j - 1][perm[i - 1]]
    return C[n][num_maq]


def busqueda_local_ingenua(individuo, matriz, num_maq, max_iter=20):
    """Búsqueda local por inserción sin acelerar: reconstruye y reevalúa cada candidata.

    Réplica exacta de la versión previa a la aceleración. Existe solo aquí, como
    patrón de comparación contra el que se contrasta la versión rápida.
    """
    mejor_sol = list(individuo)
    mejor_mk = makespan_referencia(mejor_sol, matriz, num_maq)
    n = len(mejor_sol)
    hubo_mejora = True
    pasadas = 0

    while hubo_mejora and pasadas < max_iter:
        hubo_mejora = False
        pasadas += 1
        for i in range(n):
            trabajo = mejor_sol[i]
            sin_trabajo = mejor_sol[:i] + mejor_sol[i + 1:]
            mejor_pos = i
            for pos in range(n):
                candidata = sin_trabajo[:pos] + [trabajo] + sin_trabajo[pos:]
                mk = makespan_referencia(candidata, matriz, num_maq)
                if mk < mejor_mk:
                    mejor_mk = mk
                    mejor_pos = pos
                    hubo_mejora = True
            if hubo_mejora:
                mejor_sol = sin_trabajo[:mejor_pos] + [trabajo] + sin_trabajo[mejor_pos:]
                break

    return mejor_sol, mejor_mk


def es_permutacion(perm, n):
    return sorted(int(x) for x in perm) == list(range(n))


def test_makespan_vs_oraculo():
    """calcular_makespan coincide con el oráculo sobre permutaciones al azar."""
    random.seed(0)
    matriz, num_maq, num_job, _, _ = ag.leer_instancia_taillard(INSTANCIA)
    for _ in range(50):
        perm = random.sample(range(num_job), num_job)
        esperado = makespan_referencia(perm, matriz, num_maq)
        assert ag.calcular_makespan(perm, matriz, num_maq) == esperado
    print("  [OK] calcular_makespan coincide con el oráculo (50 permutaciones)")


def test_optimo_conocido_fuerza_bruta():
    """En una instancia mini 6x3, ninguna secuencia baja del óptimo por enumeración."""
    random.seed(1)
    num_job, num_maq = 6, 3
    matriz = [[random.randint(1, 30) for _ in range(num_job)] for _ in range(num_maq)]
    optimo = min(makespan_referencia(p, matriz, num_maq)
                 for p in itertools.permutations(range(num_job)))
    for p in itertools.permutations(range(num_job)):
        assert ag.calcular_makespan(p, matriz, num_maq) >= optimo
    print(f"  [OK] enumeración 6!=720 secuencias, óptimo={optimo}, ninguna por debajo")


def test_costos_insercion_equivalen_a_recalcular():
    """La aceleración de Taillard da los mismos costos que reconstruir cada inserción."""
    random.seed(2)
    matriz, num_maq, num_job, _, _ = ag.leer_instancia_taillard(INSTANCIA)
    for _ in range(30):
        perm = random.sample(range(num_job), num_job)
        i = random.randrange(num_job)
        trabajo = perm[i]
        sin_trabajo = perm[:i] + perm[i + 1:]

        acelerado = costos_insercion(sin_trabajo, trabajo, matriz, num_maq)
        ingenuo = [makespan_referencia(sin_trabajo[:pos] + [trabajo] + sin_trabajo[pos:],
                                       matriz, num_maq)
                   for pos in range(len(sin_trabajo) + 1)]
        assert acelerado == ingenuo, f"Taillard difiere del recálculo: {acelerado} != {ingenuo}"
    print("  [OK] costos_insercion == recálculo completo (30 vecindarios enteros)")


def test_busqueda_local_acelerada_equivale_a_la_ingenua():
    """La búsqueda local rápida devuelve exactamente la misma solución que la lenta."""
    random.seed(3)
    matriz, num_maq, num_job, _, _ = ag.leer_instancia_taillard(INSTANCIA)
    for _ in range(10):
        perm = random.sample(range(num_job), num_job)
        rapida, mk_rapida = busqueda_local_insercion(perm, matriz, num_maq)
        lenta, mk_lenta = busqueda_local_ingenua(perm, matriz, num_maq)
        assert rapida == lenta, f"secuencias distintas:\n  {rapida}\n  {lenta}"
        assert mk_rapida == mk_lenta == makespan_referencia(rapida, matriz, num_maq)
    print("  [OK] búsqueda local acelerada == búsqueda local ingenua (10 casos)")


def test_busqueda_local_no_empeora():
    """La búsqueda local nunca devuelve algo peor que su entrada."""
    random.seed(4)
    matriz, num_maq, num_job, _, _ = ag.leer_instancia_taillard(INSTANCIA)
    for _ in range(10):
        perm = random.sample(range(num_job), num_job)
        antes = ag.calcular_makespan(perm, matriz, num_maq)
        mejorado, mk = busqueda_local_insercion(perm, matriz, num_maq)
        assert es_permutacion(mejorado, num_job), "la búsqueda local rompió la permutación"
        assert mk == makespan_referencia(mejorado, matriz, num_maq), "reporta un Cmax falso"
        assert mk <= antes, f"empeoró: {antes} -> {mk}"
    print("  [OK] búsqueda local: permutación válida, Cmax real, nunca empeora")


def test_neh_construye_permutacion_valida():
    """NEH devuelve una permutación válida y mejor que el promedio aleatorio."""
    random.seed(5)
    matriz, num_maq, num_job, cota_superior, _ = ag.leer_instancia_taillard(INSTANCIA)
    secuencia = neh(matriz, num_maq, num_job)
    assert es_permutacion(secuencia, num_job), "NEH no devolvió una permutación"
    mk_neh = makespan_referencia(secuencia, matriz, num_maq)
    azar = [ag.calcular_makespan(random.sample(range(num_job), num_job), matriz, num_maq)
            for _ in range(100)]
    assert mk_neh < sum(azar) / len(azar), "NEH no mejora al promedio aleatorio"
    print(f"  [OK] NEH: Cmax={mk_neh} vs promedio aleatorio={sum(azar)/len(azar):.0f} "
          f"(UB={cota_superior})")


def test_reemplazo_conserva_los_mejores():
    """(mu+lambda) devuelve exactamente los mu mejores y deja el mejor en la posición 0."""
    random.seed(6)
    for _ in range(50):
        mu = random.randint(2, 10)
        padres = [[i] for i in range(mu)]
        hijos = [[100 + i] for i in range(mu)]
        fit_padres = [random.randint(1, 50) for _ in range(mu)]
        fit_hijos = [random.randint(1, 50) for _ in range(mu)]

        poblacion, fitness = reemplazo_mu_lambda(padres, fit_padres, hijos, fit_hijos)
        assert len(poblacion) == len(fitness) == mu
        assert fitness == sorted(fitness), "la población no quedó ordenada"
        assert fitness == sorted(fit_padres + fit_hijos)[:mu], "no sobrevivieron los mu mejores"
        assert fitness[0] == min(fit_padres + fit_hijos), "se perdió la mejor solución"
    print("  [OK] reemplazo (mu+lambda): conserva los mu mejores, el mejor en posición 0")


def test_operadores_preservan_permutacion():
    """OX y las mutaciones siempre devuelven permutaciones válidas."""
    random.seed(7)
    n = 20
    for _ in range(200):
        p1 = random.sample(range(n), n)
        p2 = random.sample(range(n), n)
        h1, h2 = ag.cruce_ox(p1, p2, 1.0)
        assert es_permutacion(h1, n) and es_permutacion(h2, n), "OX rompió la permutación"
        assert es_permutacion(ag.mutar_individuo(h1, 1.0), n), "la mutación rompió la permutación"
        assert es_permutacion(ag.mutacion_swap(h1, 1.0), n), "swap rompió la permutación"
        assert es_permutacion(ag.mutacion_insercion(h1, 1.0), n), "inserción rompió la permutación"
    print("  [OK] OX y mutaciones preservan la permutación (200 casos)")


def test_ag_reporta_makespan_real():
    """El Cmax que devuelve el AG es el Cmax real de la secuencia que devuelve."""
    for semilla in (1, 7, 42):
        random.seed(semilla)
        matriz, num_maq, num_job, cota_superior, cota_inferior = ag.leer_instancia_taillard(INSTANCIA)
        sol, mk, traza = ag.ejecutar_algoritmo_genetico(30, 0.85, 0.20, 50, matriz,
                                                        num_maq, num_job)
        assert es_permutacion(sol, num_job), f"AG devolvió una secuencia inválida: {sol}"
        real = makespan_referencia(sol, matriz, num_maq)
        assert real == mk, f"AG semilla {semilla}: reporta {mk} pero la secuencia vale {real}"
        assert mk >= cota_inferior, f"AG semilla {semilla}: {mk} bajo la cota inferior"
        assert traza[-1][1] == mk and traza == sorted(traza), "la traza no es coherente"
        print(f"  [OK] AG semilla {semilla}: reportado={mk} recalculado={real} "
              f"UB={cota_superior} hallado en gen {traza[-1][0]}")


def test_memetico_reporta_makespan_real():
    """Ídem para el Memético, incluyendo el efecto de la búsqueda local."""
    for semilla in (1, 7, 42):
        random.seed(semilla)
        matriz, num_maq, num_job, cota_superior, cota_inferior = am.leer_instancia_taillard(INSTANCIA)
        sol, mk, traza = am.ejecutar_algoritmo_memetico(30, 0.85, 0.20, 50, matriz,
                                                        num_maq, num_job)
        assert es_permutacion(sol, num_job), f"MA devolvió una secuencia inválida: {sol}"
        real = makespan_referencia(sol, matriz, num_maq)
        assert real == mk, f"MA semilla {semilla}: reporta {mk} pero la secuencia vale {real}"
        assert mk >= cota_inferior, f"MA semilla {semilla}: {mk} bajo la cota inferior"
        assert traza[-1][1] == mk and traza == sorted(traza), "la traza no es coherente"
        print(f"  [OK] MA semilla {semilla}: reportado={mk} recalculado={real} "
              f"UB={cota_superior} hallado en gen {traza[-1][0]}")


def test_reproducibilidad():
    """La misma semilla produce exactamente la misma corrida."""
    matriz, num_maq, num_job, _, _ = ag.leer_instancia_taillard(INSTANCIA)
    corridas = []
    for _ in range(2):
        random.seed(123)
        corridas.append(ag.ejecutar_algoritmo_genetico(20, 0.85, 0.20, 30, matriz,
                                                       num_maq, num_job))
    assert corridas[0] == corridas[1], "la misma semilla dio resultados distintos"
    print("  [OK] reproducibilidad: misma semilla, misma solución, misma traza")


def test_renovacion_conserva_elite_tamano_y_permutaciones():
    """renovar_poblacion preserva el élite, el tamaño y la validez de permutaciones."""
    random.seed(8)
    n_job = 15
    for tam in (5, 20, 50):
        pob = [random.sample(range(n_job), n_job) for _ in range(tam)]
        fit = list(range(100, 100 + tam))
        elite_antes = list(pob[0])
        fit_elite_antes = fit[0]

        def evaluador(ind):
            return sum((i + 1) * job for i, job in enumerate(ind))

        pob_ren, fit_ren = renovar_poblacion(pob, fit, n_job, evaluador, frac_renovacion=0.20)
        assert len(pob_ren) == tam and len(fit_ren) == tam, "el tamaño de población cambió"
        for ind in pob_ren:
            assert es_permutacion(ind, n_job), "individuo no es permutación válida"
        assert fit_ren == sorted(fit_ren), "la población no quedó ordenada"
        assert elite_antes in pob_ren, "el élite original se perdió de la población"
        assert fit_ren[0] <= fit_elite_antes, "el mejor fitness empeoró tras renovación"
    print("  [OK] renovación: conserva élite, tamaño y permutaciones válidas")


def test_renovacion_protege_poblacion_unitaria():
    """Con población unitaria (tam=1), renovar_poblacion no reemplaza el único élite."""
    n_job = 10
    ind = list(range(n_job))
    fit = [42]
    pob_ren, fit_ren = renovar_poblacion([ind], fit, n_job, lambda x: 999, frac_renovacion=0.5)
    assert len(pob_ren) == 1 and pob_ren[0] == ind and fit_ren == [42]
    print("  [OK] renovación: protege población unitaria sin modificar el élite")


def test_renovacion_se_activa_tras_estancamiento():
    """El ciclo evolutivo activa la renovación tras paciencia_renovacion y reinicia contador."""
    random.seed(9)
    matriz, num_maq, num_job, _, _ = ag.leer_instancia_taillard(INSTANCIA)
    activaciones = []

    import pfsp.ga as ga_mod
    orig_ga_renovar = ga_mod.renovar_poblacion

    def interceptor(*args, **kwargs):
        activaciones.append(len(activaciones))
        return orig_ga_renovar(*args, **kwargs)

    ga_mod.renovar_poblacion = interceptor
    try:
        sol, mk, traza = ag.ejecutar_evolutivo(
            20, 0.85, 0.20, 35, matriz, num_maq, num_job,
            usar_bl=False, paciencia_renovacion=10, frac_renovacion=0.20, mostrar_progreso=False
        )
        assert es_permutacion(sol, num_job)
        assert len(activaciones) == 3, f"se esperaban 3 activaciones, hubo {len(activaciones)}"
    finally:
        ga_mod.renovar_poblacion = orig_ga_renovar
    print(f"  [OK] renovación: se activó {len(activaciones)} veces ante estancamiento en 35 gens")


def test_renovacion_con_reparador():
    """renovar_poblacion aplica el reparador a los mutantes del élite preservando invariantes."""
    random.seed(10)
    n_job = 10
    tam = 20
    pob = [random.sample(range(n_job), n_job) for _ in range(tam)]
    fit = list(range(100, 100 + tam))
    reparaciones = []

    def mi_reparador(ind):
        reparaciones.append(list(ind))
        return list(reversed(ind))

    def evaluador(ind):
        return sum((i + 1) * job for i, job in enumerate(ind))

    pob_ren, fit_ren = renovar_poblacion(
        pob, fit, n_job, evaluador, frac_renovacion=0.20, reparador=mi_reparador
    )
    assert len(reparaciones) == 2, f"se esperaban 2 llamadas a reparador, hubo {len(reparaciones)}"
    assert len(pob_ren) == tam and len(fit_ren) == tam
    for ind in pob_ren:
        assert es_permutacion(ind, n_job)
    print("  [OK] renovación con reparador: aplica reparador a mutantes del élite e invariantes OK")


def test_neh_con_orden_personalizado():
    """neh(..., orden=X) produce permutación válida y neh() sin orden reproduce exacto."""
    matriz, num_maq, num_job, _, _ = ag.leer_instancia_taillard(INSTANCIA)
    base = neh(matriz, num_maq, num_job)
    orden = orden_neh(matriz, num_maq, num_job)
    con_orden = neh(matriz, num_maq, num_job, orden=orden)
    assert base == con_orden, "neh() sin orden difiere de neh(..., orden=orden_neh(...))"

    orden_rev = list(reversed(orden))
    sec_rev = neh(matriz, num_maq, num_job, orden=orden_rev)
    assert es_permutacion(sec_rev, num_job)
    print("  [OK] NEH con orden personalizado: permutación válida y regresión idéntica")


if __name__ == "__main__":
    pruebas = [
        test_makespan_vs_oraculo,
        test_optimo_conocido_fuerza_bruta,
        test_costos_insercion_equivalen_a_recalcular,
        test_busqueda_local_acelerada_equivale_a_la_ingenua,
        test_busqueda_local_no_empeora,
        test_neh_construye_permutacion_valida,
        test_reemplazo_conserva_los_mejores,
        test_operadores_preservan_permutacion,
        test_ag_reporta_makespan_real,
        test_memetico_reporta_makespan_real,
        test_reproducibilidad,
        test_renovacion_conserva_elite_tamano_y_permutaciones,
        test_renovacion_protege_poblacion_unitaria,
        test_renovacion_se_activa_tras_estancamiento,
        test_renovacion_con_reparador,
        test_neh_con_orden_personalizado,
    ]
    for prueba in pruebas:
        print(f"\n{prueba.__name__}:")
        prueba()
    print(f"\nTodos los chequeos pasaron ({len(pruebas)} pruebas).")
