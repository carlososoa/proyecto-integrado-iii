#!/usr/bin/env python3
"""Convierte las guías en Markdown a PDF con la tipografía del informe.

Uso:
    python AE4/exportar_guias.py

Genera, en AE4/documento/:
    GUIA_EQUIPO.pdf            — datos, proceso y preguntas del docente
    GUION_PRESENTACION.pdf     — guion cronometrado de la sustentación
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "AE4" / "documento"

AZUL = RGBColor(0x1F, 0x3B, 0x63)
GRIS = RGBColor(0x55, 0x55, 0x55)

DOCUMENTOS = [
    ("GUIA_EQUIPO.md", "GUIA_EQUIPO.pdf",
     "Guía del equipo — Proyecto Integrado III · AE_Grupo 3"),
    ("GUION_PRESENTACION.md", "GUION_PRESENTACION.pdf",
     "Guion de la sustentación — Proyecto Integrado III · AE_Grupo 3"),
]


def configurar(doc: Document) -> None:
    seccion = doc.sections[0]
    seccion.page_width, seccion.page_height = Cm(21), Cm(29.7)
    for lado in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(seccion, lado, Cm(2.2))
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.space_after = Pt(5)
    for nombre, tamano in (("Heading 1", 15), ("Heading 2", 12), ("Heading 3", 11)):
        estilo = doc.styles[nombre]
        estilo.font.name = "Calibri"
        estilo.font.size = Pt(tamano)
        estilo.font.bold = True
        estilo.font.color.rgb = AZUL
        estilo.paragraph_format.space_before = Pt(11)
        estilo.paragraph_format.space_after = Pt(4)


def campo_pie(doc: Document, texto: str) -> None:
    pie = doc.sections[0].footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = pie.add_run(texto + " · Página ")
    run.font.size = Pt(8)
    run.font.color.rgb = GRIS
    run2 = pie.add_run()
    inicio = OxmlElement("w:fldChar"); inicio.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = " PAGE "
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    valor = OxmlElement("w:t"); valor.text = "1"
    fin = OxmlElement("w:fldChar"); fin.set(qn("w:fldCharType"), "end")
    for el in (inicio, instr, sep, valor, fin):
        run2._r.append(el)
    run2.font.size = Pt(8)
    run2.font.color.rgb = GRIS


def runs_con_formato(parrafo, texto: str) -> None:
    """Interpreta **negrita** y `código` dentro de un párrafo."""
    for trozo in re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)", texto):
        if not trozo:
            continue
        if trozo.startswith("**") and trozo.endswith("**"):
            run = parrafo.add_run(trozo[2:-2])
            run.bold = True
        elif trozo.startswith("*") and trozo.endswith("*") and len(trozo) > 2:
            run = parrafo.add_run(trozo[1:-1])
            run.italic = True
        elif trozo.startswith("`") and trozo.endswith("`"):
            run = parrafo.add_run(trozo[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
        else:
            parrafo.add_run(trozo)


def tabla_md(doc: Document, filas: list[str]) -> None:
    filas_limpias = []
    for linea in filas:
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in celdas if c):
            continue  # separador de encabezado
        filas_limpias.append(celdas)
    if not filas_limpias:
        return
    columnas = max(len(f) for f in filas_limpias)
    t = doc.add_table(rows=1, cols=columnas)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    t._tbl.tblPr.append(layout)
    ancho_tabla = OxmlElement("w:tblW")
    ancho_tabla.set(qn("w:type"), "dxa")
    ancho_tabla.set(qn("w:w"), str(int(16.4 / 2.54 * 1440)))
    t._tbl.tblPr.append(ancho_tabla)
    if columnas == 2:
        anchos = [6.2, 10.2]
    else:
        anchos = [16.4 / columnas] * columnas

    for i, texto in enumerate(filas_limpias[0]):
        celda = t.rows[0].cells[i]
        celda.text = ""
        p = celda.paragraphs[0]
        run = p.add_run(texto)
        run.bold = True
        run.font.size = Pt(8.5)
        sombra = OxmlElement("w:shd")
        sombra.set(qn("w:val"), "clear")
        sombra.set(qn("w:color"), "auto")
        sombra.set(qn("w:fill"), "DCE6F1")
        celda._tc.get_or_add_tcPr().append(sombra)

    for fila in filas_limpias[1:]:
        celdas = t.add_row().cells
        for i in range(columnas):
            texto = fila[i] if i < len(fila) else ""
            celdas[i].text = ""
            p = celdas[i].paragraphs[0]
            runs_con_formato(p, texto)
            for run in p.runs:
                run.font.size = Pt(8.5)

    # El ancho hay que fijarlo en la grilla, en la columna y en cada celda:
    # LibreOffice ignora el de la celda si la grilla no coincide.
    for i, ancho in enumerate(anchos):
        t.columns[i].width = Cm(ancho)
    for fila in t.rows:
        for i, ancho in enumerate(anchos):
            fila.cells[i].width = Cm(ancho)

    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def convertir(md: Path, destino: Path, pie: str) -> Path:
    doc = Document()
    configurar(doc)
    campo_pie(doc, pie)

    lineas = md.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lineas):
        linea = lineas[i].rstrip()

        if not linea.strip():
            i += 1
            continue

        if linea.startswith("|"):
            bloque = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                bloque.append(lineas[i])
                i += 1
            tabla_md(doc, bloque)
            continue

        if linea.startswith("### "):
            doc.add_heading(linea[4:].strip(), level=3)
        elif linea.startswith("## "):
            doc.add_heading(linea[3:].strip(), level=2)
        elif linea.startswith("# "):
            doc.add_heading(linea[2:].strip(), level=1)
        elif linea.startswith("> "):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            runs_con_formato(p, linea[2:].strip())
            for run in p.runs:
                run.italic = True
                run.font.color.rgb = GRIS
        elif re.match(r"^\s*[-*] ", linea):
            p = doc.add_paragraph(style="List Bullet")
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(2)
            runs_con_formato(p, re.sub(r"^\s*[-*] ", "", linea))
        elif re.match(r"^\s*\d+\. ", linea):
            p = doc.add_paragraph(style="List Number")
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(2)
            runs_con_formato(p, re.sub(r"^\s*\d+\. ", "", linea))
        elif linea.strip() == "---":
            pass
        else:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            runs_con_formato(p, linea.strip())
        i += 1

    docx = destino.with_suffix(".docx")
    doc.save(docx)
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
                    str(destino.parent), str(docx)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return destino


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    for origen, destino, pie in DOCUMENTOS:
        ruta_md = RAIZ / "AE4" / origen
        if not ruta_md.exists():
            print("falta:", ruta_md)
            continue
        pdf = convertir(ruta_md, SALIDA / destino, pie)
        paginas = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        total = re.search(r"Pages:\s+(\d+)", paginas).group(1)
        print(f"{pdf.name}: {total} páginas")


if __name__ == "__main__":
    main()
