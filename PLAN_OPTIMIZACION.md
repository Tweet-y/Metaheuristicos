# Plan de optimización: acercar AG y memético al Upper Bound

Objetivo: reducir makespan y RPD con presupuesto comparable, preservando correctitud y reproducibilidad.

**Sólo revisión y planificación. Implementación del paso 1 retirada: código y pruebas restaurados. Implementación pendiente de encargo explícito.**

Prioridad confirmada por usuario: **3 → 2A (contadores y tiempos) → 1 → 2B (límite temporal) → 4 → 5 → 6**. Se conserva numeración original para identificar cada acción. La renovación poblacional es la principal hipótesis de mejora aún no probada; será el primer experimento. No necesita esperar instrumentación de 2A.

**Próximo encargo propuesto: sólo paso 3.** Este documento no autoriza implementarlo; se requiere petición explícita.

## Diagnóstico base — revisión bfa5af7, 2026-09-18

Referencia: `local/handoff.md`, sección 2; comprobada contra código base, CSV versionado y `/tmp/chk.py` antes de probar variante retirada. Instrumentación: semilla 1, población 60, Pc=0,85, Pm=0,20, 300 generaciones, memético. Resultados de esa semilla no representan tasas sobre todas las instancias. `local/validar_paso1.py` es archivo histórico: no corre sobre HEAD, porque requiere retorno de tres valores de variante retirada.

| Instancia | UB del archivo | RPD medio AG | RPD medio memético | Corridas meméticas que alcanzan UB |
|---|---:|---:|---:|---:|
| 20×5 | 1278 | 0,57% | 0,06% | 9/10 |
| 50×10 | 3025 | 3,26% | 0,60% | 0/10 |
| 100×10 | 5770 | 1,28% | 0,45% | 0/10 |

Tabla conserva porcentajes publicados: promedio de columna `RPD_%` ya redondeada. Recalculando desde makespan y UB, medias AG de 20×5 y 100×10 son 0,56338% y 1,27210%. Diferencia de redondeo, no cambio de desempeño. Nuevos análisis deben agregar RPD sin redondear y redondear sólo presentación.

| Medida de búsqueda local | 50×10 | 100×10 |
|---|---:|---:|
| Llamadas | 148 | 79 |
| Truncadas sin certificar convergencia | 7 (4,7%) | 8 (10,1%) |
| Salidas truncadas que todavía admitían mejora | 6 | 8 |
| Pasadas medias por llamada | 3,71 | 4,77 |
| Movimientos aceptados medios por llamada | 2,76 | 3,87 |

- `ya_optimizados` significa operativamente «no volver a aplicar BL», incluso tras truncamiento. Nombre y comentario sugieren una convergencia que no siempre se comprobó; no producen makespan falsos ni permutaciones inválidas. Cambiar esta política modifica asignación del presupuesto de búsqueda y requiere evaluar costo/beneficio. Una salida truncada puede ya ser óptimo local: explica diferencia entre 7 truncamientos y 6 salidas mejorables en 50×10.
- `/tmp/chk.py` etiqueta como `movs/llamada` el número de **pasadas**. Una llamada convergente incluye pasada final sin movimiento. Promedios de movimientos corregidos: 408/148 y 306/79.
- Empates favorecen padres. Hubo **233/300 generaciones sin sobreviviente nuevo en 50×10 y 271/300 en 100×10**. Se compara población resultante contra padres que entran al reemplazo; no se cuentan mejoras locales de padres como renovación por hijos.
- AG no mejora NEH en 9/10 corridas de 20×5 y 100×10.
- Evaluaciones de hijos repetidas: aproximadamente 64% en 50×10 y 26% en 100×10, con semilla 1.
- Reaplicar búsqueda local no mejoró las 20 soluciones finales medianas/grandes examinadas.
- Pilotos que completaron descenso local o favorecieron hijos en empates dieron resultados mixtos. Ningún cambio garantiza mejora por sí solo.
- Revisión anterior: 60 soluciones guardadas verificadas; 11/11 pruebas existentes aprobadas. Esta actualización documental no implica nueva ejecución de esa suite.
- `ejecutar_comparativa.py` no pasa `cota_superior`: **ambos algoritmos corren las 300 generaciones**. Asimetría de parada existe sólo en CLI. Corregirla no exige repetir resultados publicados.

UB = referencia incluida en instancia. Alcanzarlo no certifica optimalidad; RPD negativo es válido si solución mejora referencia.

## Acciones por identificador — orden de trabajo: 3 → 2A → 1 → 2B → 4 → 5 → 6

### 1. Evaluar política de reoptimización local — pospuesta

- Encuadre: ajuste heurístico de presupuesto, no reparación de validez de resultados. Makespan, permutaciones y reproducibilidad ya cumplen sus pruebas. Documentar significado de caché es higiene semántica; reanudar búsquedas cambia comportamiento.
- Evaluar aisladamente distinguir convergencia vs límite de pasadas y guardar en `ya_optimizados` únicamente convergencias comprobadas: recorrido completo del vecindario sin mejora.
- Devolver siempre `(solucion, makespan, convergio)`. Sin flag ni retorno alternativo: adaptar motor y dos consumidores existentes en tests; re-export no requiere cambios.
- Conservar tope `max_iter=20`. Una pasada acepta como máximo un movimiento; convergencia requiere pasada completa sin mejora.
- Continuación usa solución mejorada ya almacenada en población. Si permanece elegible y sin certificado, próxima aplicación retoma desde allí: puede gastar hasta 20 movimientos adicionales. **Tiempo por generación puede aumentar**; medir y reportar esta regresión esperada, sin prometer magnitud.
- Reanudaciones consumen cupos del límite `bl_muestra + 1` (dos por aplicación actual). Un individuo truncado puede desplazar a otros candidatos en aplicaciones posteriores: posible menor cobertura de individuos por BL, además del costo temporal. Medir llamadas, entradas distintas y reanudaciones; entradas distintas cuentan permutaciones, no identidades persistentes de individuos.
- **Excluir ordenamiento de generación 1.** Conservar orden inicial actual. Único componente activo de variante retirada en 20×5, donde regresó calidad observada sin beneficio aislado demostrado.
- Añadir prueba que detecte mejoras pendientes tras truncamiento y evite certificarlas como óptimo local.
- Beneficio de reoptimización sola sigue sin aislarse en 50×10 y 100×10: prueba anterior mezcló esta política con ordenamiento. No darle prioridad por etiqueta de «corrección». Si se incorpora como higiene, declarar cambio de presupuesto y costo; no venderlo como mejora de RPD.

### 2. Medir con presupuesto comparable

**2A. Medición mínima, después del primer experimento de renovación.**

- Dos contadores de llamadas: `llamadas_makespan` y `llamadas_costos_insercion`. Contar invocaciones efectivas durante corrida, incluidas inicialización, NEH y BL; excluir verificaciones externas posteriores.
- Contar visitas a celdas máquina/posición: `nm_makespan = suma(largo * num_maq)` y `nm_insercion = suma((2 * largo + largo + 1) * num_maq)`. En inserción, `largo = len(secuencia)` sin trabajo extra: dos barridos de largo×m y combinación de (largo+1)×m.
- Reportar ambos y `nm_total = nm_makespan + nm_insercion`. Unidad comparable: visitas de los barridos, no instrucciones exactas, evaluaciones equivalentes de makespan ni segundos de CPU. Combinación realiza más operaciones por celda; igualdad de visitas no implica igualdad temporal.
- Si contadores viven a nivel módulo, llamar `reiniciar_contadores()` al entrar a `ejecutar_evolutivo`, antes de inicialización. Contar makespan sólo dentro de `calcular_makespan`; `evaluar_poblacion` delega y no incrementa. Llamadas directas de tests no deben contaminar siguiente corrida.
- Registrar segundos transcurridos con `time.perf_counter()`, generación y mejor makespan, junto con contadores acumulados. Medición empieza antes de inicializar población; incluye NEH y BL.
- Mantener salida y traza existentes; telemetría adicional optativa en salida separada. Sin nuevas dependencias ni sistema genérico de instrumentación.

**2B. Presupuesto temporal completo, después de 3, 2A y evaluación aislada de 1.**

- Motor recibe `tiempo_max=None`; ausencia conserva modo por generaciones. Usar tiempo transcurrido monótono, no llamarlo tiempo de CPU.
- BL recibe `deadline=None` opcional por keyword. Default sin límite temporal conserva equivalencia con búsqueda ingenua y comportamiento actual de `max_iter`.
- Comprobar deadline antes de cada evaluación de vecindario. Actualizar solución y makespan juntos antes de atender siguiente interrupción. Devolver mejor solución válida disponible; interrupción no certifica convergencia.
- Límite es cooperativo: puede sobrepasarse por operación ya iniciada. Incluir inicialización en tiempo medido y devolver mejor individuo evaluado si presupuesto vence allí.
- Conservar reproducibilidad exacta por generaciones, excluyendo tiempos. Modo temporal no garantiza idéntico recorrido entre ejecuciones.
- Comparar presupuestos temporales con misma política de parada por UB en ambos algoritmos.

**Corrección CLI independiente, pendiente; no depende de 2B.** Alinear CLI para que AG también reciba UB. Wrapper AG añade parámetro opcional al final, sin romper llamadas existentes. Batería fija continúa sin UB, 300 generaciones; no regenerar CSV publicados sólo por fix de CLI. Entregar este ajuste por separado del paso 1.

### 3. Introducir renovación controlada

- Primer experimento: contrasta hipótesis de estancamiento observada en 233/300 y 271/300 generaciones sin sobreviviente nuevo, con 64% y 26% de hijos repetidos. Evidencia justifica probar renovación; todavía no demuestra que reduzca RPD.
- Preservar mejor individuo y mejor solución histórica.
- Tras estancamiento, reemplazar parte de peores individuos por perturbaciones y soluciones nuevas.
- Punto inicial experimental: **30 generaciones sin mejora → renovar 20%**.
- Insertarlos directamente; competencia elitista inmediata podría descartarlos todos.
- Medir renovación efectiva y calidad. Parámetros iniciales son hipótesis para validar.
- Mantener política BL, orden inicial, cruces y mutaciones de referencia. No mezclar con paso 1, desempate a favor de hijos ni cambios de parámetros.
- Medir con runner de experimento externo: generaciones sin renovación, hijos repetidos, makespan, RPD y tiempo. No convertir ese runner en instrumentación permanente de 2A antes de probar hipótesis.

### 4. Potenciar memético

- Probar destrucción/reconstrucción: retirar 4 trabajos, reinsertarlos usando `costos_insercion` y aplicar descenso local.
- Reutilizar aceleración existente y respetar presupuesto temporal.
- Evaluar después, como cambio separado, búsqueda local sobre pocos hijos antes del reemplazo.

### 5. Potenciar AG

- Probar pequeña fracción de variantes NEH junto con población aleatoria.
- Ante estancamiento, probar mutación con varias inserciones.
- Mantener AG sin búsqueda local para conservar distinción experimental frente al memético.
- Calibrar parámetros propios: barrido previo mostró preferencias distintas entre AG y memético. Combinar valores prometedores requiere nueva validación.

### 6. Recuperar tiempo desperdiciado

- Reutilizar fitness de permutaciones repetidas mediante caché acotada y limitada a una instancia/corrida.
- Medir beneficio después de introducir diversidad; frecuencia de repeticiones puede cambiar.
- Comprobar que caché no consume aleatoriedad ni altera resultados bajo presupuesto por generaciones.

## Restricciones del próximo encargo propuesto — sólo paso 3

- Revisar estado actual antes de editar; repetir diagnóstico si cambió implementación.
- Diff mínimo. Sin dependencias nuevas ni abstracciones innecesarias.
- Preservar resultados existentes; experimentos en archivos separados.
- Primer cambio funcional sólo renovación controlada. Medición permanente, reoptimización y límites temporales se evalúan después, por separado.
- No introducir ordenamiento inicial, reconstrucción, variantes NEH ni caché de fitness.
- No presuponer mejora del RPD por renovar población. Esta revisión modifica documentos, no algoritmos.

## Validación y entrega

Para primer experimento, paso 3:

1. Reutilizar pruebas existentes. Añadir únicamente invariantes nuevos: renovación conserva élite, tamaño y permutaciones; se activa tras estancamiento y reinicia contador de espera. Proteger población de un individuo: no reemplazar único élite.
2. Comparar referencia y variante de ambos algoritmos en tres instancias actuales, semillas 1–10, población 60, Pc=0,85, Pm=0,20 y 300 generaciones. Corridas secuenciales, sin sobrescribir CSV existentes.
3. Registrar renovación efectiva, repeticiones, RPD sin redondeo intermedio y tiempo. Bajar estancamiento sin mejorar calidad/costo no basta para declarar éxito.
4. Entregar diff y resultados reproducibles. Detenerse antes de 2A; ningún cambio funcional autorizado por esta revisión documental.

Para paso 1, posteriormente y sin sort:

1. Ejecutar pruebas existentes: `python3 test_makespan.py`.
2. Añadir regresiones de estado tras truncamiento/convergencia y reanudación de individuo truncado en motor. No añadir ordenamiento ni tests que lo impongan.
3. Reutilizar pruebas existentes: `test_reemplazo_conserva_los_mejores`, `test_reproducibilidad`, equivalencia de Taillard, permutaciones y makespan. No duplicarlas.
4. Comparar memético con/sin reoptimización en tres instancias actuales, semillas 1–10, población 60, Pc=0,85, Pm=0,20 y 300 generaciones completas. Usar misma revisión inmediata anterior como base en ambos brazos: no mezclar cambios de renovación. AG debe coincidir exactamente con esa base en solución, makespan y traza. Mismo entorno; corridas secuenciales. Registrar configuración y versión.
5. Reportar makespan, RPD sin redondeo intermedio, tiempo, llamadas BL, truncamientos, entradas distintas y reanudaciones. Medir costo y consumo de cupos al retomar búsquedas; igualdad de generaciones no implica igualdad de tiempo.
6. Entregar diff, resumen y comandos reproducibles. Decidir continuidad por calidad/costo. Si se conserva sólo como higiene semántica, declararlo explícitamente con costo medido; no tratarlo como requisito de correctitud ni como primer encargo.

Para 2A: verificar conteos con llamadas pequeñas conocidas, incluyendo secuencias parciales; instrumentar no debe alterar solución, traza original ni aleatoriedad.

Para 2B: añadir prueba de deadline con reloj controlado, sin pausas reales; interrumpir BL preserva par `(solucion, makespan)` y no certifica convergencia. Comprobar default sin límite y misma política CLI por UB, manteniendo batería fija intacta.

Para etapas posteriores: evaluar cada modificación por separado. Ampliar de 3 a 30 instancias de las tres familias actuales, usando índices 00–04 para ajuste y 05–09 para validación reservada; 10 semillas por instancia. Comparar RPD medio/mediano, frecuencia de alcanzar UB y tiempo hasta objetivo.

Para cambios heurísticos, exigir mejora reproducible y costo explícito. Hasta disponer de 2B, comparar calidad y tiempo a generaciones fijas sin afirmar igualdad temporal; usar presupuestos temporales iguales para validación posterior. Una mejor corrida aislada no basta.

## Registro de prueba retirada — 2026-09-18

Implementación realizada por interpretación incorrecta del encargo y posteriormente revertida. Estos resultados corresponden a variante retirada, no al código actual. Se conservan como evidencia histórica; suite actual vuelve a sus 11 pruebas originales.

- Retorno fijo `(solucion, makespan, convergio)`, caché sólo tras convergencia y ordenamiento dentro del guard BL.
- `python3 test_makespan.py`: **14/14 pruebas**. Tres regresiones nuevas; pruebas anteriores reutilizadas.
- **30/30 corridas AG** coinciden exactamente en secuencia, makespan y traza con referencia versionada. Ordenamiento no se filtró al AG.
- **60 corridas meméticas**: 30 pares antes/después, base `bfa5af7`, semillas 1–10, tres instancias, 300 generaciones, población 60, Pc=0,85 y Pm=0,20. Todas las soluciones verificadas mediante oráculo independiente.
- Ejecuciones secuenciales, alternando orden antes/después por semilla. Tiempo incluye observación de llamadas BL en ambas versiones. CSV registra versión de Python, hash de fuentes, configuración, secuencia y traza.

| Instancia | RPD medio antes → después | Tiempo medio antes → después | Alcances UB antes → después |
|---|---:|---:|---:|
| 20×5 | 0,062598% → 0,133020% | 0,718 s → 0,727 s | 9/10 → 7/10 |
| 50×10 | 0,595041% → 0,595041% | 5,985 s → 6,757 s | 0/10 → 0/10 |
| 100×10 | 0,454073% → 0,441941% | 17,269 s → 16,882 s | 0/10 → 0/10 |

Calidad mixta: 20×5 empeora; 50×10 conserva media, con +12,9% de tiempo; 100×10 mejora levemente su media y mejor makespan pasa de 5779 a 5774. Comparaciones pareadas de makespan (mejora/empata/empeora): 1/6/3, 4/0/6 y 5/0/5, respectivamente. No demuestra mejora general ni significación estadística.

Test de signos exacto bilateral, excluyendo empates: **p=0,625; p=0,75390625; p=1**, respectivamente. No se detecta diferencia con estas muestras; no constituye prueba de equivalencia ni demuestra efecto exactamente cero. Estas pruebas comparan variante conjunta, no reoptimización aislada.

| Instancia | Llamadas BL medias antes → después | Truncadas medias antes → después | Entradas distintas medias antes → después | Reanudaciones medias después |
|---|---:|---:|---:|---:|
| 20×5 | 101,7 → 107,6 | 0 → 0 | 100,0 → 104,6 | 0 |
| 50×10 | 157,7 → 197,6 | 8,5 → 4,8 | 149,1 → 185,9 | 4,7 |
| 100×10 | 138,5 → 133,6 | 13,9 → 7,6 | 137,5 → 132,5 | 7,2 |

Reanudación = entrada que coincide con salida truncada anterior en misma corrida. Consume cupo BL; entradas distintas son permutaciones, no identidades persistentes de individuos. Cobertura observada varía por instancia; no asumir que siempre baja. En 20×5 no hubo truncamientos: cambio de trayectoria procede del orden inicial. Comparación conjunta no aísla aportes de orden y certificación en las otras instancias.

Artefactos:

- Evidencia histórica versionada en commit `4c0d054`: `results/validacion_paso1.csv` (90 filas: 60 memético + 30 AG). Corresponde a variante retirada con sort, no a propuesta actual sin sort.
- Script archivado: `local/validar_paso1.py`. Requiere variante de tres valores retirada; no ejecutarlo sobre código actual de dos valores.
- Runner guarda instrumentación fuera del motor; no implementa todavía contadores de 2A.
- Tres CSV originales conservados byte a byte. Fix independiente de UB en CLI sigue pendiente.
