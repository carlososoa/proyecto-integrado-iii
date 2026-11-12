"""Verificación: los números de la app deben coincidir con las tablas de la AE3.

Se ejecuta sin filtros (dataset completo) y compara contra los `.csv` que
generó el notebook de la etapa 2. Si algo no cuadra, falla con el detalle.

Uso:  python AE4/verificar_metricas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metricas as m  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "AE3" / "resultados"

fallos: list[str] = []


def comparar(nombre: str, obtenido: float, esperado: float, tolerancia: float = 0.051) -> None:
    ok = abs(obtenido - esperado) <= tolerancia
    marca = "OK " if ok else "FALLA"
    print(f"[{marca}] {nombre}: app={obtenido:,.2f}  ae3={esperado:,.2f}")
    if not ok:
        fallos.append(f"{nombre}: {obtenido} != {esperado}")


def main() -> int:
    df = m.cargar_datos(RAIZ / m.RUTA_DATOS)
    k = m.kpis(df)

    print("== Indicadores generales ==")
    comparar("Rentas totales", k["rentas"], 3_292_679)
    comparar("Horas registradas", k["horas"], 17_379)
    comparar("Días", k["dias"], 731)
    comparar("Promedio por hora", k["promedio"], 189.5)
    comparar("Mediana por hora", k["mediana"], 142)

    print("\n== Q2 · Franjas horarias ==")
    franjas = m.por_franja(df).set_index("franja_horaria")
    ae3_franjas = pd.read_csv(RES / "tabla_1a_franjas_horarias.csv", encoding="utf-8-sig").set_index("franja_horaria")
    for franja in ae3_franjas.index.drop("Total", errors="ignore"):
        if franja not in franjas.index:
            fallos.append(f"franja ausente: {franja}")
            continue
        comparar(f"{franja} · rentas", franjas.loc[franja, "rentas"], ae3_franjas.loc[franja, "rentas"])
        comparar(f"{franja} · promedio", franjas.loc[franja, "promedio"], ae3_franjas.loc[franja, "promedio_por_hora"])
        comparar(f"{franja} · participación %", franjas.loc[franja, "participacion_pct"], ae3_franjas.loc[franja, "participacion_pct"])

    print("\n== Q3 · Tipo de día ==")
    tipo = m.por_tipo_dia(df).set_index("tipo_dia")
    ae3_tipo = pd.read_csv(RES / "tabla_2_tipo_dia.csv", encoding="utf-8-sig").set_index("tipo_dia")
    for t in ae3_tipo.index:
        comparar(f"{t} · rentas", tipo.loc[t, "rentas"], ae3_tipo.loc[t, "rentas"])
        comparar(f"{t} · promedio", tipo.loc[t, "promedio"], ae3_tipo.loc[t, "promedio"])
        comparar(f"{t} · % casual", tipo.loc[t, "pct_casual"], ae3_tipo.loc[t, "pct_casual"])

    print("\n== Q4 · Temporada y año ==")
    temp = m.por_temporada(df).set_index("temporada")
    ae3_temp = pd.read_csv(RES / "tabla_3a_temporada.csv", encoding="utf-8-sig").set_index("temporada")
    for t in ae3_temp.index:
        comparar(f"{t} · promedio", temp.loc[t, "promedio"], ae3_temp.loc[t, "promedio"])
        comparar(f"{t} · participación %", temp.loc[t, "participacion_pct"], ae3_temp.loc[t, "participacion_pct"])

    anio = m.por_anio(df).set_index("anio")
    ae3_anio = pd.read_csv(RES / "tabla_3b_anio.csv", encoding="utf-8-sig").set_index("anio")
    for a in ae3_anio.index:
        comparar(f"{a} · rentas", anio.loc[a, "rentas"], ae3_anio.loc[a, "rentas"])
        comparar(f"{a} · promedio", anio.loc[a, "promedio"], ae3_anio.loc[a, "promedio"])

    print("\n== Q5 · Clima ==")
    clima = m.por_clima(df).set_index("clima")
    ae3_clima = pd.read_csv(RES / "tabla_4a_clima.csv", encoding="utf-8-sig").set_index("clima")
    for c in ae3_clima.index:
        comparar(f"{c} · promedio", clima.loc[c, "promedio"], ae3_clima.loc[c, "promedio"])
        comparar(f"{c} · participación %", clima.loc[c, "participacion_pct"], ae3_clima.loc[c, "participacion_pct"])

    print("\n== Q6 · Tipo de usuario ==")
    usuarios = m.por_tipo_usuario(df).set_index("tipo_usuario")
    ae3_usuarios = pd.read_csv(RES / "tabla_5a_tipo_usuario.csv", encoding="utf-8-sig", index_col=0)
    comparar("Casual · rentas", usuarios.loc["Casual", "rentas"], ae3_usuarios.loc["Casual", "rentas"])
    comparar("Registrado · rentas", usuarios.loc["Registrado", "rentas"], ae3_usuarios.loc["Registrado", "rentas"])
    comparar("Casual · participación %", usuarios.loc["Casual", "participacion_pct"], ae3_usuarios.loc["Casual", "participacion_pct"])

    print("\n== Consistencia interna ==")
    comparar("cnt = casual + registered", int((df["cnt"] - df["casual"] - df["registered"]).abs().max()), 0)
    comparar("Suma de franjas = total", int(franjas["rentas"].sum()), k["rentas"])
    comparar("Suma de temporadas = total", int(temp["rentas"].sum()), k["rentas"])

    print("\n" + ("TODO CUADRA" if not fallos else f"{len(fallos)} DIFERENCIAS"))
    for f in fallos:
        print("  -", f)
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
