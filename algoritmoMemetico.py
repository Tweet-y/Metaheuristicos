## pip install -r requirements.txt
import numpy as np 
import time 
import sys
import csv
import os
import random

if len(sys.argv) == 8:
    entrada = sys.argv[1]
    tam_pobla = int(sys.argv[2])
    prob_c = float(sys.argv[3])
    prob_m = float(sys.argv[4])
    iteracion = int(sys.argv[5])
    semilla = int(sys.argv[6])
    salida = sys.argv[7]
    
    print(f"Parámetros cargados (Memético): {entrada}, Pob={tam_pobla}, Pc={prob_c}, Pm={prob_m}, Iter={iteracion}, Semilla={semilla}")
else:
    print("Error en la entrada de los parámetros")
    print("Uso: python3 algoritmoMemetico.py DatosEntrada TamanoPobla ProbaCruza ProbaMuta NumIteraciones Semilla Resultado.csv")
    sys.exit(1)

with open(entrada, "r") as f:
    primera_linea = f.readline().strip().split()
    num_job = int(primera_linea[0])
    num_maq = int(primera_linea[1])
    lim_inf = int(primera_linea[3])
    lim_sup = int(primera_linea[4])
    matriz = np.loadtxt(f, dtype=int).tolist()

print(f"Instancia: {num_job} trabajos, {num_maq} máquinas | Upper Bound: {lim_inf}, Lower Bound: {lim_sup}")

np.random.seed(semilla)
random.seed(semilla)

## Guardar resultado en CSV
def guardar_resultado_csv(ruta_csv, instancia, semilla, tam_pobla, prob_c, prob_m,                                                                                                                
                          iteraciones, mejor_mk, cota_ref, rpd, tiempo_seg, mejor_sol):                                                                                                            
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

def inicializar_poblacion(f, c):
    pobla = [list(map(int, np.random.permutation(c))) for _ in range(f)]
    return pobla

def calcular_makespan(individuo, matriz, num_maq):                                                                                                                                                
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
    return [calcular_makespan(ind, matriz, num_maq) for ind in poblacion]

def seleccion_torneo(poblacion, fitness, k=2):                                                                                                                                                    
    indices = random.sample(range(len(poblacion)), k)                                                                                                                             
    mejor_idx = min(indices, key=lambda i: fitness[i])                                                                                                                        
    return list(poblacion[mejor_idx])

## Cruce OX (Order Crossover)
def cruce_ox(padre1, padre2, prob_c):                                                                                                                                                             
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

## Mutaciones
def mutacion_swap(individuo, prob_m):                                                                                                                                                             
    if random.random() < prob_m:                                                                                                                                                                 
        mutado = list(individuo)                                                                                                                                                                 
        n = len(mutado)                                                                                                                                                                           
        i, j = random.sample(range(n), 2)                                                                                                                                         
        mutado[i], mutado[j] = mutado[j], mutado[i]                                                                                                                                               
        return mutado                                                                                                                                                                             
    return list(individuo)  

def mutacion_insercion(individuo, prob_m):
    if random.random() < prob_m:
        mutado = list(individuo)
        n = len(mutado)
        i, j = random.sample(range(n), 2)
        trabajo = mutado.pop(i)
        mutado.insert(j, trabajo)
        return mutado
    return list(individuo)

def mutar_individuo(individuo, prob_m):
    if random.random() < 0.5:
        return mutacion_swap(individuo, prob_m)
    return mutacion_insercion(individuo, prob_m)

## Búsqueda Local (Componente Memético: Insertion Local Search)
def busqueda_local_insercion(individuo, matriz, num_maq, max_iter=20):
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

## Algoritmo Memético
def ejecutar_algoritmo_memetico(tam_pobla, prob_c, prob_m, iteraciones, matriz, num_maq, num_job, freq_bl=1):
    poblacion = inicializar_poblacion(tam_pobla, num_job)                                                                                                                                         
    fitness = evaluar_poblacion(poblacion, matriz, num_maq)                                                                                                                                       

    idx_mejor = min(range(len(fitness)), key=lambda i: fitness[i])
    mejor_solucion = list(poblacion[idx_mejor])
    mejor_makespan = fitness[idx_mejor]                                                                                                                                                           

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

        # Generar descendencia
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

        if gen % 100 == 0 or gen == iteraciones:
            print(f"Generación {gen}/{iteraciones}: Mejor Makespan = {mejor_makespan}")

        # Criterio de parada temprana si se alcanza la cota óptima
        if mejor_makespan <= lim_inf:
            print(f"\n[!] Óptimo global ({lim_inf}) alcanzado anticipadamente en la generación {gen}!")
            break

    return mejor_solucion, mejor_makespan

tiempo_inicio = time.time()                                                                                                                                                                       

mejor_sol, mejor_mk = ejecutar_algoritmo_memetico(                                                                                                                                                
    tam_pobla, prob_c, prob_m, iteracion, matriz, num_maq, num_job
)                                                                                                                                                                                                 

tiempo_fin = time.time()                                                                                                                                                                          
tiempo_total = tiempo_fin - tiempo_inicio                                                                                                                                                         

rpd = ((mejor_mk - lim_inf) / lim_inf) * 100                                                                                                                                                      

print("\n" + "=" * 50)                                                                                                                                                                            
print("RESULTADOS FINALES ALGORITMO MEMÉTICO:")  
print(f"Semilla:                    {semilla}")                                                                                                                                                 
print(f"Mejor secuencia encontrada: {mejor_sol}")                                                                                                                                                 
print(f"Makespan obtenido:          {mejor_mk}")                                                                                                                                                  
print(f"Upper Bound conocido:       {lim_inf}")                                                                                                                                                   
print(f"RPD (% de error):           {rpd:.2f}%")                                                                                                                                                  
print(f"Tiempo de ejecución:        {tiempo_total:.4f} segundos")                                                                                                                                 
print("=" * 50)      

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
