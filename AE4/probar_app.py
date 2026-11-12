"""Prueba automática de la app: recorre las 7 vistas y valida que no haya errores.

Usa el AppTest de Streamlit (ejecuta el script real, sin navegador).
Uso:  ~/.venvs/pi3/bin/python AE4/probar_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parent / "app.py"
VISTAS = [
    "Resumen del periodo",
    "1 · Demanda y reparto del día",
    "2 · Franjas horarias",
    "3 · Tipo de día",
    "4 · Temporada y año",
    "5 · Clima y temperatura",
    "6 · Casuales y registrados",
]

fallos = 0
at = AppTest.from_file(str(APP), default_timeout=90).run()
if at.exception:
    print("FALLA en la carga inicial:", [e.value for e in at.exception])
    fallos += 1
else:
    print("OK  carga inicial ·", len(at.markdown), "bloques de texto")

for vista in VISTAS:
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    at.radio[0].set_value(vista).run()
    if at.exception:
        print("FALLA", vista, "→", [e.value for e in at.exception])
        fallos += 1
    else:
        print("OK ", vista)

# Filtros: un subconjunto pequeño (un año, un tipo de día, un clima)
at = AppTest.from_file(str(APP), default_timeout=90).run()
at.multiselect[0].set_value(["Verano"])
at.multiselect[1].set_value(["No laborable"])
at.multiselect[2].set_value(["Despejado"])
at.run()
if at.exception:
    print("FALLA filtros combinados →", [e.value for e in at.exception])
    fallos += 1
else:
    print("OK  filtros combinados (Verano · No laborable · Despejado)")

# Filtro extremo: solo una temporada sin filas de clima lluvia
at = AppTest.from_file(str(APP), default_timeout=90).run()
at.multiselect[0].set_value(["Invierno"])
at.radio[0].set_value(VISTAS[5]).run()
if at.exception:
    print("FALLA filtro estrecho en clima →", [e.value for e in at.exception])
    fallos += 1
else:
    print("OK  filtro estrecho en la vista de clima")

print("\n" + ("TODAS LAS VISTAS RESPONDEN" if not fallos else f"{fallos} FALLAS"))
sys.exit(1 if fallos else 0)
