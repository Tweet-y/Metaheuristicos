## pip install -r requirements.txt
import numpy as np 
import time 
import sys
import csv
import os

if len(sys.argv) == 8:
    entrada = entrada = sys.argv[1]
    tam_pobla = int(sys.argv[2])
    prob_c = float(sys.argv[3])
    prob_m = float(sys.argv[4])
    iteracion = int(sys.argv[5])
    semilla = int(sys.argv[6])
    salida = sys.argv[7]
    
    print(f"Parámetros cargados: {entrada}, {tam_pobla}, {prob_c}, {prob_m}, {iteracion}, {semilla}")
    
else:
    print(f"Error en la entrada de los parametros")
    print("Uso: python3 ag.py DatosEntrada TamanoPobla ProbaCruza ProbaMuta NumIteraciones Semilla Resultado.csv")
    print("donde:")
    print(" - Semilla: valor entero positivo [ejem: 1]")
    print(" - Tamano_Pobla: valor entero positivo [ejem: 20]")
    print(" - %_Cruza: valor real positivo [ejem: 0.95]")
    print(" - %_Muta: valor de Tau entero positivo [ejem: 0.05]")
    print(" - NroIteraciones: valor entero positivo [ejem: 100]")
    print(" - DatosEntrada: nombre archivo con los datos del problema [ejem: ins_20_5_00.txt]")
    print(" - ArchivoSalida: nombre archivo con los resultados de la solución del problema [ejem: ins_20_5_00_s1.csv]")
    sys.exit(1)
    
with open(entrada, "r") as f:
    primera_linea = f.readline().strip().split()
    num_job = int(primera_linea[0])
    num_maq = int(primera_linea[1])
    lim_inf = int(primera_linea[3])
    lim_sup = int(primera_linea[4])
    matriz = np.loadtxt(f, dtype=int)
print(f"P1: {num_job}, P2: {num_maq}, P3: {lim_inf}, P4: {lim_sup}")
print(matriz)

np.random.seed(semilla)

## Guardar resultado

def guardar_resultado_csv(ruta_csv, instancia, semilla, tam_pobla, prob_c, prob_m,                                                                                                                
                            iteraciones, mejor_mk, cota_ref, rpd, tiempo_seg, mejor_sol):                                                                                                            
    existe = os.path.exists(ruta_csv)                                                                                                                                                             

    with open(ruta_csv, mode="a", newline="", encoding="utf-8") as f:                                                                                                                             
        writer = csv.writer(f, delimiter=";")                                                                                                                                                     
        if not existe:                                                                                                                                                                            
            writer.writerow([                                                                                                                                                                     
                "Instancia", "Semilla", "Poblacion", "Prob_Cruce", "Prob_Mutacion",                                                                                                               
                "Iteraciones", "Makespan", "Upper_Bound", "RPD_%", "Tiempo_Seg", "Mejor_Secuencia"                                                                                                
            ])                                                                                                                                                                                    

        secuencia_str = "-".join(map(str, mejor_sol))                                                                                                                                             
        writer.writerow([                                                                                                                                                                         
            instancia, semilla, tam_pobla, prob_c, prob_m,                                                                                                                                        
            iteraciones, mejor_mk, cota_ref, f"{rpd:.2f}", f"{tiempo_seg:.4f}", secuencia_str                                                                                                     
        ])                                                                                                                                                                                        
    print(f"\n[OK] Resultado guardado exitosamente en: {ruta_csv}")  

def inicializar_poblacion(f, c):
    pobla = np.tile(np.arange(c), (f, 1))
    for i in range(f):
        np.random.shuffle(pobla[i])
    return pobla

poblacion = inicializar_poblacion(tam_pobla, num_job)
print("Población Inicial:")
print(poblacion)

tiempo_proceso_fin = time.process_time()

def calcular_makespan(individuo, matriz, num_maq):                                                                                                                                                
        tiempos_maquinas = np.zeros(num_maq, dtype=int)                                                                                                                                               
        for trabajo in individuo:                                                                                                                                                                     
            tiempos_maquinas[0] += matriz[0, trabajo]                                                                                                                                                 
            for m in range(1, num_maq):                                                                                                                                                               
                if tiempos_maquinas[m] < tiempos_maquinas[m - 1]:                                                                                                                                     
                    tiempos_maquinas[m] = tiempos_maquinas[m - 1]                                                                                                                                     
                tiempos_maquinas[m] += matriz[m, trabajo]                                                                                                                                             
        return tiempos_maquinas[-1]                                                                                                                                                                   

def evaluar_poblacion(poblacion, matriz, num_maq):                                                                                                                                                
    fitness = np.zeros(len(poblacion), dtype=int)                                                                                                                                                 
    for i, ind in enumerate(poblacion):                                                                                                                                                           
        fitness[i] = calcular_makespan(ind, matriz, num_maq)                                                                                                                                      
    return fitness 

fitness_poblacion = evaluar_poblacion(poblacion, matriz, num_maq)                                                                                                                                 
print("Fitness (Makespan) de cada individuo:")                                                                                                                                                    
print(fitness_poblacion)                                                                                                                                                                          
print(f"Mejor inicial: {np.min(fitness_poblacion)}")

def seleccion_torneo(poblacion, fitness, k=2):                                                                                                                                                    
    indices_aspirantes = np.random.randint(0, len(poblacion), size=k)                                                                                                                             
    mejor_idx = indices_aspirantes[np.argmin(fitness[indices_aspirantes])]                                                                                                                        
    return poblacion[mejor_idx].copy()

## selección
padre1 = seleccion_torneo(poblacion, fitness_poblacion)                                                                                                                                           
padre2 = seleccion_torneo(poblacion, fitness_poblacion)                                                                                                                                           
print("Padre 1 seleccionado:", padre1, "Makespan:", calcular_makespan(padre1, matriz, num_maq))                                                                                                   
print("Padre 2 seleccionado:", padre2, "Makespan:", calcular_makespan(padre2, matriz, num_maq)) 

## Cruce

def cruce_ox(padre1, padre2, prob_c):                                                                                                                                                             
    # Si no ocurre el cruce por probabilidad, los hijos son copias de los padres                                                                                                                  
    if np.random.rand() > prob_c:                                                                                                                                                                 
        return padre1.copy(), padre2.copy()                                                                                                                                                       

    n = len(padre1)                                                                                                                                                                               
    # Seleccionar dos puntos de corte distintos                                                                                                                                                   
    c1, c2 = sorted(np.random.choice(n, size=2, replace=False))                                                                                                                                   

    def generar_hijo(p1, p2):                                                                                                                                                                     
        hijo = np.full(n, -1, dtype=int)                                                                                                                                                          
        # Copiar segmento de p1                                                                                                                                                                   
        hijo[c1:c2 + 1] = p1[c1:c2 + 1]                                                                                                                                                           

        # Elementos ya presentes en el hijo                                                                                                                                                       
        en_hijo = set(hijo[c1:c2 + 1])                                                                                                                                                            

        # Recorrer p2 a partir de c2 + 1 en forma circular                                                                                                                                        
        pos_hijo = (c2 + 1) % n                                                                                                                                                                   
        for i in range(n):                                                                                                                                                                        
            idx_p2 = (c2 + 1 + i) % n                                                                                                                                                             
            gen = p2[idx_p2]                                                                                                                                                                      
            if gen not in en_hijo:                                                                                                                                                                
                hijo[pos_hijo] = gen                                                                                                                                                              
                pos_hijo = (pos_hijo + 1) % n                                                                                                                                                     
        return hijo                                                                                                                                                                               

    hijo1 = generar_hijo(padre1, padre2)                                                                                                                                                          
    hijo2 = generar_hijo(padre2, padre1)                                                                                                                                                          
    return hijo1, hijo2 

hijo1, hijo2 = cruce_ox(padre1, padre2, prob_c)                                                                                                                                                   
print("Hijo 1:", hijo1, "Makespan:", calcular_makespan(hijo1, matriz, num_maq))                                                                                                                   
print("Hijo 2:", hijo2, "Makespan:", calcular_makespan(hijo2, matriz, num_maq))     

## Mutación

def mutacion_swap(individuo, prob_m):                                                                                                                                                             
    # mutar solo si se cumple la probabilidad                                                                                                                                                     
    if np.random.rand() < prob_m:                                                                                                                                                                 
        mutado = individuo.copy()                                                                                                                                                                 
        n = len(mutado)                                                                                                                                                                           
        i, j = np.random.choice(n, size=2, replace=False)                                                                                                                                         
        mutado[i], mutado[j] = mutado[j], mutado[i]                                                                                                                                               
        return mutado                                                                                                                                                                             
    return individuo.copy()  

hijo1_mutado = mutacion_swap(hijo1, prob_m=1.0)  # Forzamos 1.0 solo para ver el swap                                                                                                             
print("Hijo 1 original:", hijo1)                                                                                                                                                                  
print("Hijo 1 mutado:  ", hijo1_mutado, "Makespan:", calcular_makespan(hijo1_mutado, matriz, num_maq))  

## Algoritmo Genético

def ejecutar_algoritmo_genetico(tam_pobla, prob_c, prob_m, iteraciones, matriz, num_maq, num_job):                                                                                                
    # 1. Inicializar población                                                                                                                                                                    
    poblacion = inicializar_poblacion(tam_pobla, num_job)                                                                                                                                         
    fitness = evaluar_poblacion(poblacion, matriz, num_maq)                                                                                                                                       

    # Identificar el mejor inicial                                                                                                                                                                
    idx_mejor = np.argmin(fitness)                                                                                                                                                                
    mejor_solucion = poblacion[idx_mejor].copy()                                                                                                                                                  
    mejor_makespan = fitness[idx_mejor]                                                                                                                                                           

    print(f"Generación 0: Mejor Makespan = {mejor_makespan}")                                                                                                                                     

    # 2. Bucle generacional                                                                                                                                                                       
    for gen in range(1, iteraciones + 1):                                                                                                                                                         
        nueva_poblacion = []                                                                                                                                                                      

        # Elitismo: preservamos al mejor individuo de la generación                                                                                                                               
        idx_elite = np.argmin(fitness)                                                                                                                                                            
        nueva_poblacion.append(poblacion[idx_elite].copy())                                                                                                                                       

        # Generar descendencia hasta completar el tamaño de población                                                                                                                             
        while len(nueva_poblacion) < tam_pobla:                                                                                                                                                   
            padre1 = seleccion_torneo(poblacion, fitness)                                                                                                                                         
            padre2 = seleccion_torneo(poblacion, fitness)                                                                                                                                         

            hijo1, hijo2 = cruce_ox(padre1, padre2, prob_c)                                                                                                                                       

            hijo1 = mutacion_swap(hijo1, prob_m)                                                                                                                                                  
            hijo2 = mutacion_swap(hijo2, prob_m)                                                                                                                                                  

            nueva_poblacion.append(hijo1)                                                                                                                                                         
            if len(nueva_poblacion) < tam_pobla:                                                                                                                                                  
                nueva_poblacion.append(hijo2)                                                                                                                                                     

        # Actualizar población y evaluar                                                                                                                                                          
        poblacion = np.array(nueva_poblacion)                                                                                                                                                     
        fitness = evaluar_poblacion(poblacion, matriz, num_maq)                                                                                                                                   

        # Actualizar mejor histórico si hubo mejora                                                                                                                                               
        min_gen = np.min(fitness)                                                                                                                                                                 
        if min_gen < mejor_makespan:                                                                                                                                                              
            mejor_makespan = min_gen                                                                                                                                                              
            mejor_solucion = poblacion[np.argmin(fitness)].copy()                                                                                                                                 

        # Imprimir avance cada 10 generaciones o en la última                                                                                                                                     
        if gen % 10 == 0 or gen == iteraciones:                                                                                                                                                   
            print(f"Generación {gen}/{iteraciones}: Mejor Makespan = {mejor_makespan}")                                                                                                           

    return mejor_solucion, mejor_makespan  

tiempo_inicio = time.time()                                                                                                                                                                       

mejor_sol, mejor_mk = ejecutar_algoritmo_genetico(                                                                                                                                                
    tam_pobla, prob_c, prob_m, iteracion, matriz, num_maq, num_job                                                                                                                                )                                                                                                                                                                                                 

tiempo_fin = time.time()                                                                                                                                                                          
tiempo_total = tiempo_fin - tiempo_inicio                                                                                                                                                         

# Cálculo del Relative Percentage Deviation (RPD) con respecto al Upper Bound de Taillard                                                                                                         
rpd = ((mejor_mk - lim_inf) / lim_inf) * 100                                                                                                                                                      

print("\n" + "=" * 50)                                                                                                                                                                            
print("RESULTADOS FINALES ALGORITMO GENÉTICO:")                                                                                                                                                   
print(f"Mejor secuencia encontrada: {mejor_sol}")                                                                                                                                                 
print(f"Makespan obtenido:          {mejor_mk}")                                                                                                                                                  
print(f"Upper Bound conocido:       {lim_inf}")                                                                                                                                                   
print(f"RPD (% de error):           {rpd:.2f}%")                                                                                                                                                  
print(f"Tiempo de ejecución:        {tiempo_total:.4f} segundos")                                                                                                                                 
print("=" * 50)      

## Guardar resultado
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