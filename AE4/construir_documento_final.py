#!/usr/bin/env python3
"""Genera el documento integral del proyecto (AE4) en Word y PDF.

Todas las cifras salen de ``metricas.py``, la misma fuente que usa la aplicación
de Streamlit, de modo que documento y app no pueden decir cosas distintas.

Dos pasadas: la primera escribe el índice con marcadores, se convierte a PDF
para leer la página real de cada sección y la segunda escribe esos números.

Uso:  python AE4/construir_documento_final.py
"""

from __future__ import annotations

import copy
import re
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metricas as m  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "AE4" / "documento" / "PI3_proyecto_integrador_analitica_datos_grupo3.docx"
PDF = SALIDA.with_suffix(".pdf")
FIGURAS = RAIZ / "AE4" / "documento" / "figuras"
CAPTURA_APP = RAIZ / "AE4" / "documento" / "figuras" / "app_resumen.png"

REPO = "https://github.com/carlososoa/proyecto-integrado-iii"
APP = "https://proyecto-integrado-iii-team3-preica2602b020038.streamlit.app/"

AZUL = RGBColor(0x1F, 0x3B, 0x63)
GRIS = RGBColor(0x44, 0x44, 0x44)
AZUL_HEX = "#0F5C6B"
AZUL_CLARO_HEX = "#7FA9B3"
TERRACOTA_HEX = "#C8623F"
ARENA_HEX = "#F6F3EC"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.edgecolor": "#D9D3C7",
    "axes.labelcolor": "#2E2E2E",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 200,
})


# ── formato numérico en español ───────────────────────────────────────────
def num(valor, dec: int = 1) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"
    texto = f"{valor:,.{dec}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor, dec: int = 1) -> str:
    return num(valor, dec) + " %"


# ── datos calculados (una sola vez) ───────────────────────────────────────
DF = m.cargar_datos(RAIZ / m.RUTA_DATOS)
K = m.kpis(DF)
COBERTURA = m.cobertura_pct(DF)
FRANJAS = m.por_franja(DF)
HORAS = m.por_hora(DF)
TIPO_DIA = m.por_tipo_dia(DF).set_index("tipo_dia")
TEMPORADA = m.por_temporada(DF).set_index("temporada")
ANIO = m.por_anio(DF).set_index("anio")
TEMP_ANIO = m.temporada_por_anio(DF).set_index("temporada")
CLIMA = m.por_clima(DF).set_index("clima")
TEMPERATURA = m.por_rango_temperatura(DF).set_index("rango_temperatura")
USUARIO = m.por_tipo_usuario(DF).set_index("tipo_usuario")
USUARIO_DIA = m.usuarios_por_tipo_dia(DF).set_index("tipo_dia")
CONCENTRACION = m.concentracion_horaria(DF)
DIAS_TOP = m.dias_destacados(DF, 5)

TOTAL = K["rentas"]
FRANJA_TOP = FRANJAS.loc[FRANJAS["participacion_pct"].idxmax()]
FRANJA_FLOJA = FRANJAS.loc[FRANJAS["participacion_pct"].idxmin()]
PICO = float(FRANJAS[FRANJAS["franja_horaria"].isin(["Pico mañana", "Pico tarde"])]["participacion_pct"].sum())
HORA_TOP = HORAS.loc[HORAS["promedio"].idxmax()]
HORA_FLOJA = HORAS.loc[HORAS["promedio"].idxmin()]
TEMP_TOP = TEMPORADA.loc[TEMPORADA["promedio"].idxmax()]
TEMP_FLOJA = TEMPORADA.loc[TEMPORADA["promedio"].idxmin()]
CRECIMIENTO = 100 * (ANIO.loc[2012, "promedio"] / ANIO.loc[2011, "promedio"] - 1)
CLIMA_TOP = CLIMA.loc[CLIMA["promedio"].idxmax()]
LLUVIA = CLIMA.loc["Lluvia o nieve ligera"]
CAIDA_LLUVIA = 100 * (1 - LLUVIA["promedio"] / CLIMA_TOP["promedio"])
REGISTRADO = USUARIO.loc["Registrado"]
CASUAL = USUARIO.loc["Casual"]
PCT_CASUAL_LAB = USUARIO_DIA.loc["Laborable", "pct_casual"]
PCT_CASUAL_NOLAB = USUARIO_DIA.loc["No laborable", "pct_casual"]

REGLAS = pd.read_csv(RAIZ / "AE3" / "resultados" / "tabla_0_reglas_transformacion.csv", index_col=0, encoding="utf-8-sig")
DICCIONARIO = pd.read_csv(RAIZ / "AE3" / "resultados" / "tabla_diccionario.csv", encoding="utf-8-sig") if (
    RAIZ / "AE3" / "resultados" / "tabla_diccionario.csv").exists() else None
VARIABLES_NUEVAS = [
    ("mes", "Nombre del mes a partir de dteday", "Comparar estacionalidad"),
    ("es_fin_de_semana", "weekday en {0, 6} (0 = domingo)", "Separar el uso de fin de semana"),
    ("franja_horaria", "Rangos de hr: 0-5, 6-8, 9-11, 12-15, 16-19, 20-23", "Comparar la demanda a lo largo del día"),
    ("es_hora_pico", "franja_horaria en {Pico mañana, Pico tarde}", "Identificar la presión operativa"),
    ("pct_casual", "casual / cnt × 100", "Describir el perfil ocasional"),
    ("pct_registered", "registered / cnt × 100", "Describir el perfil suscrito"),
    ("rango_temperatura", "Cortes de temp_c en 5, 15 y 25 °C", "Comparar la demanda por temperatura"),
    ("clima_adverso", "weathersit en {3, 4}", "Aislar el efecto del mal tiempo"),
    ("total_dia", "Suma de cnt por dteday", "Contexto del día para cada hora"),
    ("promedio_hora_dia", "Media de cnt de las horas del día", "Comparar la hora con un día típico"),
    ("horas_registradas_dia", "Conteo de registros del día", "Identificar días incompletos"),
    ("pct_hora_del_dia", "cnt / total_dia × 100", "Dimensionar el peso de una hora en su día"),
]
DICCIONARIO_BASE = [
    ("instant", "Entero", "1 a 17.379", "Número consecutivo de la hora en el archivo; identificador del registro"),
    ("dteday", "Fecha", "AAAA-MM-DD", "Fecha del registro horario"),
    ("fecha_hora", "Fecha y hora", "Timestamp", "Fecha del día más la hora; clave temporal del análisis"),
    ("hr", "Entero", "0 a 23", "Hora del día"),
    ("cnt", "Entero", "Rentas por hora", "Total de rentas de la hora; equivale a casual + registered"),
    ("casual", "Entero", "Rentas por hora", "Rentas de usuarios sin suscripción"),
    ("registered", "Entero", "Rentas por hora", "Rentas de usuarios con suscripción"),
    ("season / temporada", "Categórica", "1-4 / primavera a invierno", "Temporada del año"),
    ("yr / anio", "Categórica", "0-1 / 2011-2012", "Año del periodo"),
    ("mnth / mes", "Entero / texto", "1-12", "Mes del año"),
    ("holiday", "Binaria", "0 o 1", "Si el día es festivo"),
    ("weekday", "Entero", "0 a 6 (0 = domingo)", "Día de la semana"),
    ("workingday", "Binaria", "0 o 1", "Día laborable (ni festivo ni fin de semana)"),
    ("weathersit / clima", "Categórica", "1-4", "Despejado, neblina, lluvia ligera, tormenta"),
    ("temp / temp_c", "Decimal", "°C", "Temperatura normalizada y convertida a grados"),
    ("atemp / atemp_c", "Decimal", "°C", "Sensación térmica"),
    ("hum / hum_pct", "Decimal", "%", "Humedad relativa"),
    ("windspeed / windspeed_kmh", "Decimal", "km/h", "Velocidad del viento"),
    ("tipo_dia", "Texto", "Laborable / No laborable", "Clasificación usada en las comparaciones"),
    ("dia_completo", "Booleana", "True / False", "Si el día tiene las 24 horas registradas"),
]


# ── utilidades de documento (mismo motor que el documento de la AE3) ──────
ENTRADAS: list[dict] = []
TABLAS: list[dict] = []
FIGURAS_DOC: list[dict] = []
NUM_TABLA = 0
NUM_FIGURA = 0


def nueva_hoja(doc, texto: str = "") -> None:
    doc.add_page_break()


def configurar(doc: Document) -> None:
    seccion = doc.sections[0]
    seccion.page_width, seccion.page_height = Cm(21), Cm(29.7)
    for lado in ("left_margin", "right_margin"):
        setattr(seccion, lado, Cm(2.5))
    seccion.top_margin, seccion.bottom_margin = Cm(2.5), Cm(2.5)

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(6)

    for nombre, tamano in (("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11.5)):
        estilo = doc.styles[nombre]
        estilo.font.name = "Calibri"
        estilo.font.size = Pt(tamano)
        estilo.font.bold = True
        estilo.font.color.rgb = AZUL
        estilo.paragraph_format.space_before = Pt(12)
        estilo.paragraph_format.space_after = Pt(6)


def campo(parrafo, instruccion: str) -> None:
    run = parrafo.add_run()
    inicio = OxmlElement("w:fldChar"); inicio.set(qn("w:fldCharType"), "begin")
    texto = OxmlElement("w:instrText"); texto.set(qn("xml:space"), "preserve"); texto.text = instruccion
    separador = OxmlElement("w:fldChar"); separador.set(qn("w:fldCharType"), "separate")
    valor = OxmlElement("w:t"); valor.text = "1"
    fin = OxmlElement("w:fldChar"); fin.set(qn("w:fldCharType"), "end")
    for elemento in (inicio, texto, separador, valor, fin):
        run._r.append(elemento)


def pie_de_pagina(doc: Document) -> None:
    pie = doc.sections[0].footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pie.add_run("Proyecto Integrado III · AE_Grupo 3 · Página ")
    campo(pie, " PAGE ")
    pie.add_run(" de ")
    campo(pie, " NUMPAGES ")


def parrafo(doc, texto: str, negrita: bool = False, cursiva: bool = False,
            tamano: float | None = None, alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY,
            estilo: str | None = None, espacio_despues: float | None = None):
    p = doc.add_paragraph(style=estilo) if estilo else doc.add_paragraph()
    p.alignment = alineacion
    run = p.add_run(texto)
    run.bold = negrita
    run.italic = cursiva
    if tamano:
        run.font.size = Pt(tamano)
    if espacio_despues is not None:
        p.paragraph_format.space_after = Pt(espacio_despues)
    return p


def vinetas(doc, items: list[str], tamano: float = 11) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(item)
        run.font.size = Pt(tamano)
        p.paragraph_format.space_after = Pt(3)


def sombrear(celda, color: str = "DCE6F1") -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), color)
    celda._tc.get_or_add_tcPr().append(shd)


def tabla(doc, encabezados: list[str], filas: list[list[str]],
          anchos: list[float] | None = None, tamano: float = 9,
          alinear_derecha: list[int] | None = None) -> None:
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    layout = OxmlElement("w:tblLayout"); layout.set(qn("w:type"), "fixed"); t._tbl.tblPr.append(layout)

    for i, texto in enumerate(encabezados):
        celda = t.rows[0].cells[i]
        celda.text = ""
        p = celda.paragraphs[0]
        run = p.add_run(texto)
        run.bold = True
        run.font.size = Pt(tamano)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sombrear(celda)

    for fila in filas:
        celdas = t.add_row().cells
        for i, texto in enumerate(fila):
            celdas[i].text = ""
            p = celdas[i].paragraphs[0]
            run = p.add_run(str(texto))
            run.font.size = Pt(tamano)
            if alinear_derecha and i in alinear_derecha:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if anchos:
        for fila in t.rows:
            for i, ancho in enumerate(anchos):
                fila.cells[i].width = Cm(ancho)

    for fila in t.rows:
        trPr = fila._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))

    if len(filas) <= 8:
        for fila in t.rows[:-1]:
            for celda in fila.cells:
                for parrafo_celda in celda.paragraphs:
                    parrafo_celda.paragraph_format.keep_with_next = True

    trPr = t.rows[0]._tr.get_or_add_trPr()
    repeticion = OxmlElement("w:tblHeader"); repeticion.set(qn("w:val"), "true"); trPr.append(repeticion)


def nota(doc, texto: str) -> None:
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run("Nota. " + texto)
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = GRIS


def nueva_tabla(doc, titulo: str) -> int:
    global NUM_TABLA
    NUM_TABLA += 1
    TABLAS.append({"numero": NUM_TABLA, "titulo": titulo})
    p = doc.add_paragraph(style="Heading 3")
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    p.add_run(f"Tabla {NUM_TABLA}. {titulo}")
    return NUM_TABLA


def figura(doc, ruta: Path, titulo: str, ancho_cm: float = 15.5) -> None:
    global NUM_FIGURA
    NUM_FIGURA += 1
    FIGURAS_DOC.append({"numero": NUM_FIGURA, "titulo": titulo})
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    # La imagen y su pie no se separan: sin esto, la figura queda al final de
    # una página y el pie de figura al inicio de la siguiente.
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.keep_together = True
    p.add_run().add_picture(str(ruta), width=Cm(ancho_cm))
    pie = doc.add_paragraph()
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pie.paragraph_format.space_after = Pt(10)
    pie.paragraph_format.keep_together = True
    run = pie.add_run(f"Figura {NUM_FIGURA}. {titulo}")
    run.font.size = Pt(9)
    run.italic = True
    run.font.color.rgb = GRIS


def seccion(doc, nivel: int, texto: str, clave: str | None = None) -> None:
    doc.add_heading(texto, level=nivel)
    if nivel <= 2:
        ENTRADAS.append({"titulo": texto, "nivel": nivel, "clave": clave or texto})


def parrafo_enlace(doc, antes: str, url: str, enlace: str | None = None, despues: str = "") -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(6)
    p.add_run(antes)

    campo_hiper = OxmlElement("w:fldSimple")
    campo_hiper.set(qn("w:instr"), f'HYPERLINK "{url}"')
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    color = OxmlElement("w:color"); color.set(qn("w:val"), "1155CC"); rpr.append(color)
    sub = OxmlElement("w:u"); sub.set(qn("w:val"), "single"); rpr.append(sub)
    run.append(rpr)
    txt = OxmlElement("w:t"); txt.text = enlace or url; run.append(txt)
    campo_hiper.append(run)
    p._p.append(campo_hiper)

    if despues:
        p.add_run(despues)


# ── figuras ───────────────────────────────────────────────────────────────
def _guardar(fig, nombre: str) -> Path:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = FIGURAS / nombre
    fig.tight_layout()
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def _miles(eje):
    from matplotlib.ticker import FuncFormatter
    eje.yaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0)))
    eje.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v, 0)))


def generar_figuras() -> dict[str, Path]:
    rutas: dict[str, Path] = {}

    # Figura 1 — demanda promedio a lo largo del día
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    ax.plot(HORAS["hr"], HORAS["promedio"], color=AZUL_HEX, linewidth=2.2, marker="o", markersize=3.2)
    ax.fill_between(HORAS["hr"], HORAS["promedio"], color=AZUL_HEX, alpha=0.10)
    ax.axhline(K["promedio"], color=TERRACOTA_HEX, linestyle="--", linewidth=1.2)
    ax.annotate(f"promedio general: {num(K['promedio'], 1)}", xy=(1.5, K["promedio"] * 1.06),
                color=TERRACOTA_HEX, fontsize=8)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hora del día")
    ax.set_ylabel("Rentas por hora (promedio)")
    ax.set_title("Demanda promedio por hora — 2011-2012")
    _miles(ax)
    rutas["hora"] = _guardar(fig, "fig1_promedio_por_hora.png")

    # Figura 2 — participación por franja
    fig, ax = plt.subplots(figsize=(7.4, 3.0))
    colores = [TERRACOTA_HEX if f in ("Pico mañana", "Pico tarde") else AZUL_CLARO_HEX for f in FRANJAS["franja_horaria"]]
    ax.barh(FRANJAS["franja_horaria"], FRANJAS["participacion_pct"], color=colores)
    for i, valor in enumerate(FRANJAS["participacion_pct"]):
        ax.text(valor + 0.5, i, f"{num(valor, 1)} %", va="center", fontsize=8)
    ax.set_xlabel("Participación del total de rentas (%)")
    ax.set_title("Participación de cada franja horaria")
    ax.invert_yaxis()
    ax.set_xlim(0, max(FRANJAS["participacion_pct"]) * 1.18)
    rutas["franja"] = _guardar(fig, "fig2_participacion_franja.png")

    # Figura 3 — tipo de día
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.0), gridspec_kw={"width_ratios": [1, 1.5]})
    ax1.bar(TIPO_DIA.index, TIPO_DIA["promedio"], color=[AZUL_HEX, TERRACOTA_HEX])
    for i, (nombre, fila) in enumerate(TIPO_DIA.iterrows()):
        ax1.text(i, fila["promedio"] + 4, num(fila["promedio"], 1), ha="center", fontsize=8)
    ax1.set_ylabel("Rentas por hora (promedio)")
    ax1.set_title("Promedio por tipo de día")
    ax1.set_ylim(0, TIPO_DIA["promedio"].max() * 1.2)
    _miles(ax1)

    perfil = m.perfil_horario_por(DF, "tipo_dia")
    for columna, color in (("Laborable", AZUL_HEX), ("No laborable", TERRACOTA_HEX)):
        if columna in perfil.columns:
            ax2.plot(perfil.index, perfil[columna], color=color, linewidth=2, marker="o", markersize=2.6, label=columna)
    ax2.set_xticks(range(0, 24, 3))
    ax2.set_xlabel("Hora del día")
    ax2.set_ylabel("Rentas por hora (promedio)")
    ax2.set_title("Perfil horario por tipo de día")
    ax2.legend(frameon=False, fontsize=8)
    _miles(ax2)
    rutas["tipo_dia"] = _guardar(fig, "fig3_tipo_dia.png")

    # Figura 4 — temporada y año
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.0))
    colores = [AZUL_HEX if t == TEMP_TOP.name else AZUL_CLARO_HEX for t in TEMPORADA.index]
    ax1.bar(TEMPORADA.index, TEMPORADA["promedio"], color=colores)
    for i, (nombre, fila) in enumerate(TEMPORADA.iterrows()):
        ax1.text(i, fila["promedio"] + 5, num(fila["promedio"], 1), ha="center", fontsize=8)
    ax1.set_ylabel("Rentas por hora (promedio)")
    ax1.set_title("Promedio por temporada")
    ax1.set_ylim(0, TEMPORADA["promedio"].max() * 1.18)
    _miles(ax1)

    temporadas = list(TEMP_ANIO.index)
    x = range(len(temporadas))
    ancho = 0.38
    for i, (anio, color) in enumerate(((2011, AZUL_CLARO_HEX), (2012, AZUL_HEX))):
        if anio in TEMP_ANIO.columns:
            valores = TEMP_ANIO[anio].values
            ax2.bar([v + (i - 0.5) * ancho for v in x], valores, width=ancho, color=color, label=str(anio))
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(temporadas)
    ax2.set_ylabel("Rentas por hora (promedio)")
    ax2.set_title("Promedio por temporada y año")
    ax2.legend(frameon=False, fontsize=8)
    _miles(ax2)
    rutas["temporada"] = _guardar(fig, "fig4_temporada_anio.png")

    # Figura 5 — clima y temperatura
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.0), gridspec_kw={"width_ratios": [1.35, 1]})
    orden = list(CLIMA.index)
    colores = [TERRACOTA_HEX if "Lluvia" in c else (AZUL_HEX if c == "Despejado" else AZUL_CLARO_HEX) for c in orden]
    ax1.barh(orden, CLIMA["promedio"], color=colores)
    for i, valor in enumerate(CLIMA["promedio"]):
        ax1.text(valor + 6, i, num(valor, 1), va="center", fontsize=8)
    ax1.invert_yaxis()
    ax1.set_xlabel("Rentas por hora (promedio)")
    ax1.set_title("Promedio por condición climática")
    ax1.set_xlim(0, CLIMA["promedio"].max() * 1.2)

    ax2.plot(TEMPERATURA.index, TEMPERATURA["promedio"], color=TERRACOTA_HEX, linewidth=2, marker="o", markersize=5)
    for i, valor in enumerate(TEMPERATURA["promedio"]):
        ax2.annotate(num(valor, 1), (i, valor), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
    ax2.set_ylabel("Rentas por hora (promedio)")
    ax2.set_title("Promedio por rango de temperatura")
    ax2.tick_params(axis="x", labelsize=8)
    _miles(ax2)
    rutas["clima"] = _guardar(fig, "fig5_clima_temperatura.png")

    # Figura 6 — tipo de usuario
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.0), gridspec_kw={"width_ratios": [1, 1.5]})
    ax1.pie(USUARIO["rentas"], labels=USUARIO.index, autopct=lambda v: f"{num(v, 1)} %",
            colors=[AZUL_HEX if i == "Registrado" else TERRACOTA_HEX for i in USUARIO.index],
            startangle=90, wedgeprops=dict(width=0.42, edgecolor="white"))
    ax1.set_title("Participación sobre el total")

    perfil_usuarios = DF.pivot_table(index="hr", values=["casual", "registered"], aggfunc="mean").reindex(range(24))
    ax2.plot(perfil_usuarios.index, perfil_usuarios["registered"], color=AZUL_HEX, linewidth=2, label="Registrado")
    ax2.plot(perfil_usuarios.index, perfil_usuarios["casual"], color=TERRACOTA_HEX, linewidth=2, label="Casual")
    ax2.set_xticks(range(0, 24, 3))
    ax2.set_xlabel("Hora del día")
    ax2.set_ylabel("Rentas por hora (promedio)")
    ax2.set_title("Perfil horario por tipo de usuario")
    ax2.legend(frameon=False, fontsize=8)
    _miles(ax2)
    rutas["usuario"] = _guardar(fig, "fig6_tipo_usuario.png")

    return rutas


# ── portada e índices ─────────────────────────────────────────────────────
def portada(doc: Document) -> None:
    for _ in range(2):
        doc.add_paragraph()
    parrafo(doc, "INSTITUCIÓN UNIVERSITARIA DIGITAL DE ANTIOQUIA", negrita=True,
            alineacion=WD_ALIGN_PARAGRAPH.CENTER, tamano=12)
    parrafo(doc, "Proyecto Integrado III — Analítica de Datos", alineacion=WD_ALIGN_PARAGRAPH.CENTER, tamano=11)
    for _ in range(4):
        doc.add_paragraph()
    p = parrafo(doc, "Demanda de un sistema de bicicletas públicas: análisis descriptivo "
                     "de la operación 2011-2012 y aplicación de visualización",
                negrita=True, alineacion=WD_ALIGN_PARAGRAPH.CENTER, tamano=16)
    p.paragraph_format.line_spacing = 1.15
    parrafo(doc, "Informe final del proyecto integrador", alineacion=WD_ALIGN_PARAGRAPH.CENTER,
            tamano=12, cursiva=True)
    for _ in range(5):
        doc.add_paragraph()

    datos = [
        ("Integrantes", "Carlos Andrés Osorio Agudelo\nEstefanía Martínez Guzmán\nValentina Pérez Flórez"),
        ("Grupo", "AE_Grupo 3"),
        ("Asignatura", "Proyecto Integrado III - Analítica de Datos"),
        ("Docente", "Andrés Felipe Callejas Jaramillo"),
        ("Institución", "Institución Universitaria Digital de Antioquia"),
        ("Periodo académico", "2026-2, bloque 2"),
        ("Fecha", "Noviembre de 2026"),
        ("Repositorio", REPO.replace("https://", "")),
        ("Aplicación", APP.replace("https://", "")),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for etiqueta, valor in datos:
        celdas = t.add_row().cells
        p0 = celdas[0].paragraphs[0]
        r0 = p0.add_run(etiqueta)
        r0.bold = True
        r0.font.size = Pt(9.5)
        p0.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p1 = celdas[1].paragraphs[0]
        r1 = p1.add_run(valor)
        r1.font.size = Pt(9.5)
        celdas[0].width, celdas[1].width = Cm(4.2), Cm(10.5)
    doc.add_page_break()


def indice(doc: Document, paginas: dict[str, int] | None, marca) -> None:
    """Escribe el índice al final y lo mueve antes del cuerpo.

    Todo ocurre dentro del mismo documento: si el cuerpo se construyera en un
    documento aparte y se copiara, las imágenes perderían sus relaciones y las
    figuras desaparecerían del archivo final.
    """
    creados = []

    def nuevo_parrafo(estilo: str | None = None):
        p = doc.add_paragraph(style=estilo) if estilo else doc.add_paragraph()
        creados.append(p)
        return p

    p = nuevo_parrafo("Heading 1")
    p.add_run("Tabla de contenido")
    intro = nuevo_parrafo()
    run = intro.add_run("Las páginas indicadas corresponden a este documento en formato PDF.")
    run.italic = True
    run.font.size = Pt(9)
    intro.alignment = WD_ALIGN_PARAGRAPH.LEFT

    for entrada in ENTRADAS:
        p = nuevo_parrafo()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.tab_stops.add_tab_stop(Cm(16), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        p.paragraph_format.left_indent = Cm(0 if entrada["nivel"] == 1 else 0.6)
        run = p.add_run(entrada["titulo"])
        run.font.size = Pt(11 if entrada["nivel"] == 1 else 10.5)
        run.bold = entrada["nivel"] == 1
        numero = paginas.get(entrada["titulo"], 0) if paginas else 0
        p.add_run("\t" + (str(numero) if numero else "00")).font.size = Pt(11)

    creados.append(doc.add_page_break())
    p = nuevo_parrafo("Heading 1")
    p.add_run("Índice de tablas")
    for item in TABLAS:
        p = nuevo_parrafo()
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(f"Tabla {item['numero']}. {item['titulo']}")
        run.font.size = Pt(9.5)

    creados.append(doc.add_page_break())
    p = nuevo_parrafo("Heading 1")
    p.add_run("Índice de figuras")
    for item in FIGURAS_DOC:
        p = nuevo_parrafo()
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        run = p.add_run(f"Figura {item['numero']}. {item['titulo']}")
        run.font.size = Pt(9.5)

    creados.append(doc.add_page_break())

    for elemento in creados:
        marca._p.addprevious(elemento._p)


# ── 1. Introducción ───────────────────────────────────────────────────────
def introduccion(doc: Document) -> None:
    seccion(doc, 1, "1. Introducción")
    parrafo(doc, "Este informe cierra el proyecto integrador del curso. Reúne en un solo documento "
                 "las cuatro etapas del trabajo: la definición de la necesidad y el reconocimiento del "
                 "conjunto de datos, la transformación y el enriquecimiento de la información, la "
                 "construcción de métricas y visualizaciones, y la aplicación que permite recorrer los "
                 "resultados. No es una suma de entregas anteriores: cada etapa se reescribió para que "
                 "el documento se lea como una sola investigación, con una pregunta al principio y una "
                 "respuesta sustentada al final.")
    parrafo(doc, "El objeto de estudio es la demanda de un sistema de bicicletas públicas: cuántas "
                 "bicicletas se rentan cada hora y cómo cambia esa cantidad según la hora del día, el "
                 "tipo de día, la temporada y el clima. El conjunto de datos contiene 17.379 horas de "
                 "operación del sistema Capital Bikeshare de Washington D. C. entre 2011 y 2012, y cada "
                 "fila es una hora, no un viaje ni un usuario. Esa decisión —la unidad de análisis— "
                 "condiciona todo lo que sigue: el proyecto describe el comportamiento del sistema, no "
                 "el de las personas que lo usan.")
    parrafo(doc, "El documento se organiza así: la sección 2 plantea la necesidad y las seis "
                 "preguntas de negocio; la 3 justifica el trabajo; la 4 fija los objetivos; la 5 "
                 "presenta el marco conceptual; la 6 describe la metodología y las herramientas; la 7 "
                 "documenta la transformación y el enriquecimiento de los datos; la 8 define las "
                 "métricas y las visualizaciones; la 9 discute los resultados; la 10 describe la "
                 "aplicación publicada; y las secciones 11 a 13 cierran con conclusiones, limitaciones "
                 "y referencias. Los anexos reúnen los enlaces, la estructura del repositorio y las "
                 "instrucciones para reproducir el análisis.")
    parrafo(doc, "Todo el trabajo es verificable: el repositorio conserva el código, los notebooks "
                 "ejecutados, las tablas de resultados y el documento; un flujo de integración continua "
                 "vuelve a ejecutar los notebooks en cada cambio; y un script de verificación contrasta "
                 "las cifras de la aplicación contra las tablas del análisis.")
    parrafo_enlace(doc, "Repositorio del proyecto: ", REPO, REPO,
                   ". Aplicación publicada: ")
    parrafo_enlace(doc, "", APP, APP, ".")


# ── 2. Necesidad y preguntas ──────────────────────────────────────────────
def necesidad(doc: Document) -> None:
    seccion(doc, 1, "2. La necesidad y las preguntas de negocio")
    seccion(doc, 2, "2.1. La necesidad de información")
    parrafo(doc, "El área de operaciones de un sistema de bicicletas públicas necesita anticipar en qué "
                 "momentos del día y bajo qué condiciones se concentra la demanda. De esa anticipación "
                 "dependen tres decisiones que se toman todos los días: cuántas bicicletas conviene tener "
                 "disponibles en cada zona, cuántas personas se destinan a reubicar bicicletas entre "
                 "estaciones y cuándo se programa el mantenimiento sin afectar el servicio.")
    parrafo(doc, "El conjunto de datos no trae esa lectura hecha. La información existe —cada hora "
                 "registrada incluye la cantidad de rentas, la hora, el día, la temporada y las "
                 "condiciones climáticas—, pero comparar franjas horarias, tipos de día o condiciones "
                 "climáticas exige preparar los datos y agregarlos de forma sistemática. Ese es el aporte "
                 "del proyecto: convertir un archivo de registros horarios en un conjunto de métricas "
                 "comparables y en una herramienta que permita recorrerlas.")
    parrafo(doc, "La necesidad se puede formular como una pregunta de análisis: describir cómo se "
                 "distribuye la demanda de rentas a lo largo del día y cómo cambia según el tipo de día, "
                 "la temporada y el clima, con el fin de apoyar decisiones de capacidad, personal y "
                 "mantenimiento.")

    seccion(doc, 2, "2.2. Las seis preguntas de negocio")
    parrafo(doc, "La pregunta de análisis se descompone en seis preguntas que se responden con las "
                 "variables disponibles. Cada una se asocia a una métrica, a una unidad y a una tabla de "
                 "resultados, de modo que cualquier afirmación del informe se pueda rastrear hasta un "
                 "cálculo.")
    numero = nueva_tabla(doc, "Preguntas de negocio, variables que las responden y métrica asociada")
    tabla(doc,
          ["#", "Pregunta", "Variables", "Métrica principal", "Unidad"],
          [["1", "¿Cuánta demanda hay y cómo se reparte en el día?", "cnt, hr, fecha_hora",
            "Rentas totales, promedio y mediana por hora", "rentas y rentas/hora"],
           ["2", "¿En qué franjas horarias se concentra?", "hr, franja_horaria",
            "Participación de cada franja sobre el total", "% del total"],
           ["3", "¿Cambia según el tipo de día?", "workingday, holiday, tipo_dia",
            "Promedio por hora y peso del usuario ocasional", "rentas/hora y %"],
           ["4", "¿Cambia con la temporada y entre 2011 y 2012?", "season, mnth, yr, temporada, anio",
            "Promedio por temporada y variación anual", "rentas/hora y %"],
           ["5", "¿Cambia con el clima y la temperatura?", "weathersit, temp_c, hum_pct, windspeed_kmh",
            "Promedio por condición climática y por rango de temperatura", "rentas/hora"],
           ["6", "¿Qué peso tienen casuales y registrados?", "casual, registered, pct_casual",
            "Participación de cada tipo de usuario", "% del total"]],
          anchos=[0.9, 4.6, 3.6, 4.6, 2.4])
    nota(doc, "Elaboración propia. La columna de variables remite a los nombres del conjunto de datos "
              "preparado, documentado en la sección 7.3.")

    seccion(doc, 2, "2.3. Alcance")
    parrafo(doc, "El análisis es descriptivo y comparativo. Describe el comportamiento observado de la "
                 "demanda y lo compara entre grupos (franjas, tipos de día, temporadas, condiciones "
                 "climáticas, tipos de usuario). No busca explicar causas ni predecir valores futuros, y "
                 "esa restricción no es una limitación del trabajo sino una decisión de diseño: con dos "
                 "años de historia y sin datos de oferta no es posible aislar relaciones causales ni "
                 "construir un modelo predictivo defendible.")
    parrafo(doc, "El alcance también excluye cualquier lectura financiera. El conjunto de datos no "
                 "contiene precios, tarifas, costos ni ingresos, de modo que el informe habla de "
                 "cantidad de rentas y nunca de rentabilidad. Cuando se menciona una decisión de "
                 "negocio, se formula como una decisión de operación —capacidad, personal, "
                 "mantenimiento— y no como un resultado económico.")


# ── 3. Justificación ──────────────────────────────────────────────────────
def justificacion(doc: Document) -> None:
    seccion(doc, 1, "3. Justificación")
    parrafo(doc, "Un sistema de bicicletas públicas tiene un problema operativo concreto: la demanda no "
                 "se reparte de forma uniforme. Hay horas en que las estaciones se vacían y horas en que "
                 "las bicicletas se acumulan; hay días en que el sistema trabaja al límite y días en que "
                 "sobra capacidad. Si la operación se planea con promedios diarios, esas diferencias "
                 "desaparecen y el resultado es un servicio desigual: bicicletas donde nadie las usa y "
                 "estaciones vacías donde hay demanda.")
    parrafo(doc, "El proyecto aborda ese problema con evidencia. En lugar de decidir por intuición, "
                 "construye métricas que muestran dónde se concentra la demanda y cuánto cambia según el "
                 "contexto, de modo que la discusión sobre turnos, reubicación y mantenimiento se pueda "
                 "sostener en cifras. La aplicación cumple una función adicional: cualquier persona del "
                 "área de operaciones puede abrir el enlace, filtrar el periodo y ver la respuesta sin "
                 "instalar nada ni saber programar.")
    parrafo(doc, "La elección del conjunto de datos también se justifica. El registro horario del "
                 "sistema Capital Bikeshare es público, verificable y de dos años completos; incluye la "
                 "variable que se quiere describir (cantidad de rentas) y los criterios de agrupación "
                 "necesarios para compararla (hora, día, temporada, clima). Es decir, la pregunta se "
                 "puede responder íntegramente con las variables disponibles, y esa correspondencia entre "
                 "pregunta y datos es la razón para usar este conjunto y no otro.")
    parrafo(doc, "Desde el punto de vista formativo, el proyecto integra las competencias del curso: "
                 "preparación y validación de datos, construcción de indicadores, visualización, "
                 "versionamiento del código y publicación de una aplicación. Cada etapa deja un "
                 "artefacto verificable —notebook ejecutado, tablas de resultados, documento y "
                 "aplicación— y el conjunto demuestra que el análisis se puede reproducir de principio a "
                 "fin.")


# ── 4. Objetivos ──────────────────────────────────────────────────────────
def objetivos(doc: Document) -> None:
    seccion(doc, 1, "4. Objetivos")
    seccion(doc, 2, "4.1. Objetivo general")
    parrafo(doc, "Describir el comportamiento horario de la demanda de un sistema de bicicletas públicas "
                 "entre 2011 y 2012, y comunicar los resultados mediante métricas, visualizaciones y una "
                 "aplicación que permita recorrerlos y apoyar decisiones de operación.")
    seccion(doc, 2, "4.2. Objetivos específicos")
    vinetas(doc, [
        "Preparar y validar el conjunto de datos: tipos, escalas, duplicados, consistencia y cobertura.",
        "Construir variables derivadas que permitan comparar la demanda por franja horaria, tipo de día, "
        "temporada, clima y tipo de usuario.",
        "Definir una métrica con su fórmula, su unidad y su periodo para cada una de las seis preguntas "
        "de negocio.",
        "Producir visualizaciones que respondan cada pregunta y que declaren la decisión que apoyan y su "
        "limitación.",
        "Publicar una aplicación en Streamlit vinculada al repositorio, con filtros y verificación de "
        "cifras contra las tablas del análisis.",
        "Documentar el proceso completo en un informe reproducible y versionado en GitHub.",
    ])


# ── 5. Marco teórico ──────────────────────────────────────────────────────
def marco_teorico(doc: Document) -> None:
    seccion(doc, 1, "5. Marco teórico")
    seccion(doc, 2, "5.1. Analítica descriptiva y su lugar frente a explicar y predecir")
    parrafo(doc, "La analítica de datos suele dividirse en tres niveles: descriptiva, que caracteriza lo "
                 "que ocurrió; explicativa, que busca relaciones causales; y predictiva, que estima lo que "
                 "puede ocurrir. Este proyecto se ubica deliberadamente en el primer nivel. Describir no es "
                 "una versión menor de explicar: es la condición para hacerlo, porque no se puede plantear "
                 "una hipótesis causal sobre un fenómeno cuya forma no se ha caracterizado.")
    parrafo(doc, "La distinción tiene consecuencias prácticas. Un informe descriptivo puede afirmar que "
                 "la demanda cae cuando llueve, porque eso es lo que muestran los datos; no puede afirmar "
                 "que la lluvia causa la caída, porque el clima se mueve junto con la temporada y con el "
                 "tipo de día, y el conjunto de datos no permite separar esos efectos. Mantener la "
                 "diferencia evita la conclusión más común y más difícil de sostener en un análisis de "
                 "este tipo: confundir asociación con causa.")
    seccion(doc, 2, "5.2. De la tabla a la métrica")
    parrafo(doc, "Una métrica es un cálculo con tres componentes explícitos: la fórmula, la unidad y el "
                 "periodo al que se refiere. Sin los tres, un número no significa nada. Decir que el "
                 "sistema registró 3.292.679 rentas solo tiene sentido si se aclara que son rentas "
                 "acumuladas en 17.379 horas entre 2011 y 2012; decir que el promedio es 189,5 exige la "
                 "unidad —rentas por hora— y aclarar que promedia horas registradas, no días.")
    parrafo(doc, "El proyecto usa dos familias de métricas. Las de volumen (rentas totales, rentas del "
                 "día) miden cuánto; las de intensidad (promedio por hora, mediana, participación) miden "
                 "cómo se reparte. Distinguirlas es importante: dos periodos pueden tener el mismo "
                 "volumen y una distribución completamente distinta, y es la distribución la que informa "
                 "la decisión operativa.")
    parrafo(doc, "Junto al promedio se reporta la mediana. Cuando el promedio supera a la mediana, la "
                 "distribución tiene una cola de valores altos: unas pocas horas muy cargadas elevan el "
                 "promedio, mientras la hora típica se parece más a la mediana. En este proyecto el "
                 f"promedio es {num(K['promedio'], 1)} y la mediana {num(K['mediana'])} rentas por hora, "
                 "una diferencia que ya anticipa que el día no es homogéneo.")
    seccion(doc, 2, "5.3. Diseño de visualizaciones")
    parrafo(doc, "Una visualización se justifica cuando responde una pregunta. De ahí se derivan cuatro "
                 "reglas que se aplicaron en todas las figuras: cada gráfico tiene título, ejes con "
                 "unidad y periodo; el tipo de gráfico corresponde a la comparación (barras para "
                 "categorías, líneas para evolución horaria, barras horizontales cuando las etiquetas son "
                 "largas); el eje de valores no se trunca, porque truncar exagera diferencias; y la cifra "
                 "que sostiene la lectura aparece en el propio gráfico o en la tabla que lo acompaña.")
    parrafo(doc, "También se evita el exceso de tinta: sin fondos de color, sin efectos 3D, sin "
                 "rejillas innecesarias y con un máximo de dos colores por figura. Cuando una categoría "
                 "importa —la franja de mayor demanda, la temporada más fuerte, la condición climática "
                 "seca— se resalta con color y el resto queda en un tono secundario, de modo que la "
                 "figura se lea en dos segundos.")
    seccion(doc, 2, "5.4. Del notebook a la aplicación")
    parrafo(doc, "Un notebook es un buen instrumento de análisis y un mal instrumento de consulta: "
                 "requiere instalar dependencias, ejecutar celdas y saber dónde mirar. Para que el "
                 "resultado sea utilizable por un área de operaciones, el análisis se publica como "
                 "aplicación web. Streamlit permite escribirla en Python, leer los mismos datos del "
                 "repositorio y publicarla desde GitHub con una URL accesible.")
    parrafo(doc, "La consecuencia metodológica es importante: si la aplicación y el documento calculan "
                 "por separado, tarde o temprano muestran cifras distintas. Por eso el proyecto concentra "
                 "el cálculo en un módulo único del que dependen la aplicación, el documento y el script "
                 "de verificación. La reproducibilidad no se declara, se comprueba: el repositorio "
                 "re-ejecuta los notebooks en cada cambio y un script contrasta las cifras de la "
                 "aplicación contra las tablas del análisis.")
    seccion(doc, 2, "5.5. Límites conceptuales del dato")
    parrafo(doc, "El conjunto de datos describe la demanda satisfecha: los viajes que ocurrieron. No "
                 "registra la demanda insatisfecha —la persona que llegó a una estación vacía y se fue—, "
                 "ni la oferta disponible —bicicletas, anclajes, estaciones—. Tampoco identifica usuarios: "
                 "las variables casual y registered son tipos de renta, no personas. Estas tres ausencias "
                 "acotan lo que el informe puede afirmar y se retoman en la sección de limitaciones.")


# ── 6. Metodología ────────────────────────────────────────────────────────
def metodologia(doc: Document) -> None:
    seccion(doc, 1, "6. Metodología")
    seccion(doc, 2, "6.1. Enfoque y herramientas")
    parrafo(doc, "El trabajo sigue un enfoque cuantitativo, descriptivo y comparativo, organizado en "
                 "cuatro etapas encadenadas: obtención y reconocimiento de los datos, transformación y "
                 "enriquecimiento, construcción de métricas y visualizaciones, y publicación de la "
                 "aplicación. Cada etapa produce un artefacto que la siguiente consume, y todas quedan "
                 "versionadas en el mismo repositorio.")
    numero = nueva_tabla(doc, "Herramientas utilizadas y función en el proyecto")
    tabla(doc,
          ["Herramienta", "Función"],
          [["Python 3", "Lenguaje del análisis y de la aplicación"],
           ["pandas", "Lectura, transformación, validación y agregación de los datos"],
           ["Hugging Face datasets", "Obtención del conjunto de datos original"],
           ["Jupyter / nbconvert", "Notebooks ejecutados de cada etapa"],
           ["matplotlib y plotly", "Gráficos del documento y de la aplicación"],
           ["Streamlit", "Aplicación web de consulta"],
           ["Git y GitHub", "Versionamiento, historial e integración continua"],
           ["LibreOffice", "Conversión del documento a PDF"]],
          anchos=[5.0, 11.0], tamano=9)
    nota(doc, "El repositorio incluye el archivo requirements.txt con las versiones mínimas requeridas.")

    seccion(doc, 2, "6.2. Fuente de los datos y cobertura")
    numero = nueva_tabla(doc, "Ficha técnica del conjunto de datos")
    tabla(doc,
          ["Campo", "Valor"],
          [["Identificador", "t22000t/bike-sharing-tabular (Hugging Face)"],
           ["Origen", "UCI Machine Learning Repository, Bike Sharing Dataset (id 275)"],
           ["Sistema observado", "Capital Bikeshare, Washington D. C."],
           ["Periodo", f"1 de enero de 2011 a 31 de diciembre de 2012 ({num(K['dias'])} días)"],
           ["Registros", f"{num(K['horas'])} horas de operación"],
           ["Columnas originales / finales", "17 / 40"],
           ["Cobertura", f"{pct(COBERTURA)} de las {num(K['horas_esperadas'])} horas del periodo"],
           ["Horas sin registro", f"{num(K['horas_faltantes'])} (no se imputan)"],
           ["Licencia", "CC-BY-4.0"],
           ["Datos reales", "Sí, registro horario del sistema operado por Capital Bikeshare"]],
          anchos=[5.0, 11.0], tamano=9)
    nota(doc, "Cita de los datos: Fanaee-T y Gama (2013), ver sección 12.")

    seccion(doc, 2, "6.3. Las cuatro etapas del proyecto")
    numero = nueva_tabla(doc, "Etapas del proyecto y producto de cada una")
    tabla(doc,
          ["Etapa", "Propósito", "Producto verificable"],
          [["EA1", "Cargar el conjunto y describir su estructura",
            "Notebook ejecutado y resumen descriptivo"],
           ["AE2", "Definir la necesidad, las preguntas y revisar la calidad de los datos",
            "Documento de la etapa 1 y reporte de calidad"],
           ["AE3", "Transformar, enriquecer y generar las tablas de resultados",
            "17 tablas en CSV y el conjunto preparado"],
           ["AE4", "Construir métricas, visualizaciones y la aplicación; integrar el informe",
            "Aplicación publicada y este documento"]],
          anchos=[1.6, 8.4, 6.0], tamano=9)
    nota(doc, "Cada notebook se vuelve a ejecutar automáticamente en GitHub Actions en cada cambio del "
              "repositorio, de modo que las salidas publicadas corresponden al código vigente.")

    seccion(doc, 2, "6.4. Reglas de transformación y control de calidad")
    parrafo(doc, "La transformación no eliminó registros: las ocho reglas documentadas se aplicaron sobre "
                 "los 17.379 registros y su efecto quedó registrado una por una, incluidas las que no "
                 "encontraron problemas. Esa práctica permite distinguir entre una regla que se aplicó y "
                 "una regla que se verificó sin hallazgos.")
    numero = nueva_tabla(doc, "Reglas de transformación aplicadas y registros afectados")
    filas = []
    for _, fila in REGLAS.iterrows():
        filas.append([str(fila["regla"]), str(fila["detalle"]), num(int(fila["registros_afectados"]), 0)])
    tabla(doc, ["Regla", "Decisión aplicada", "Registros afectados"], filas,
          anchos=[3.4, 10.4, 2.4], tamano=8.5, alinear_derecha=[2])
    nota(doc, "Elaboración propia a partir del notebook de la etapa 3. Las reglas de control que no "
              "encontraron problemas se reportan con cero registros afectados.")

    seccion(doc, 2, "6.5. Enriquecimiento: doce variables derivadas")
    parrafo(doc, "El enriquecimiento construye información nueva a partir de la que ya existe: no agrega "
                 "registros ni incorpora fuentes externas. Las doce variables derivadas se agrupan en "
                 "cuatro bloques —calendario, horario, clima y contexto del día— y cada una existe por "
                 "una razón analítica concreta.")
    numero = nueva_tabla(doc, "Variables construidas en la etapa de enriquecimiento")
    tabla(doc, ["Variable", "Fórmula o regla", "Para qué sirve"],
          [[nombre, regla, utilidad] for nombre, regla, utilidad in VARIABLES_NUEVAS],
          anchos=[3.8, 7.4, 5.0], tamano=8.5)
    nota(doc, "Todas las variables se calculan con operaciones sobre columnas existentes; ninguna "
              "requiere información externa al conjunto de datos.")

    seccion(doc, 2, "6.6. Reproducibilidad y verificación")
    parrafo(doc, "El repositorio contiene el código, los notebooks ya ejecutados, las tablas de "
                 "resultados, el conjunto preparado, la aplicación y este documento. Un flujo de "
                 "integración continua vuelve a ejecutar los tres notebooks en cada cambio publicado, y "
                 "el resultado se confirma antes de dar por buena cualquier cifra.")
    parrafo(doc, "Sobre esa base se añadieron dos controles propios de esta etapa. El primero, un script "
                 "que recalcula las métricas y las compara contra las tablas del análisis: si una cifra "
                 "no coincide, falla y lo reporta. El segundo, una prueba automática que ejecuta las "
                 "siete vistas de la aplicación y verifica que ninguna lance errores, incluso con "
                 "combinaciones de filtros que dejan pocos registros.")
    vin_bullets = [
        "Coherencia aritmética: la cantidad de rentas es igual a la suma de casuales y registradas en "
        "todos los registros.",
        "Coherencia de agregación: la suma de las franjas horarias y de las temporadas equivale al total "
        "del periodo.",
        "Coherencia documento-aplicación: las cifras publicadas en este informe provienen del mismo "
        "módulo de cálculo que usa la aplicación.",
    ]
    vinetas(doc, vin_bullets)


# ── 7. Transformación y enriquecimiento ───────────────────────────────────
def transformacion(doc: Document) -> None:
    seccion(doc, 1, "7. Transformación y enriquecimiento de los datos")
    parrafo(doc, "El conjunto original tiene 17 columnas, varias de ellas codificadas: la temporada y el "
                 "clima como números enteros, el año como 0 y 1, la temperatura y la humedad normalizadas "
                 "en una escala sin unidad. Antes de comparar cualquier cosa hay que devolver esas "
                 "variables a una forma legible y verificar que la conversión no alteró los registros.")
    seccion(doc, 2, "7.1. Efecto de las reglas sobre el conjunto")
    parrafo(doc, "La transformación no eliminó filas. El control se hizo comparando la estructura antes y "
                 "después: mismas horas, mismas rentas totales, mismos días. Si una conversión hubiera "
                 "fallado, el total de rentas habría cambiado y la validación lo habría detectado.")
    numero = nueva_tabla(doc, "Comparación del conjunto antes y después de la transformación")
    tabla(doc, ["Comprobación", "Antes", "Después", "Diferencia"],
          [["Filas (horas registradas)", num(K["horas"]), num(K["horas"]), "0"],
           ["Rentas totales", num(TOTAL), num(TOTAL), "0"],
           ["Días con registro", num(K["dias"]), num(K["dias"]), "0"],
           ["Columnas", "17", "40", "+23"],
           ["Filas con cnt distinto de casual + registered", "0", "0", "0"]],
          anchos=[8.0, 2.8, 2.8, 2.6], alinear_derecha=[1, 2, 3], tamano=9)
    nota(doc, "El aumento de columnas corresponde a las cuatro escalas convertidas, las etiquetas "
              "traducidas y las doce variables derivadas.")

    seccion(doc, 2, "7.2. Cobertura y datos faltantes")
    parrafo(doc, f"El periodo tiene {num(K['dias'])} días, es decir {num(K['horas_esperadas'])} horas "
                 f"posibles, y el archivo registra {num(K['horas'])}. Faltan {num(K['horas_faltantes'])} "
                 f"horas repartidas en días incompletos, un {pct(100 - COBERTURA)} del total. Esas horas "
                 "no se imputaron: inventar registros alteraría los promedios y ocultaría el problema. En "
                 "cambio, se marcaron con la variable dia_completo, de modo que cualquier análisis pueda "
                 "excluir los días incompletos si lo necesita.")
    parrafo(doc, "La decisión tiene un costo y se asume: los promedios por hora se calculan sobre las "
                 "horas que existen, así que una hora con pocos registros puede tener un promedio menos "
                 "estable. Por eso cada tabla reporta, junto al promedio, la cantidad de horas que lo "
                 "sostienen: es la forma de que el lector juzgue la solidez de la cifra.")

    seccion(doc, 2, "7.3. Diccionario de datos")
    parrafo(doc, "El diccionario documenta el significado, el tipo y la unidad de cada variable del "
                 "conjunto final. Es la referencia para leer las tablas de resultados y para interpretar "
                 "las variables que aparecen en la aplicación.")
    numero = nueva_tabla(doc, "Diccionario de datos del conjunto final")
    tabla(doc, ["Variable", "Tipo", "Unidad o valores", "Significado y regla"],
          [list(fila) for fila in DICCIONARIO_BASE],
          anchos=[3.6, 3.0, 3.8, 5.8], tamano=8.5)
    nota(doc, "Las variables derivadas se documentan en la Tabla 6. El conjunto completo tiene 40 "
              "columnas; aquí se describen las que se usan en el informe y en la aplicación.")

    seccion(doc, 2, "7.4. Validaciones aplicadas")
    parrafo(doc, "Cuatro validaciones sostienen la calidad del conjunto y se repiten en cada ejecución "
                 "del notebook:")
    vinetas(doc, [
        "Consistencia del total: cnt es igual a casual + registered en los 17.379 registros; no hay "
        "filas donde la suma de los dos tipos de usuario no coincida con el total.",
        "Duplicados temporales: no hay dos registros con la misma fecha y hora; la clave fecha_hora es "
        "única.",
        "Dominios: la hora está entre 0 y 23, el día de la semana entre 0 y 6, la temporada y la "
        "condición climática entre 1 y 4.",
        "Cobertura: se informa cuántas horas del periodo tienen registro y cuántas faltan, sin imputar "
        "ninguna.",
    ])


# ── 8. Métricas y visualizaciones ─────────────────────────────────────────
def metricas_visualizaciones(doc: Document, figuras: dict[str, Path]) -> None:
    seccion(doc, 1, "8. Métricas y visualizaciones")
    parrafo(doc, "Esta sección define qué se mide y cómo se muestra. La definición va antes que los "
                 "resultados por una razón: si la métrica no está definida —fórmula, unidad y "
                 "periodo—, el número que aparece después no se puede discutir.")
    seccion(doc, 2, "8.1. Catálogo de métricas")
    numero = nueva_tabla(doc, "Métrica, cálculo y visualización por pregunta de negocio")
    tabla(doc, ["#", "Pregunta", "Métrica y cálculo", "Unidad", "Visualización"],
          [["1", "¿Cuánta demanda hay y cómo se reparte en el día?",
            "Suma de cnt; media y mediana de cnt por hr", "rentas y rentas/hora",
            "Línea de promedio por hora"],
           ["2", "¿En qué franjas horarias se concentra?",
            "Suma de cnt por franja / total × 100", "% del total",
            "Barras horizontales por franja"],
           ["3", "¿Cambia según el tipo de día?",
            "Media de cnt por tipo_dia; casual / total del día × 100", "rentas/hora y %",
            "Barras comparativas y perfil horario"],
           ["4", "¿Cambia con la temporada y entre 2011 y 2012?",
            "Media de cnt por temporada y por año; variación porcentual", "rentas/hora y %",
            "Barras por temporada y barras agrupadas por año"],
           ["5", "¿Cambia con el clima y la temperatura?",
            "Media de cnt por clima y por rango_temperatura", "rentas/hora",
            "Barras horizontales y línea"],
           ["6", "¿Qué peso tienen casuales y registrados?",
            "Suma de casual y de registered / total × 100", "% del total",
            "Dona de participación y perfil horario"]],
          anchos=[0.8, 4.4, 5.4, 2.4, 3.4], tamano=8.5)
    nota(doc, "Todas las métricas se calculan sobre las horas que sobreviven a los filtros aplicados; "
              "las participaciones se recalculan sobre el total del subconjunto y nunca se reutilizan "
              "las columnas precalculadas sobre el conjunto completo.")

    seccion(doc, 2, "8.2. Las seis visualizaciones")
    parrafo(doc, "Cada figura responde una pregunta y se lee en una frase. Las seis comparten escala de "
                 "color: el tono oscuro señala la categoría que importa en esa comparación y el tono "
                 "claro el resto.")

    figura(doc, figuras["hora"], "Demanda promedio por hora. Cada punto es el promedio de las horas "
                                 "registradas a esa hora del día en todo el periodo.")
    parrafo(doc, f"La curva tiene dos picos —las {int(HORA_TOP['hr'])}:00 y la franja de entrada al "
                 "trabajo— y un valle profundo en la madrugada. La línea punteada marca el promedio "
                 f"general ({num(K['promedio'], 1)} rentas por hora): sirve para ver de un golpe que la "
                 "mayor parte del día está por debajo y que unas pocas horas sostienen el promedio.")

    figura(doc, figuras["franja"], "Participación de cada franja horaria sobre el total de rentas del "
                                   "periodo.")
    parrafo(doc, f"Las dos franjas de hora pico —en naranja— suman {pct(PICO)} de las rentas, mientras "
                 f"la madrugada aporta {pct(FRANJA_FLOJA['participacion_pct'])}. La lectura operativa es "
                 "directa: la discusión sobre capacidad se juega en cuatro horas del día.")

    figura(doc, figuras["tipo_dia"], "Promedio por tipo de día y perfil horario comparado.")
    parrafo(doc, "El promedio por hora es parecido entre laborable y no laborable, pero la forma del día "
                 "no: el laborable tiene dos picos marcados y el no laborable una curva más plana y "
                 "corrida hacia el mediodía. Comparar solo promedios habría ocultado esa diferencia.")

    figura(doc, figuras["temporada"], "Promedio por temporada y comparación entre 2011 y 2012.")
    parrafo(doc, f"La temporada más fuerte es {TEMP_TOP.name} ({num(TEMP_TOP['promedio'], 1)} rentas por "
                 f"hora) y la más floja {TEMP_FLOJA.name} ({num(TEMP_FLOJA['promedio'], 1)}). El segundo "
                 "panel muestra que la diferencia entre años se repite en las cuatro temporadas: el "
                 "crecimiento no es efecto de una estación particular.")

    figura(doc, figuras["clima"], "Promedio por condición climática y por rango de temperatura.")
    parrafo(doc, f"Con cielo despejado el sistema promedia {num(CLIMA_TOP['promedio'], 1)} rentas por "
                 f"hora; con lluvia o nieve ligera, {num(LLUVIA['promedio'], 1)}: una caída de "
                 f"{pct(CAIDA_LLUVIA)}. La temperatura acompaña el mismo patrón, con la demanda "
                 "concentrada en los rangos templado y cálido.")

    figura(doc, figuras["usuario"], "Participación de cada tipo de usuario y perfil horario comparado.")
    parrafo(doc, f"El usuario registrado concentra {pct(REGISTRADO['participacion_pct'])} de las rentas "
                 "y marca los picos de entrada y salida del trabajo; el ocasional, "
                 f"{pct(CASUAL['participacion_pct'])}, se reparte hacia el mediodía y la tarde. Son dos "
                 "usos distintos del mismo sistema, y por eso el informe los trata por separado.")


# ── 9. Resultados y discusión ─────────────────────────────────────────────
def resultados(doc: Document) -> None:
    seccion(doc, 1, "9. Resultados y discusión")
    parrafo(doc, f"En el periodo se registraron {num(TOTAL)} rentas en {num(K['horas'])} horas, con un "
                 f"promedio de {num(K['promedio'], 1)} rentas por hora y una mediana de "
                 f"{num(K['mediana'])}. La diferencia entre ambas cifras es el primer resultado del "
                 "análisis: el sistema no opera a un ritmo constante, sino con horas muy cargadas y "
                 "muchas horas flojas.")

    seccion(doc, 2, "9.1. Distribución por franja horaria")
    filas = []
    for _, fila in FRANJAS.iterrows():
        filas.append([fila["franja_horaria"], num(fila["horas"], 0), num(fila["rentas"], 0),
                      num(fila["promedio"], 1), num(fila["mediana"], 0),
                      pct(fila["participacion_pct"]), num(fila["veces_promedio"], 2)])
    filas.append(["Total", num(K["horas"], 0), num(TOTAL, 0), num(K["promedio"], 1),
                  num(K["mediana"], 0), pct(100.0), num(1.0, 2)])
    numero = nueva_tabla(doc, "Demanda por franja horaria")
    tabla(doc, ["Franja", "Horas", "Rentas", "Promedio", "Mediana", "Participación", "Veces el promedio"],
          filas, anchos=[2.9, 2.0, 2.6, 2.2, 2.1, 2.4, 2.4],
          alinear_derecha=[1, 2, 3, 4, 5, 6], tamano=8.5)
    nota(doc, "Promedio y mediana en rentas por hora. 'Veces el promedio' compara el promedio de la "
              "franja con el promedio general del periodo.")
    parrafo(doc, f"La franja de {FRANJA_TOP['franja_horaria']} concentra "
                 f"{pct(FRANJA_TOP['participacion_pct'])} de las rentas con "
                 f"{num(FRANJA_TOP['promedio'], 1)} rentas por hora, "
                 f"{num(FRANJA_TOP['veces_promedio'], 1)} veces el promedio general. La madrugada, en el "
                 f"otro extremo, aporta {pct(FRANJA_FLOJA['participacion_pct'])}. Entre ambas hay un "
                 "factor de quince en intensidad: es la diferencia que justifica planear la operación "
                 "por franja y no por día.")
    parrafo(doc, f"El detalle por hora confirma la forma de la curva: las {int(HORA_TOP['hr'])}:00 son la "
                 f"hora más cargada con {num(HORA_TOP['promedio'], 1)} rentas por hora, y las "
                 f"{int(HORA_FLOJA['hr'])}:00 la más floja con {num(HORA_FLOJA['promedio'], 1)}. En "
                 "términos operativos, la ventana crítica va de las 16:00 a las 19:00 y la ventana de "
                 "mantenimiento, de las 0:00 a las 5:00.")

    seccion(doc, 2, "9.2. Tipo de día")
    numero = nueva_tabla(doc, "Comparación entre día laborable y no laborable")
    filas = []
    for nombre, fila in TIPO_DIA.iterrows():
        filas.append([nombre, num(fila["horas"], 0), num(fila["rentas"], 0), num(fila["promedio"], 1),
                      num(fila["mediana"], 0), pct(fila["participacion_pct"]), pct(fila["pct_casual"])])
    numero_tabla = numero
    tabla(doc, ["Tipo de día", "Horas", "Rentas", "Promedio", "Mediana", "Participación", "% casual"],
          filas, anchos=[2.6, 2.2, 2.6, 2.2, 2.1, 2.6, 2.2],
          alinear_derecha=[1, 2, 3, 4, 5, 6], tamano=8.5)
    nota(doc, "Promedio y mediana en rentas por hora; '% casual' es la proporción de rentas de usuarios "
              "sin suscripción dentro de ese tipo de día.")
    parrafo(doc, f"El promedio por hora es mayor en día laborable "
                 f"({num(TIPO_DIA.loc['Laborable', 'promedio'], 1)}) que en no laborable "
                 f"({num(TIPO_DIA.loc['No laborable', 'promedio'], 1)}), pero la diferencia más "
                 f"informativa es la composición: el usuario ocasional pasa de "
                 f"{pct(PCT_CASUAL_LAB)} a {pct(PCT_CASUAL_NOLAB)} del total del día. El fin de semana "
                 "no mueve tanto el volumen como el tipo de uso: deja de ser un sistema de movilidad "
                 "cotidiana para volverse, en parte, recreativo.")
    parrafo(doc, "Ese cambio de composición explica por qué los promedios se parecen aunque los "
                 "perfiles horarios difieran: en el día laborable la demanda se concentra en dos picos "
                 "cortos; en el no laborable se reparte en una meseta más larga. Un operador que solo "
                 "mire el promedio concluiría que el fin de semana es 'parecido'; al mirar la forma "
                 "descubre que necesita otra distribución del personal.")

    seccion(doc, 2, "9.3. Temporada y año")
    numero = nueva_tabla(doc, "Demanda por temporada")
    filas = []
    for nombre, fila in TEMPORADA.iterrows():
        filas.append([nombre, num(fila["horas"], 0), num(fila["rentas"], 0), num(fila["promedio"], 1),
                      num(fila["mediana"], 0), pct(fila["participacion_pct"])])
    tabla(doc, ["Temporada", "Horas", "Rentas", "Promedio", "Mediana", "Participación"], filas,
          anchos=[3.0, 2.4, 3.0, 2.6, 2.4, 2.8], alinear_derecha=[1, 2, 3, 4, 5], tamano=8.5)
    nota(doc, "Temporadas según la codificación del conjunto original (1 primavera, 2 verano, "
              "3 otoño, 4 invierno).")

    numero = nueva_tabla(doc, "Demanda por año y variación porcentual")
    filas = []
    for anio, fila in ANIO.iterrows():
        filas.append([str(anio), num(fila["horas"], 0), num(fila["rentas"], 0), num(fila["promedio"], 1),
                      pct(fila["participacion_pct"])])
    tabla(doc, ["Año", "Horas", "Rentas", "Promedio", "% del periodo"], filas,
          anchos=[3.0, 3.0, 3.4, 3.0, 3.0], alinear_derecha=[1, 2, 3, 4], tamano=8.5)
    nota(doc, f"El promedio por hora creció {pct(CRECIMIENTO)} entre 2011 y 2012; la variación se repite "
              "en las cuatro temporadas (Tabla 14).")

    numero = nueva_tabla(doc, "Promedio por temporada y año, con variación")
    filas = []
    for nombre, fila in TEMP_ANIO.iterrows():
        filas.append([nombre, num(fila[2011], 1), num(fila[2012], 1), pct(fila["variacion_pct"])])
    tabla(doc, ["Temporada", "2011", "2012", "Variación"], filas,
          anchos=[4.0, 3.0, 3.0, 3.0], alinear_derecha=[1, 2, 3], tamano=8.5)
    nota(doc, "Promedio en rentas por hora. La variación se calcula sobre el promedio, no sobre el "
              "volumen, para no mezclar el crecimiento con la cantidad de horas registradas.")

    parrafo(doc, f"{TEMP_TOP.name} es la temporada más fuerte ({num(TEMP_TOP['promedio'], 1)} rentas por "
                 f"hora) y {TEMP_FLOJA.name} la más floja ({num(TEMP_FLOJA['promedio'], 1)}). La "
                 f"diferencia entre años es grande y consistente: el promedio por hora pasó de "
                 f"{num(ANIO.loc[2011, 'promedio'], 1)} a {num(ANIO.loc[2012, 'promedio'], 1)}, un "
                 f"{pct(CRECIMIENTO)} más, y el aumento aparece en las cuatro temporadas.")
    parrafo(doc, "Leer ese crecimiento como 'la gente usa más la bicicleta' sería exceder los datos. El "
                 "sistema pudo ampliar su red de estaciones, sumar suscriptores o cambiar sus tarifas; el "
                 "conjunto no trae ninguna de esas variables. Lo que el análisis sí sostiene es que la "
                 "demanda observada creció de forma generalizada, y que cualquier proyección ingenua con "
                 "el promedio de dos años mezclaría crecimiento del sistema con estacionalidad.")

    seccion(doc, 2, "9.4. Clima y temperatura")
    numero = nueva_tabla(doc, "Demanda por condición climática")
    filas = []
    for nombre, fila in CLIMA.iterrows():
        filas.append([nombre, num(fila["horas"], 0), num(fila["rentas"], 0), num(fila["promedio"], 1),
                      num(fila["mediana"], 0), pct(fila["participacion_pct"])])
    tabla(doc, ["Condición", "Horas", "Rentas", "Promedio", "Mediana", "Participación"], filas,
          anchos=[4.2, 2.2, 2.8, 2.4, 2.2, 2.6], alinear_derecha=[1, 2, 3, 4, 5], tamano=8.5)
    nota(doc, "La categoría 'lluvia fuerte o tormenta' tiene solo 3 horas registradas: su promedio no es "
              "representativo y se reporta por completitud, no como hallazgo.")

    numero = nueva_tabla(doc, "Demanda por rango de temperatura")
    filas = []
    for nombre, fila in TEMPERATURA.iterrows():
        filas.append([nombre, num(fila["horas"], 0), num(fila["promedio"], 1), num(fila["mediana"], 0),
                      pct(fila["participacion_pct"])])
    tabla(doc, ["Rango de temperatura", "Horas", "Promedio", "Mediana", "Participación"], filas,
          anchos=[5.0, 2.6, 2.8, 2.6, 3.0], alinear_derecha=[1, 2, 3, 4], tamano=8.5)
    nota(doc, "Rangos construidos en la etapa de enriquecimiento con cortes en 5, 15 y 25 °C.")

    parrafo(doc, f"Con cielo despejado el promedio es {num(CLIMA_TOP['promedio'], 1)} rentas por hora; con "
                 f"lluvia o nieve ligera baja a {num(LLUVIA['promedio'], 1)}, una caída de "
                 f"{pct(CAIDA_LLUVIA)}. La mediana confirma que no es un efecto de pocas horas extremas: "
                 f"pasa de {num(CLIMA_TOP['mediana'], 0)} a {num(LLUVIA['mediana'], 0)}. La temperatura "
                 "sigue la misma dirección, con la demanda alta en los rangos templado y cálido y baja en "
                 "el frío.")
    parrafo(doc, "La interpretación tiene un límite claro: clima, temporada y tipo de día se mueven "
                 "juntos. Las horas de lluvia se concentran en determinadas estaciones y en determinados "
                 "días, así que la caída observada no se puede atribuir en su totalidad al clima. El "
                 "informe reporta la asociación y evita la frase causal, que es exactamente el error que "
                 "un análisis descriptivo debe evitar.")

    seccion(doc, 2, "9.5. Tipo de usuario")
    numero = nueva_tabla(doc, "Participación de cada tipo de usuario")
    filas = []
    for nombre, fila in USUARIO.iterrows():
        filas.append([nombre, num(fila["rentas"], 0), num(fila["promedio_por_hora"], 1),
                      pct(fila["participacion_pct"])])
    filas.append(["Total", num(TOTAL, 0), num(K["promedio"], 1), pct(100.0)])
    tabla(doc, ["Tipo de usuario", "Rentas", "Promedio por hora", "Participación"], filas,
          anchos=[4.4, 4.0, 4.0, 3.6], alinear_derecha=[1, 2, 3], tamano=9)
    nota(doc, "Promedio por hora calculado sobre el total de horas del periodo.")

    numero = nueva_tabla(doc, "Composición del usuario según el tipo de día")
    filas = []
    for nombre, fila in USUARIO_DIA.iterrows():
        filas.append([nombre, num(fila["casual"], 0), num(fila["registrado"], 0),
                      pct(fila["pct_casual"]), pct(fila["pct_registrado"])])
    tabla(doc, ["Tipo de día", "Rentas casuales", "Rentas registradas", "% casual", "% registrado"], filas,
          anchos=[3.0, 3.6, 3.8, 2.8, 3.0], alinear_derecha=[1, 2, 3, 4], tamano=9)
    nota(doc, "Los porcentajes se calculan dentro de cada tipo de día, no sobre el total del periodo.")

    parrafo(doc, f"El usuario registrado concentra {pct(REGISTRADO['participacion_pct'])} de las rentas "
                 f"({num(REGISTRADO['rentas'], 0)}) y el ocasional "
                 f"{pct(CASUAL['participacion_pct'])} ({num(CASUAL['rentas'], 0)}). La proporción cambia "
                 f"según el día: el ocasional representa {pct(PCT_CASUAL_LAB)} en día laborable y "
                 f"{pct(PCT_CASUAL_NOLAB)} en no laborable.")
    parrafo(doc, "Los perfiles horarios explican el resto. El registrado dibuja dos picos —entrada y "
                 "salida del trabajo—, mientras el ocasional se distribuye en una meseta de mediodía y "
                 "tarde. La consecuencia para la operación es que no hay un solo usuario al que servir: "
                 "conviven un servicio de movilidad y un servicio de esparcimiento, y cada uno exige "
                 "capacidad en momentos distintos.")

    seccion(doc, 2, "9.6. Concentración diaria y días extremos")
    numero = nueva_tabla(doc, "Días de mayor demanda del periodo")
    filas = []
    for _, fila in DIAS_TOP.iterrows():
        filas.append([pd.Timestamp(fila["dteday"]).strftime("%d/%m/%Y"), num(fila["rentas"], 0),
                      num(fila["horas"], 0)])
    tabla(doc, ["Fecha", "Rentas del día", "Horas registradas"], filas,
          anchos=[4.4, 4.4, 4.4], alinear_derecha=[1, 2], tamano=9)
    nota(doc, "Los cinco días de mayor volumen; todos tienen las 24 horas registradas, así que el total "
              "no está afectado por horas faltantes.")

    parrafo(doc, f"En el día mediano, la hora más cargada concentra {pct(CONCENTRACION['mediana_pct'])} "
                 f"de las rentas de ese día; en el cuartil superior de días esa proporción llega a "
                 f"{pct(CONCENTRACION['p75_pct'])}. Es una forma distinta de medir lo mismo: la demanda "
                 "no solo se concentra en ciertas horas, sino que en algunos días se concentra más que "
                 "en otros, lo que sugiere días con un pico operativo más exigente.")
    parrafo(doc, "Los días de mayor volumen caen en septiembre y marzo de 2012, con más de ocho mil "
                 "rentas diarias. Son útiles como referencia de capacidad: si la operación funciona en "
                 "esos días, funciona en la mayoría de los demás.")

    seccion(doc, 2, "9.7. Discusión integrada")
    parrafo(doc, "Leídas juntas, las seis respuestas describen un sistema con una demanda predecible en "
                 "su forma y creciente en su volumen. La forma la definen la hora y el tipo de día: dos "
                 "picos en día laborable, meseta en fin de semana, valle nocturno. El volumen lo "
                 "modifican la temporada y el clima, con otoño y verano por encima de primavera y con "
                 "una caída clara en los días de lluvia.")
    parrafo(doc, "Esa combinación es la que hace útil el análisis para la operación. Si la demanda fuera "
                 "plana, bastaría con una flota fija; si fuera impredecible, no habría nada que planear. "
                 "El resultado es un patrón estable con variaciones conocidas, que es justamente el "
                 "insumo que necesita quien decide turnos, reubicación y mantenimiento.")
    parrafo(doc, "El contraste con la literatura de sistemas de bicicletas compartidas es consistente: "
                 "los estudios sobre estos sistemas describen una demanda bimodal asociada a los viajes "
                 "pendulares y una sensibilidad al clima y a la estación. El aporte de este trabajo no es "
                 "descubrir ese patrón, sino medirlo con los datos disponibles, documentar las decisiones "
                 "de preparación y dejarlo disponible en una herramienta que se puede consultar sin "
                 "saber programar.")
    parrafo(doc, "Lo que el análisis no permite afirmar es igual de importante. No se puede decir que el "
                 "clima cause la caída —solo que se asocia—, ni que el crecimiento entre años se deba al "
                 "comportamiento de los usuarios, ni que la demanda observada sea la demanda real: el "
                 "sistema registra los viajes que ocurrieron, no los que se frustraron por falta de "
                 "bicicletas. Y no se puede hablar de rentabilidad: no hay precios ni costos en los "
                 "datos.")


# ── 10. Aplicación ────────────────────────────────────────────────────────
def aplicacion(doc: Document) -> None:
    seccion(doc, 1, "10. Aplicación de visualización en Streamlit")
    parrafo(doc, "La aplicación es la forma en que el análisis llega a quien toma las decisiones. Está "
                 "publicada en Streamlit Community Cloud, vinculada al mismo repositorio del proyecto, y "
                 "se abre desde cualquier navegador sin instalar nada ni crear cuenta.")
    parrafo_enlace(doc, "Dirección de la aplicación: ", APP, APP, ".")
    seccion(doc, 2, "10.1. Estructura y navegación")
    parrafo(doc, "La pantalla se organiza en tres zonas. En la barra lateral están los filtros —periodo, "
                 "temporada, tipo de día y clima— y el recorrido por las secciones: un resumen del "
                 "periodo y una entrada por cada pregunta. En el cuerpo, cada sección repite la misma "
                 "estructura: la pregunta, la métrica con su unidad, los indicadores del periodo "
                 "filtrado, el gráfico y tres bloques de lectura —qué muestran los datos, qué decisión "
                 "pueden apoyar y cuál es su limitación—. Al pie, la fuente de los datos y la "
                 "identificación del grupo.")
    parrafo(doc, "Los filtros recalculan todos los indicadores y gráficos sobre el subconjunto "
                 "seleccionado. Esa decisión tiene un costo de interpretación que la aplicación hace "
                 "explícito: al filtrar, las participaciones se recalculan sobre el nuevo total y el "
                 "periodo mostrado cambia en la cabecera, de modo que nunca se compara una cifra filtrada "
                 "contra un total sin filtrar.")
    if CAPTURA_APP.exists():
        figura(doc, CAPTURA_APP, "Pantalla de resumen de la aplicación publicada: indicadores del "
                                 "periodo, gráficos principales y navegación por las seis preguntas.",
               ancho_cm=13.5)

    seccion(doc, 2, "10.2. Cómo se garantiza que la aplicación y el documento digan lo mismo")
    parrafo(doc, "Todas las métricas viven en un módulo único del repositorio. La aplicación, el "
                 "documento y el script de verificación llaman a ese módulo; ninguno recalcula por su "
                 "cuenta. Si una definición cambia, cambia en un solo lugar y el efecto se propaga a todo "
                 "lo que la usa.")
    parrafo(doc, "Sobre esa base hay dos controles automáticos. El primero recalcula las métricas del "
                 "periodo completo y las compara contra las tablas del análisis: 53 comprobaciones que "
                 "incluyen totales, promedios, medianas y participaciones, además de la coherencia "
                 "aritmética entre rentas y tipos de usuario. El segundo ejecuta las siete vistas de la "
                 "aplicación y verifica que ninguna lance errores, incluso con filtros que dejan pocos "
                 "registros.")
    numero = nueva_tabla(doc, "Controles automáticos del proyecto")
    tabla(doc, ["Control", "Qué verifica", "Cómo se ejecuta"],
          [["Verificación de métricas", "Que las cifras calculadas coincidan con las tablas del análisis",
            "python AE4/verificar_metricas.py"],
           ["Prueba de la aplicación", "Que las siete vistas se ejecuten sin errores",
            "python AE4/probar_app.py"],
           ["Ejecución de notebooks", "Que los notebooks corran desde cero con el código vigente",
            "GitHub Actions en cada push a main"]],
          anchos=[4.0, 7.0, 5.0], tamano=8.5)
    nota(doc, "Los tres controles forman parte del repositorio y se pueden reproducir en cualquier "
              "máquina con las dependencias instaladas.")

    seccion(doc, 2, "10.3. Uso previsto en la presentación")
    parrafo(doc, "La aplicación está pensada para demostrarse en vivo en diez minutos: el resumen del "
                 "periodo sitúa el problema y las cifras generales, y luego cada pregunta se abre con un "
                 "filtro distinto para mostrar que los indicadores responden. La recomendación operativa "
                 "es abrirla unos minutos antes de la presentación, porque los servicios gratuitos de "
                 "alojamiento suspenden las aplicaciones inactivas y tardan en reactivarse.")


# ── 11. Conclusiones ──────────────────────────────────────────────────────
def conclusiones(doc: Document) -> None:
    seccion(doc, 1, "11. Conclusiones y recomendaciones")
    parrafo(doc, "El proyecto respondió las seis preguntas de negocio y dejó el resultado en una "
                 "herramienta consultable. Las conclusiones se ordenan de lo general a lo operativo.")
    seccion(doc, 2, "11.1. Conclusiones sobre la demanda")
    vinetas(doc, [
        f"La demanda no es uniforme. En {num(K['dias'])} días se registraron {num(TOTAL)} rentas, con un "
        f"promedio de {num(K['promedio'], 1)} por hora y una mediana de {num(K['mediana'])}: la hora "
        "típica está muy por debajo del promedio, porque unas pocas horas cargan el resultado.",
        f"La concentración es horaria. La franja de {FRANJA_TOP['franja_horaria']} aporta "
        f"{pct(FRANJA_TOP['participacion_pct'])} de las rentas y las dos horas pico suman {pct(PICO)}; "
        f"la madrugada, en cambio, solo {pct(FRANJA_FLOJA['participacion_pct'])}.",
        f"El tipo de día cambia el perfil, no solo el volumen. Los promedios son parecidos "
        f"({num(TIPO_DIA.loc['Laborable', 'promedio'], 1)} frente a "
        f"{num(TIPO_DIA.loc['No laborable', 'promedio'], 1)}), pero el laborable tiene dos picos y el no "
        "laborable una meseta, y el peso del usuario ocasional se duplica.",
        f"La estacionalidad y el clima modifican la intensidad. {TEMP_TOP.name} supera a "
        f"{TEMP_FLOJA.name} en {num(TEMP_TOP['promedio'] - TEMP_FLOJA['promedio'], 1)} rentas por hora, y "
        f"la lluvia coincide con una caída de {pct(CAIDA_LLUVIA)} frente al cielo despejado.",
        f"El sistema creció entre los dos años: {pct(CRECIMIENTO)} más de promedio por hora, con el "
        "aumento presente en las cuatro temporadas.",
        f"El usuario registrado sostiene el servicio ({pct(REGISTRADO['participacion_pct'])} de las "
        f"rentas) y define los picos; el ocasional ({pct(CASUAL['participacion_pct'])}) crece los fines "
        "de semana y se concentra en el mediodía.",
    ])
    seccion(doc, 2, "11.2. Recomendaciones para la operación")
    vinetas(doc, [
        "Dimensionar turnos y reubicación por franja horaria y no por día: la ventana de 16:00 a 19:00 "
        "concentra la mayor presión y la de 0:00 a 5:00 es la de menor actividad.",
        "Tratar el fin de semana como una operación distinta: cobertura más continua, con personal "
        "distribuido entre mediodía y tarde en lugar de concentrado en dos picos.",
        "Programar mantenimiento preventivo en la madrugada y en temporada baja, cuando la interrupción "
        "del servicio tiene menor costo operativo.",
        "Anticipar capacidad con la estacionalidad y el pronóstico del clima: reforzar flota y personal "
        "en la temporada alta y en días secos, y ajustar la reubicación en días de lluvia.",
        "Abrir la aplicación en las reuniones de operación: permite contrastar una decisión con la cifra "
        "que la sustenta en el momento, sin depender de un informe previo.",
    ])
    seccion(doc, 2, "11.3. Conclusiones sobre el proceso")
    parrafo(doc, "El trabajo deja tres aprendizajes metodológicos. El primero es que la unidad de análisis "
                 "define el alcance: al trabajar con horas y no con viajes, el proyecto describe la "
                 "operación y no el comportamiento individual, y eso debe decirse desde la introducción. "
                 "El segundo es que documentar lo que no se encuentra también es documentar: las reglas de "
                 "calidad que no hallaron problemas respaldan la confianza en el conjunto. El tercero es "
                 "que un análisis se vuelve útil cuando se puede consultar: la aplicación y los controles "
                 "automáticos convierten un notebook en una herramienta que otra persona puede usar y "
                 "verificar.")


# ── 12. Limitaciones ──────────────────────────────────────────────────────
def limitaciones(doc: Document) -> None:
    seccion(doc, 1, "12. Limitaciones del análisis")
    parrafo(doc, "Las limitaciones se declaran porque acotan lo que el informe puede afirmar. Ninguna "
                 "invalida los resultados; todas indican hasta dónde llegan.")
    vinetas(doc, [
        "Demanda satisfecha, no demanda real. El conjunto registra los viajes que ocurrieron; no incluye "
        "las personas que no encontraron bicicleta. La demanda puede estar subestimada, sobre todo en "
        "horas pico.",
        "Sin información de oferta. No hay datos de bicicletas disponibles, anclajes ni estaciones, así "
        "que no se puede analizar la capacidad ni la redistribución necesaria.",
        "Sin usuarios identificables. casual y registered son tipos de renta, no personas: no se puede "
        "calcular frecuencia por usuario, retención ni perfiles individuales.",
        "Horas faltantes. Faltan " + num(K["horas_faltantes"]) + " horas de "
        + num(K["horas_esperadas"]) + ". No se imputaron; los promedios se calculan sobre las horas "
        "existentes y cada tabla informa cuántas lo sostienen.",
        "Categorías con pocos registros. La condición de lluvia fuerte o tormenta aparece solo en 3 "
        "horas: su promedio se reporta por completitud, no como hallazgo.",
        "Dos años y una ciudad. El periodo (2011-2012) y el sistema (Washington D. C.) no permiten "
        "generalizar a otras ciudades ni proyectar con confianza; el crecimiento observado no se puede "
        "atribuir a una causa específica.",
        "Asociación, no causalidad. Clima, temporada y tipo de día se mueven juntos; el informe describe "
        "asociaciones y evita atribuir causas que el diseño no puede aislar.",
        "Sin dimensión económica. No hay precios, tarifas ni costos: el informe habla de cantidad de "
        "rentas y no de ingresos ni de rentabilidad.",
    ])


# ── 13. Referencias ───────────────────────────────────────────────────────
def referencias(doc: Document) -> None:
    seccion(doc, 1, "13. Referencias")
    refs = [
        "Fanaee-T, H. y Gama, J. (2013). Event labeling combining ensemble detectors and background "
        "knowledge. Progress in Artificial Intelligence, 2, 113-127. Springer. "
        "https://doi.org/10.1007/s13748-013-0040-3",
        "UCI Machine Learning Repository. (2013). Bike Sharing Dataset (id 275). University of "
        "California, Irvine. https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset",
        "Provost, F. y Fawcett, T. (2013). Data science for business: what you need to know about data "
        "mining and data-analytic thinking. O'Reilly Media.",
        "McKinney, W. (2010). Data structures for statistical computing in Python. Proceedings of the "
        "9th Python in Science Conference, 56-61.",
        "Knaflic, C. N. (2015). Storytelling with data: a data visualization guide for business "
        "professionals. Wiley.",
        "Streamlit. (2026). Streamlit documentation: create and share data apps. "
        "https://docs.streamlit.io",
        "pandas development team. (2026). pandas documentation. https://pandas.pydata.org/docs/",
        "Hugging Face. (2026). Datasets library documentation. https://huggingface.co/docs/datasets",
    ]
    for ref in refs:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.space_after = Pt(8)
        run = p.add_run(ref)
        run.font.size = Pt(10)


# ── Anexos ────────────────────────────────────────────────────────────────
def anexos(doc: Document) -> None:
    seccion(doc, 1, "Anexo A. Enlaces del proyecto")
    parrafo_enlace(doc, "Repositorio del proyecto: ", REPO, REPO)
    parrafo_enlace(doc, "Aplicación publicada: ", APP, APP)
    parrafo(doc, "El repositorio es público y contiene el código de las cuatro etapas, los notebooks "
                 "ejecutados, las tablas de resultados, el conjunto preparado, la aplicación y este "
                 "documento. La aplicación está vinculada a ese repositorio y se reconstruye cuando el "
                 "repositorio cambia.")

    seccion(doc, 1, "Anexo B. Estructura del repositorio")
    estructura = [
        ("AE4/", "Aplicación, métricas, controles y documento final"),
        ("AE4/app.py", "Aplicación en Streamlit"),
        ("AE4/metricas.py", "Cálculo único de las métricas del proyecto"),
        ("AE4/verificar_metricas.py", "Contraste de cifras contra las tablas del análisis"),
        ("AE4/probar_app.py", "Prueba automática de las siete vistas"),
        ("AE3/", "Transformación, enriquecimiento y tablas de resultados"),
        ("AE3/datos/dataset_preparado.csv", "Conjunto final (17.379 × 40)"),
        ("AE3/resultados/", "17 tablas en CSV y el reporte descriptivo"),
        ("AE2/", "Documento de la etapa 1 y notebook de reconocimiento"),
        ("EA1/", "Notebook de carga y resumen descriptivo"),
        ("src/clases_po/", "Clases reutilizables del proyecto"),
        ("requirements.txt", "Dependencias del proyecto"),
        (".github/workflows/", "Ejecución automática de los notebooks"),
    ]
    numero = nueva_tabla(doc, "Estructura de carpetas del repositorio")
    tabla(doc, ["Ruta", "Contenido"], [[r, d] for r, d in estructura],
          anchos=[7.6, 8.4], tamano=8.5)

    seccion(doc, 1, "Anexo C. Cómo reproducir el análisis")
    parrafo(doc, "Los comandos siguientes se ejecutan desde la raíz del repositorio, con las "
                 "dependencias instaladas:")
    for comando, descripcion in [
        ("pip install -r requirements.txt", "Instala las dependencias del proyecto"),
        ("streamlit run AE4/app.py", "Ejecuta la aplicación en local"),
        ("python AE4/verificar_metricas.py", "Verifica que las cifras coincidan con las tablas"),
        ("python AE4/probar_app.py", "Comprueba que las siete vistas funcionan"),
        ("python AE4/construir_documento_final.py", "Regenera este documento en Word y PDF"),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.left_indent = Cm(0.6)
        run = p.add_run(comando)
        run.font.name = "Consolas"
        run.font.size = Pt(9.5)
        run2 = p.add_run("  —  " + descripcion)
        run2.font.size = Pt(9.5)
    parrafo(doc, "Los notebooks se ejecutan cada uno desde su carpeta, porque sus rutas de salida son "
                 "relativas. El flujo de integración continua repite esa ejecución en cada cambio "
                 "publicado en la rama principal.")


# ── construcción ──────────────────────────────────────────────────────────
def construir(paginas: dict[str, int] | None) -> Path:
    global NUM_TABLA, NUM_FIGURA
    ENTRADAS.clear()
    TABLAS.clear()
    FIGURAS_DOC.clear()
    NUM_TABLA = 0
    NUM_FIGURA = 0

    figuras = generar_figuras()

    doc = Document()
    configurar(doc)
    pie_de_pagina(doc)
    portada(doc)

    # Marca de posición: el índice se escribe al final (cuando ya se conocen
    # los títulos) y se inserta justo aquí, antes del cuerpo.
    marca = doc.add_paragraph()

    introduccion(doc)
    necesidad(doc)
    justificacion(doc)
    objetivos(doc)
    marco_teorico(doc)
    metodologia(doc)
    transformacion(doc)
    metricas_visualizaciones(doc, figuras)
    resultados(doc)
    aplicacion(doc)
    conclusiones(doc)
    limitaciones(doc)
    referencias(doc)
    anexos(doc)

    indice(doc, paginas, marca)
    marca._p.getparent().remove(marca._p)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    doc.save(SALIDA)
    return SALIDA


def a_pdf(docx: Path) -> Path:
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
                    str(docx.parent), str(docx)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return docx.with_suffix(".pdf")


def paginas_reales(pdf: Path) -> dict[str, int]:
    total = int(re.search(r"Pages:\s+(\d+)",
                          subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    textos = {}
    for pagina in range(1, total + 1):
        salida = subprocess.run(["pdftotext", "-f", str(pagina), "-l", str(pagina), "-layout", str(pdf), "-"],
                                capture_output=True, text=True).stdout
        textos[pagina] = re.sub(r"\s+", " ", salida)
    paginas_indice = [p for p, t in textos.items() if "Índice de figuras" in t]
    inicio = (max(paginas_indice) + 1) if paginas_indice else 1

    encontradas = {}
    for entrada in ENTRADAS:
        clave = re.sub(r"\s+", " ", entrada["clave"])[:60]
        for pagina in range(inicio, total + 1):
            if clave in textos[pagina]:
                encontradas[entrada["titulo"]] = pagina
                break
    return encontradas


def main() -> None:
    docx = construir(None)
    pdf = a_pdf(docx)
    paginas = paginas_reales(pdf)
    faltantes = [e["titulo"] for e in ENTRADAS if e["titulo"] not in paginas]
    if faltantes:
        print("AVISO: secciones sin página detectada:", faltantes)

    for intento in range(3):
        docx = construir(paginas)
        pdf = a_pdf(docx)
        nuevas = paginas_reales(pdf)
        if nuevas == paginas:
            print(f"Índice estable en el intento {intento + 1}")
            break
        paginas = nuevas
    else:
        print("AVISO: el índice no se estabilizó")

    total = re.search(r"Pages:\s+(\d+)",
                      subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1)
    print(f"Documento: {docx}")
    print(f"PDF: {pdf} ({total} páginas)")
    print(f"Secciones en el índice: {len(ENTRADAS)} | tablas: {len(TABLAS)} | figuras: {len(FIGURAS_DOC)}")
    for e in ENTRADAS:
        print(f"  p.{paginas.get(e['titulo'], '?'):>3}  {'  ' * (e['nivel'] - 1)}{e['titulo']}")


if __name__ == "__main__":
    main()
