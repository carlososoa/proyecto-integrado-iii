"""Variables derivadas y cruce con la tabla diaria.

Enriquecer no es inventar datos: es aprovechar la información que ya está en el
dataset (hora, fecha, tipo de usuario) para construir columnas que respondan
mejor las preguntas de negocio. Cada columna nueva queda con su fórmula.
"""
from __future__ import annotations

import pandas as pd

# Franjas definidas para describir la operación del sistema. Los cortes separan
# los dos picos de movilidad (entrada y salida laboral) del resto del día.
FRANJAS = [
    (0, 5, "Madrugada"),      # 00:00 a 05:59
    (6, 8, "Pico mañana"),    # 06:00 a 08:59
    (9, 11, "Mañana"),        # 09:00 a 11:59
    (12, 15, "Mediodía"),     # 12:00 a 15:59
    (16, 19, "Pico tarde"),   # 16:00 a 19:59
    (20, 23, "Noche"),        # 20:00 a 23:59
]


def franja_de(hora: int) -> str:
    """Devuelve la franja horaria de una hora del día (0-23)."""
    for inicio, fin, nombre in FRANJAS:
        if inicio <= hora <= fin:
            return nombre
    raise ValueError(f"Hora fuera de rango: {hora}")


class EnriquecedorBikes:
    """Agrega variables calculadas y une la tabla diaria al detalle horario."""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df.copy()
        self.columnas_nuevas: list[dict[str, str]] = []
        self.validacion_union: dict[str, object] = {}

    def _anotar(self, columna: str, formula: str, utilidad: str) -> None:
        self.columnas_nuevas.append(
            {"variable": columna, "formula": formula, "utilidad": utilidad}
        )

    # ── 1. Calendario ────────────────────────────────────────────────────
    def agregar_calendario(self) -> None:
        """Dimensiones de fecha y hora: mes, fin de semana y franja horaria."""
        # Nombres de mes en español sin depender del locale del sistema.
        meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
                 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
        self.df["mes"] = self.df["dteday"].dt.month.map(meses)
        self.df["es_fin_de_semana"] = self.df["weekday"].isin([0, 6])
        self.df["franja_horaria"] = self.df["hr"].apply(franja_de)
        self.df["es_hora_pico"] = self.df["franja_horaria"].isin(["Pico mañana", "Pico tarde"])
        self._anotar("mes", "nombre del mes a partir de dteday", "comparar estacionalidad")
        self._anotar("es_fin_de_semana", "weekday en {0, 6} (0=domingo, 6=sábado)",
                     "separar uso de fin de semana del laboral")
        self._anotar("franja_horaria", "rangos de hr: 0-5, 6-8, 9-11, 12-15, 16-19, 20-23",
                     "comparar la demanda a lo largo del día")
        self._anotar("es_hora_pico", "franja_horaria en {Pico mañana, Pico tarde}",
                     "identificar las horas de mayor presión operativa")

    # ── 2. Composición del usuario ───────────────────────────────────────
    def agregar_participacion(self) -> None:
        """Peso porcentual de cada tipo de usuario dentro de la hora."""
        self.df["pct_casual"] = (self.df["casual"] / self.df["cnt"] * 100).round(2)
        self.df["pct_registered"] = (self.df["registered"] / self.df["cnt"] * 100).round(2)
        self._anotar("pct_casual", "casual / cnt × 100", "describir el perfil ocasional")
        self._anotar("pct_registered", "registered / cnt × 100", "describir el perfil suscrito")

    # ── 3. Clima ─────────────────────────────────────────────────────────
    def agregar_rangos_clima(self) -> None:
        """Rango de temperatura y marca de clima adverso."""
        cortes = [-5, 5, 15, 25, 50]
        etiquetas = ["Fría (≤5 °C)", "Templada (5-15 °C)", "Cálida (15-25 °C)", "Calurosa (>25 °C)"]
        self.df["rango_temperatura"] = pd.cut(
            self.df["temp_c"], bins=cortes, labels=etiquetas, right=True
        )
        self.df["clima_adverso"] = self.df["weathersit"].isin([3, 4])
        self._anotar("rango_temperatura", "cortes de temp_c en 5, 15 y 25 °C",
                     "comparar la demanda por temperatura")
        self._anotar("clima_adverso", "weathersit en {3, 4} (lluvia, nieve o tormenta)",
                     "aislar el efecto del mal tiempo")

    # ── 4. Cruce con la tabla diaria ─────────────────────────────────────
    def unir_tabla_diaria(self) -> None:
        """Une el resumen del día a cada hora, validando que no multiplique filas.

        La tabla diaria se construye con los MISMOS datos: no es una fuente
        externa. Se usa la fecha como clave (un registro por día), por eso la
        unión no puede duplicar horas; se comprueba igual, como pide la consigna.
        """
        diaria = (
            self.df.groupby("dteday")
            .agg(
                total_dia=("cnt", "sum"),
                promedio_hora_dia=("cnt", "mean"),
                horas_registradas_dia=("cnt", "size"),
            )
            .round(2)
            .reset_index()
        )
        filas_antes = len(self.df)
        total_antes = int(self.df["cnt"].sum())

        self.df = self.df.merge(diaria, on="dteday", how="left", validate="many_to_one")

        # Participación de la hora dentro del día: cuánto aporta esa hora al total diario.
        self.df["pct_hora_del_dia"] = (self.df["cnt"] / self.df["total_dia"] * 100).round(2)

        self.validacion_union = {
            "filas_antes": filas_antes,
            "filas_despues": len(self.df),
            "total_rentas_antes": total_antes,
            "total_rentas_despues": int(self.df["cnt"].sum()),
            "dias_en_tabla_diaria": len(diaria),
            "sin_coincidencia": int(self.df["total_dia"].isna().sum()),
        }
        if len(self.df) != filas_antes or total_antes != int(self.df["cnt"].sum()):
            raise ValueError("La unión alteró el número de filas o el total de rentas")

        self._anotar("total_dia", "suma de cnt por dteday (clave de unión)",
                     "contexto del día para cada hora")
        self._anotar("promedio_hora_dia", "media de cnt de las horas registradas del día",
                     "comparar la hora con un día típico")
        self._anotar("horas_registradas_dia", "conteo de registros del día",
                     "identificar días incompletos")
        self._anotar("pct_hora_del_dia", "cnt / total_dia × 100",
                     "saber cuánto pesa la hora en la operación del día")

    # ── 5. Orquestador ───────────────────────────────────────────────────
    def procesar(self) -> pd.DataFrame:
        """Aplica todo el enriquecimiento en orden."""
        self.agregar_calendario()
        self.agregar_participacion()
        self.agregar_rangos_clima()
        self.unir_tabla_diaria()
        return self.df

    def diccionario(self) -> pd.DataFrame:
        """Diccionario de las variables incorporadas."""
        return pd.DataFrame(self.columnas_nuevas)
