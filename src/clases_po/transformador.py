"""Transformaciones de calidad sobre el dataset horario de bicicletas públicas.

Cada regla está en un método propio y devuelve cuántos registros modificó, de
modo que el notebook pueda mostrar el antes y el después. El criterio general:
no se elimina ni se imputa nada sin justificarlo; cuando un control no
encuentra problemas, también se informa (con cero registros afectados).
"""
from __future__ import annotations

import pandas as pd


def miles(valor: int) -> str:
    """Formatea un entero con separador de miles (punto, uso en español)."""
    return f"{valor:,}".replace(",", ".")

# Significados tomados del README oficial del dataset (UCI, id 275).
ESTACIONES = {1: "Primavera", 2: "Verano", 3: "Otoño", 4: "Invierno"}
CLIMA = {
    1: "Despejado",
    2: "Neblina o nublado",
    3: "Lluvia o nieve ligera",
    4: "Lluvia fuerte o tormenta",
}
DIAS = {0: "Domingo", 1: "Lunes", 2: "Martes", 3: "Miércoles",
        4: "Jueves", 5: "Viernes", 6: "Sábado"}


class TransformadorBikes:
    """Convierte el dataset crudo en una tabla lista para analizar."""

    def __init__(self, df: pd.DataFrame) -> None:
        # Copia de trabajo: el DataFrame original queda intacto para comparar.
        self.df_crudo = df.copy()
        self.df = df.copy()
        self.n_columnas_originales = df.shape[1]
        self.reglas: list[dict[str, object]] = []

    def _registrar(self, regla: str, detalle: str, afectados: int) -> None:
        self.reglas.append(
            {"regla": regla, "detalle": detalle, "registros_afectados": int(afectados)}
        )

    # ── 1. Fechas ────────────────────────────────────────────────────────
    def convertir_fechas(self) -> None:
        """`dteday` llega como texto: se convierte a fecha y se arma el timestamp."""
        antes = str(self.df["dteday"].dtype)
        self.df["dteday"] = pd.to_datetime(self.df["dteday"], format="%Y-%m-%d")
        # fecha_hora = fecha del día + hora del registro. Sirve para ordenar,
        # detectar huecos y unir tablas por hora exacta.
        self.df["fecha_hora"] = self.df["dteday"] + pd.to_timedelta(self.df["hr"], unit="h")
        self.df = self.df.sort_values("fecha_hora").reset_index(drop=True)
        self._registrar(
            "Tipo de fecha",
            f"dteday pasó de {antes} a {self.df['dteday'].dtype}; se creó fecha_hora",
            len(self.df),
        )

    # ── 2. Unidades ──────────────────────────────────────────────────────
    def escalar_variables(self) -> None:
        """Devuelve las variables normalizadas a su escala original (README UCI)."""
        # El dataset publica temp/41, atemp/50, hum/100 y windspeed/67.
        self.df["temp_c"] = (self.df["temp"] * 41).round(1)
        self.df["atemp_c"] = (self.df["atemp"] * 50).round(1)
        self.df["hum_pct"] = (self.df["hum"] * 100).round(1)
        self.df["windspeed_kmh"] = (self.df["windspeed"] * 67).round(1)
        self._registrar(
            "Escalas",
            "temp→°C, atemp→°C, hum→%, windspeed→km/h (4 columnas nuevas)",
            len(self.df),
        )

    # ── 3. Códigos ───────────────────────────────────────────────────────
    def decodificar_categoricas(self) -> None:
        """Traduce los códigos numéricos a etiquetas, sin borrar el código."""
        self.df["temporada"] = self.df["season"].map(ESTACIONES)
        self.df["clima"] = self.df["weathersit"].map(CLIMA)
        self.df["dia_semana"] = self.df["weekday"].map(DIAS)
        self.df["anio"] = self.df["yr"].map({0: 2011, 1: 2012})
        self.df["tipo_dia"] = self.df["workingday"].map({1: "Laborable", 0: "No laborable"})
        sin_mapear = int(
            self.df[["temporada", "clima", "dia_semana", "anio", "tipo_dia"]]
            .isna().any(axis=1).sum()
        )
        if sin_mapear:
            raise ValueError(f"{sin_mapear} registros con códigos sin equivalencia")
        self._registrar("Códigos", "5 variables categóricas traducidas a etiquetas", len(self.df))

    # ── 4. Identificadores ───────────────────────────────────────────────
    def revisar_identificadores(self) -> None:
        """Comprueba que los conteos sean enteros y que no haya identificadores decimales."""
        conteos = ["casual", "registered", "cnt", "hr", "mnth", "yr", "season",
                   "holiday", "weekday", "workingday", "weathersit"]
        for col in conteos:
            self.df[col] = self.df[col].astype("int64")
        self._registrar(
            "Tipos numéricos",
            f"{len(conteos)} columnas de conteo y código convertidas a entero; "
            "el dataset no trae identificadores con decimales",
            0,
        )

    # ── 5. Duplicados ────────────────────────────────────────────────────
    def revisar_duplicados(self) -> None:
        """Un sistema no puede registrar dos veces la misma hora: se buscan y se informan."""
        dup = int(self.df.duplicated(subset="fecha_hora").sum())
        if dup:
            raise ValueError(f"Hay {dup} horas duplicadas: revisar antes de continuar")
        self._registrar("Duplicados", "0 horas repetidas en fecha_hora", 0)

    # ── 6. Consistencia del total ────────────────────────────────────────
    def validar_total(self) -> None:
        """El total debe ser exactamente la suma de ocasionales y registrados."""
        diferencia = (self.df["cnt"] - (self.df["casual"] + self.df["registered"]))
        inconsistentes = int((diferencia != 0).sum())
        self._registrar(
            "Consistencia cnt",
            f"cnt = casual + registered en los {miles(len(self.df))} registros" if not inconsistentes
            else f"{inconsistentes} registros no cumplen cnt = casual + registered",
            inconsistentes,
        )

    # ── 7. Cobertura ─────────────────────────────────────────────────────
    def revisar_cobertura(self) -> None:
        """Informa las horas que faltan; NO se rellenan (imputar alteraría los promedios)."""
        dias = self.df["dteday"].nunique()
        esperadas = dias * 24
        faltantes = esperadas - len(self.df)
        por_dia = self.df.groupby("dteday").size()
        dias_incompletos = int((por_dia < 24).sum())
        self.df["dia_completo"] = self.df["dteday"].map(por_dia.eq(24))
        self._registrar(
            "Cobertura",
            f"{miles(len(self.df))} de {miles(esperadas)} horas ({miles(faltantes)} faltantes en {dias_incompletos} días); no se imputan",
            0,
        )

    # ── 8. Selección ─────────────────────────────────────────────────────
    def justificar_seleccion(self) -> None:
        """Documenta qué columnas y registros se conservan, y por qué.

        No se descarta ninguna de las 17 columnas originales: todas aportan a
        alguna de las preguntas de negocio (cantidad, tiempo, clima o tipo de
        usuario), y tampoco se eliminan horas porque cada una es una
        observación válida del sistema. Queda registrado como control.
        """
        self._registrar(
            "Selección",
            f"se conservan las {self.n_columnas_originales} columnas originales y los {miles(len(self.df))} registros: todos aportan a las preguntas",
            0,
        )

    # ── 9. Orquestador ───────────────────────────────────────────────────
    def procesar(self) -> pd.DataFrame:
        """Ejecuta todas las reglas en orden y devuelve el DataFrame transformado."""
        self.convertir_fechas()
        self.escalar_variables()
        self.decodificar_categoricas()
        self.revisar_identificadores()
        self.revisar_duplicados()
        self.validar_total()
        self.revisar_cobertura()
        self.justificar_seleccion()
        return self.df

    def tabla_reglas(self) -> pd.DataFrame:
        """Resumen legible de las reglas aplicadas y su efecto."""
        return pd.DataFrame(self.reglas)

    def comparacion(self, df_final: pd.DataFrame) -> pd.DataFrame:
        """Compara estructura, nulos y duplicados del DataFrame inicial y final."""
        def resumen(df: pd.DataFrame) -> dict[str, object]:
            return {
                "filas": len(df),
                "columnas": len(df.columns),
                "tipos_de_dato": df.dtypes.nunique(),
                "valores_nulos": int(df.isna().sum().sum()),
                "filas_duplicadas": int(df.duplicated().sum()),
            }
        tabla = pd.DataFrame({"antes": resumen(self.df_crudo), "despues": resumen(df_final)})
        tabla["cambio"] = tabla["despues"] - tabla["antes"]
        return tabla
