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
    "1. ¿Cuánta demanda hay y cómo se reparte en el día?",
    "2. ¿En qué franjas horarias se concentra la demanda?",
    "3. ¿Cambia la demanda según el tipo de día?",
    "4. ¿Cambia con la temporada y entre 2011 y 2012?",
    "5. ¿Cambia con el clima y la temperatura?",
    "6. ¿Qué peso tienen los usuarios casuales y los registrados?",
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
