"""Cálculo de las métricas del proyecto integrador (AE4).

Este módulo es la ÚNICA fuente de verdad de los números: la aplicación de
Streamlit, el documento y el script de verificación llaman a las mismas
funciones. Si un número cambia, cambia aquí y se propaga a todo.

Convenciones del proyecto:
- Una fila del dataset es UNA HORA de operación del sistema de bicicletas.
- ``cnt`` es la cantidad de rentas de esa hora (``cnt = casual + registered``).
- Los agregados se calculan sobre las filas que sobreviven a los filtros; nunca
  se reutilizan las columnas precalculadas (``pct_hora_del_dia``, etc.) porque
  esas fueron calculadas sobre el dataset completo, no sobre el subconjunto.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Ruta relativa desde la raíz del repositorio: la app corre con cwd = raíz.
RUTA_DATOS = Path("AE3") / "datos" / "dataset_preparado.csv"

# Orden canónico de la jornada: la madrugada primero, para leer el día como
# empieza de verdad y no alfabéticamente.
ORDEN_FRANJAS = ["Madrugada", "Mañana", "Pico mañana", "Mediodía", "Pico tarde", "Noche"]
ORDEN_TEMPORADAS = ["Primavera", "Verano", "Otoño", "Invierno"]


def cargar_datos(ruta: str | Path | None = None) -> pd.DataFrame:
    """Lee el dataset preparado en la AE3 y lo deja listo para agregar."""
    ruta = Path(ruta) if ruta is not None else RUTA_DATOS
    df = pd.read_csv(ruta, encoding="utf-8-sig")
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"])
    return df


# ---------------------------------------------------------------------------
# Indicadores generales
# ---------------------------------------------------------------------------
def kpis(df: pd.DataFrame) -> dict:
    """Indicadores de cabecera: volumen, intensidad y cobertura del periodo."""
    return {
        "rentas": int(df["cnt"].sum()),
        "horas": int(len(df)),
        "promedio": float(df["cnt"].mean()),
        "mediana": float(df["cnt"].median()),
        "dias": int(df["dteday"].nunique()),
        "casual": int(df["casual"].sum()),
        "registrado": int(df["registered"].sum()),
        "fecha_min": df["fecha_hora"].min(),
        "fecha_max": df["fecha_hora"].max(),
        "horas_esperadas": int(df["dteday"].nunique() * 24),
        "horas_faltantes": int(df["dteday"].nunique() * 24 - len(df)),
    }


def cobertura_pct(df: pd.DataFrame) -> float:
    """Porcentaje de horas del periodo que sí tienen registro."""
    k = kpis(df)
    return 100.0 * k["horas"] / k["horas_esperadas"] if k["horas_esperadas"] else 0.0


# ---------------------------------------------------------------------------
# Pregunta 2 — franjas horarias
# ---------------------------------------------------------------------------
def por_franja(df: pd.DataFrame) -> pd.DataFrame:
    """Rentas por franja horaria, con participación y veces el promedio general."""
    total = df["cnt"].sum()
    g = (
        df.groupby("franja_horaria")
        .agg(horas=("cnt", "size"), rentas=("cnt", "sum"), promedio=("cnt", "mean"), mediana=("cnt", "median"))
        .reindex(ORDEN_FRANJAS)
        .dropna(how="all")
    )
    g["participacion_pct"] = 100.0 * g["rentas"] / total
    g["veces_promedio"] = g["promedio"] / df["cnt"].mean()
    return g.reset_index()


# ---------------------------------------------------------------------------
# Pregunta 1 — reparto a lo largo del día
# ---------------------------------------------------------------------------
def por_hora(df: pd.DataFrame) -> pd.DataFrame:
    """Comportamiento hora a hora: promedio, mediana y participación del día."""
    total = df["cnt"].sum()
    g = (
        df.groupby("hr")
        .agg(rentas=("cnt", "sum"), promedio=("cnt", "mean"), mediana=("cnt", "median"), horas=("cnt", "size"))
        .reindex(range(24))
        .fillna(0)
    )
    g["participacion_pct"] = 100.0 * g["rentas"] / total if total else 0.0
    return g.reset_index()


def perfil_horario_por(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Promedio de rentas por hora, separado por las categorías de ``columna``.

    Devuelve una tabla ancha (una columna por categoría) lista para graficar
    varias líneas sobre el mismo eje de horas.
    """
    tabla = df.pivot_table(index="hr", columns=columna, values="cnt", aggfunc="mean").reindex(range(24))
    return tabla


# ---------------------------------------------------------------------------
# Pregunta 3 — tipo de día
# ---------------------------------------------------------------------------
def por_tipo_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Comparación laborable vs. no laborable, incluido el peso del usuario ocasional."""
    g = df.groupby("tipo_dia").agg(
        horas=("cnt", "size"),
        rentas=("cnt", "sum"),
        promedio=("cnt", "mean"),
        mediana=("cnt", "median"),
        casual=("casual", "sum"),
        registrado=("registered", "sum"),
    )
    g["participacion_pct"] = 100.0 * g["rentas"] / df["cnt"].sum()
    g["pct_casual"] = 100.0 * g["casual"] / g["rentas"]
    orden = [x for x in ["Laborable", "No laborable"] if x in g.index]
    return g.reindex(orden).reset_index()


# ---------------------------------------------------------------------------
# Pregunta 4 — temporada y año
# ---------------------------------------------------------------------------
def por_temporada(df: pd.DataFrame) -> pd.DataFrame:
    """Rentas y promedio por temporada."""
    g = (
        df.groupby("temporada")
        .agg(horas=("cnt", "size"), rentas=("cnt", "sum"), promedio=("cnt", "mean"), mediana=("cnt", "median"))
        .reindex([t for t in ORDEN_TEMPORADAS if t in df["temporada"].unique()])
    )
    g["participacion_pct"] = 100.0 * g["rentas"] / df["cnt"].sum()
    return g.reset_index()


def por_anio(df: pd.DataFrame) -> pd.DataFrame:
    """Volumen y promedio por año del periodo."""
    g = df.groupby("anio").agg(horas=("cnt", "size"), rentas=("cnt", "sum"), promedio=("cnt", "mean"))
    g["participacion_pct"] = 100.0 * g["rentas"] / df["cnt"].sum()
    return g.reset_index()


def temporada_por_anio(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio por temporada y año: distingue estacionalidad de crecimiento."""
    tabla = df.pivot_table(index="temporada", columns="anio", values="cnt", aggfunc="mean")
    tabla = tabla.reindex([t for t in ORDEN_TEMPORADAS if t in tabla.index])
    if {2011, 2012}.issubset(tabla.columns):
        tabla["variacion_pct"] = 100.0 * (tabla[2012] / tabla[2011] - 1)
    return tabla.reset_index()


# ---------------------------------------------------------------------------
# Pregunta 5 — clima y temperatura
# ---------------------------------------------------------------------------
def por_clima(df: pd.DataFrame) -> pd.DataFrame:
    """Rentas por condición climática."""
    g = df.groupby("clima").agg(
        horas=("cnt", "size"), rentas=("cnt", "sum"), promedio=("cnt", "mean"), mediana=("cnt", "median")
    )
    g = g.sort_values("promedio", ascending=False)
    g["participacion_pct"] = 100.0 * g["rentas"] / df["cnt"].sum()
    return g.reset_index()


def por_rango_temperatura(df: pd.DataFrame) -> pd.DataFrame:
    """Rentas por rango de temperatura construido en la etapa 2."""
    orden = ["Fría (≤5 °C)", "Templada (5-15 °C)", "Cálida (15-25 °C)", "Calurosa (>25 °C)"]
    g = df.groupby("rango_temperatura").agg(
        horas=("cnt", "size"), rentas=("cnt", "sum"), promedio=("cnt", "mean"), mediana=("cnt", "median")
    )
    existentes = [o for o in orden if o in g.index]
    resto = [o for o in g.index if o not in existentes]
    g = g.reindex(existentes + resto).dropna(how="all")
    g["participacion_pct"] = 100.0 * g["rentas"] / df["cnt"].sum()
    return g.reset_index()


# ---------------------------------------------------------------------------
# Pregunta 6 — casuales vs. registrados
# ---------------------------------------------------------------------------
def por_tipo_usuario(df: pd.DataFrame) -> pd.DataFrame:
    """Peso de cada tipo de usuario sobre el total de rentas."""
    total = df["cnt"].sum()
    filas = [
        ("Casual", int(df["casual"].sum()), float(df["casual"].mean())),
        ("Registrado", int(df["registered"].sum()), float(df["registered"].mean())),
    ]
    g = pd.DataFrame(filas, columns=["tipo_usuario", "rentas", "promedio_por_hora"])
    g["participacion_pct"] = 100.0 * g["rentas"] / total
    return g


def usuarios_por_tipo_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Participación de cada tipo de usuario según el tipo de día."""
    g = df.groupby("tipo_dia").agg(casual=("casual", "sum"), registrado=("registered", "sum"))
    g["total"] = g["casual"] + g["registrado"]
    g["pct_casual"] = 100.0 * g["casual"] / g["total"]
    g["pct_registrado"] = 100.0 * g["registrado"] / g["total"]
    orden = [x for x in ["Laborable", "No laborable"] if x in g.index]
    return g.reindex(orden).reset_index()


# ---------------------------------------------------------------------------
# Concentración y días extremos (soporte para la interpretación)
# ---------------------------------------------------------------------------
def concentracion_horaria(df: pd.DataFrame) -> dict:
    """¿Cuánto pesa la hora más cargada de cada día dentro de ese día?"""
    diario = df.groupby("dteday").agg(rentas_dia=("cnt", "sum"), max_hora=("cnt", "max"))
    diario["pct"] = 100.0 * diario["max_hora"] / diario["rentas_dia"]
    return {
        "mediana_pct": float(diario["pct"].median()),
        "p75_pct": float(diario["pct"].quantile(0.75)),
        "max_pct": float(diario["pct"].max()),
    }


def dias_destacados(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Días de mayor demanda del periodo filtrado."""
    g = df.groupby("dteday").agg(rentas=("cnt", "sum"), horas=("cnt", "size"))
    g = g.sort_values("rentas", ascending=False).head(n)
    return g.reset_index()


def tabla_preguntas() -> list[dict]:
    """Las seis preguntas de negocio con su métrica, unidad y gráfico.

    Es el índice que usan la app y el documento para no divergir.
    """
    return [
        {
            "id": "p1",
            "pregunta": "¿Cuánta demanda hay y cómo se reparte en el día?",
            "metrica": "Rentas totales, promedio y mediana por hora",
            "unidad": "rentas (conteo) / rentas por hora",
            "grafico": "Línea de promedio por hora + barras de participación por franja",
        },
        {
            "id": "p2",
            "pregunta": "¿En qué franjas horarias se concentra la demanda?",
            "metrica": "Participación de cada franja sobre el total y veces el promedio",
            "unidad": "% del total / múltiplo del promedio",
            "grafico": "Barras horizontales ordenadas por participación",
        },
        {
            "id": "p3",
            "pregunta": "¿Cambia la demanda según el tipo de día?",
            "metrica": "Promedio por hora y participación del usuario ocasional, laborable vs. no laborable",
            "unidad": "rentas por hora / %",
            "grafico": "Barras comparativas + perfil horario de ambos tipos de día",
        },
        {
            "id": "p4",
            "pregunta": "¿Cambia con la temporada y entre 2011 y 2012?",
            "metrica": "Promedio por temporada y variación porcentual 2011→2012",
            "unidad": "rentas por hora / % de variación",
            "grafico": "Barras por temporada + barras agrupadas por año",
        },
        {
            "id": "p5",
            "pregunta": "¿Cambia con el clima y la temperatura?",
            "metrica": "Promedio por condición climática y por rango de temperatura",
            "unidad": "rentas por hora",
            "grafico": "Barras por clima + línea por rango de temperatura",
        },
        {
            "id": "p6",
            "pregunta": "¿Qué peso tienen los usuarios casuales y los registrados?",
            "metrica": "Participación de cada tipo de usuario y su comportamiento por tipo de día",
            "unidad": "% del total de rentas",
            "grafico": "Dona de participación + perfil horario por tipo de usuario",
        },
    ]
