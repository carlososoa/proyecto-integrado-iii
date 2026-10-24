"""
Resumen de un DataFrame exportado a archivo .txt.

=========================================================================
¿QUÉ HACE ESTA CLASE?
=========================================================================

Recibe un DataFrame de pandas ya cargado (no sabe de dónde viene) y produce
un resumen en texto plano que permite RECONOCER los datos sin abrirlos:

    - filas y columnas
    - nombres y tipos de cada columna
    - valores nulos por columna
    - estadísticas descriptivas de las variables numéricas
    - valores más frecuentes de las variables categóricas

El resultado se puede imprimir en pantalla o guardar en un .txt, y ese .txt
es la evidencia de la actividad 1.

Relación con HFDatasetLoader: son clases SEPARADAS a propósito. Una consigue
los datos; esta otra los describe. Cada una se puede usar y probar por su
cuenta (principio de responsabilidad única).
=========================================================================
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


class DatasetSummarizer:
    """Resume un DataFrame y lo exporta a un archivo .txt."""

    def __init__(
        self,
        dataset_id: str | None = None,
        split: str | None = None,
        nota: str | None = None,
    ) -> None:
        """Guarda los metadatos que se quieren dejar escritos en el .txt.

        Args:
            dataset_id: identificador del dataset en Hugging Face.
            split: división utilizada (train, test...).
            nota: aclaración libre, por ejemplo qué transformación se aplicó.
        """
        self.dataset_id = dataset_id
        self.split = split
        self.nota = nota

    # ------------------------------------------------------------------
    # RESUMEN EN TEXTO
    # ------------------------------------------------------------------
    def resumen(self, df: pd.DataFrame) -> str:
        """Devuelve el resumen del DataFrame como texto."""
        self._validar(df)

        numericas = df.select_dtypes(include="number")
        categoricas = df.select_dtypes(exclude="number")

        lineas: list[str] = [
            "RESUMEN DEL DATAFRAME",
            "=" * 62,
        ]

        # Metadatos: solo se escriben si fueron proporcionados.
        if self.dataset_id:
            lineas.append(f"Dataset: {self.dataset_id}")
        if self.split:
            lineas.append(f"Split: {self.split}")
        lineas.append(f"Generado: {datetime.now():%Y-%m-%d %H:%M}")
        if self.nota:
            lineas.append(f"Nota: {self.nota}")

        # Dimensiones y tamaño en memoria.
        memoria_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
        lineas += [
            "",
            "DIMENSIONES",
            "-" * 62,
            f"Filas: {len(df)}",
            f"Columnas: {len(df.columns)}",
            f"Memoria aproximada: {memoria_mb:.2f} MB",
            f"Filas duplicadas: {int(df.duplicated().sum())}",
            f"Valores nulos totales: {int(df.isna().sum().sum())}",
        ]

        # Nombres y tipos de columna.
        lineas += ["", "COLUMNAS Y TIPOS", "-" * 62]
        lineas += [f"- {col}: {tipo}" for col, tipo in df.dtypes.items()]

        # Nulos por columna, con porcentaje para dimensionar el problema.
        lineas += ["", "VALORES NULOS POR COLUMNA", "-" * 62]
        for col, nulos in df.isna().sum().items():
            pct = (nulos / len(df) * 100) if len(df) else 0
            lineas.append(f"- {col}: {int(nulos)} ({pct:.2f} %)")

        # Estadísticas de las variables numéricas.
        if not numericas.empty:
            lineas += [
                "",
                "ESTADISTICAS DESCRIPTIVAS (variables numericas)",
                "-" * 62,
                numericas.describe().round(3).to_string(),
            ]

        # Valores más frecuentes de las categóricas (solo si son pocas).
        if not categoricas.empty:
            lineas += ["", "VALORES MAS FRECUENTES (variables no numericas)", "-" * 62]
            for col in categoricas.columns:
                if categoricas[col].nunique(dropna=True) > 20:
                    lineas.append(f"- {col}: {categoricas[col].nunique()} valores distintos (no se listan)")
                    continue
                conteo = categoricas[col].value_counts(dropna=False).head(5)
                detalle = ", ".join(f"{valor} ({n})" for valor, n in conteo.items())
                lineas.append(f"- {col}: {detalle}")

        return "\n".join(lineas) + "\n"

    # ------------------------------------------------------------------
    # SALIDAS
    # ------------------------------------------------------------------
    def imprimir(self, df: pd.DataFrame) -> None:
        """Muestra el resumen en la consola."""
        print(self.resumen(df), end="")

    def guardar(self, df: pd.DataFrame, ruta: str | Path) -> Path:
        """Escribe el resumen en un .txt (UTF-8) y devuelve la ruta final."""
        path = Path(ruta)
        # Crea la carpeta si no existe, para que funcione en un repo recién clonado.
        path.parent.mkdir(parents=True, exist_ok=True)
        # encoding="utf-8" conserva tildes y ñ.
        path.write_text(self.resumen(df), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # VALIDACIÓN
    # ------------------------------------------------------------------
    @staticmethod
    def _validar(df: pd.DataFrame) -> None:
        """Comprueba que lo recibido sea realmente un DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df debe ser un pandas.DataFrame.")
