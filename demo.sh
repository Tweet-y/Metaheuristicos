#!/usr/bin/env bash
# Script de demostración en vivo para el profesor (PFSP: AG vs Memético).
# Muestra manejo de errores, ambas metaheurísticas y reproducibilidad por semilla.
# Uso: ./demo.sh [instancia]
set -uo pipefail   # sin -e: los casos 1 y 2 fallan a propósito

if [ -f ".venv/bin/python3" ]; then
    PYTHON=".venv/bin/python3"
elif [ -f "venv/bin/python3" ]; then
    PYTHON="venv/bin/python3"
else
    PYTHON="python3"
fi

INSTANCIA=${1:-taillards/ins_20_5_00.txt}
OUT=results

titulo() {
    echo ""
    echo "=========================================================="
    echo " $1"
    echo "=========================================================="
}

titulo "1. Manejo de errores: sin argumentos"
"$PYTHON" algoritmoGenetico.py
echo "   -> código de salida: $?  (se espera 1)"

titulo "2. Manejo de errores: probabilidad de cruce fuera de (0, 1]"
"$PYTHON" algoritmoGenetico.py "$INSTANCIA" 30 5.0 0.2 50 42 "$OUT/demo_ag.csv"
echo "   -> código de salida: $?  (se espera 1)"

titulo "3. Algoritmo Genético ($INSTANCIA, semilla 42, 50 generaciones)"
"$PYTHON" algoritmoGenetico.py "$INSTANCIA" 30 0.8 0.2 50 42 "$OUT/demo_ag.csv" || exit 1

titulo "4. Algoritmo Memético (búsqueda local cada 2 generaciones, 3 trabajos)"
"$PYTHON" algoritmoMemetico.py "$INSTANCIA" 30 0.8 0.2 50 42 "$OUT/demo_am.csv" 2 3 || exit 1

titulo "5. Reproducibilidad: la semilla 42 debe dar el mismo makespan"
"$PYTHON" algoritmoGenetico.py "$INSTANCIA" 30 0.8 0.2 50 42 "$OUT/demo_ag_bis.csv" > /dev/null || exit 1
if diff <(cut -d';' -f7 "$OUT/demo_ag.csv") <(cut -d';' -f7 "$OUT/demo_ag_bis.csv") > /dev/null; then
    echo "   -> OK: misma semilla, mismo resultado"
else
    echo "   -> ERROR: resultados distintos con la misma semilla"
    exit 1
fi

titulo "Resultados guardados"
column -t -s';' "$OUT/demo_ag.csv" 2>/dev/null || cat "$OUT/demo_ag.csv"
echo ""
column -t -s';' "$OUT/demo_am.csv" 2>/dev/null || cat "$OUT/demo_am.csv"
