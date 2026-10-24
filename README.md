# Proyecto Integrado III — Analítica de Datos

Repositorio del proyecto del curso **Proyecto Integrado III - Analítica de Datos**
(IU Digital de Antioquia, 2026-Q4).

Contiene las dos clases reutilizables del proyecto y el notebook de la
**Actividad 1**: cargar un dataset de Hugging Face, transformarlo y generar
automáticamente un resumen en `.txt`.

---

## Dataset

| Campo | Valor |
|---|---|
| **Identificador** | `t22000t/bike-sharing-tabular` |
| **Enlace** | https://huggingface.co/datasets/t22000t/bike-sharing-tabular |
| **Split utilizado** | `train` |
| **Filas × columnas** | 17.379 × 17 |
| **Licencia** | CC-BY-4.0 |
| **Origen** | UCI Machine Learning Repository, *Bike Sharing Dataset* (id 275) |
| **Datos reales** | Sí — registro horario del sistema **Capital Bikeshare**, Washington D.C. |
| **Periodo** | 1 de enero de 2011 – 31 de diciembre de 2012 |
| **Fecha de consulta** | 24 de octubre de 2026 |

### Qué representa cada fila

Una fila es **una hora de operación** del sistema de bicicletas públicas:
cuántas bicicletas se rentaron en esa hora, con qué condiciones climáticas y
en qué momento del calendario.

### Cita de los datos

> Fanaee-T, Hadi y Gama, Joao. (2013). *Event labeling combining ensemble
> detectors and background knowledge*. Progress in Artificial Intelligence,
> pp. 1–15. Springer Berlin Heidelberg.
> doi:10.1007/s13748-013-0040-3

---

## Estructura del repositorio

```
.
├── src/
│   └── clases_po/
│       ├── __init__.py        # expone las dos clases del paquete
│       ├── hf_loader.py       # HFDatasetLoader  → obtiene el DataFrame
│       └── summarizer.py      # DatasetSummarizer → genera el .txt
├── EA1/
│   ├── notebooks/
│   │   └── EA1_carga_y_transformacion.ipynb
│   └── resultados/
│       └── resumen_dataset.txt
├── AE2/
│   ├── documento/
│   │   ├── EA2_proyecto_integrador_etapa1.docx
│   │   └── EA2_proyecto_integrador_etapa1.pdf
│   ├── notebooks/
│   │   └── EA2_reconocimiento_dataset.ipynb
│   └── resultados/
│       └── resumen_dataframe.txt
├── requirements.txt
└── README.md
```

---

## Las dos clases

### `HFDatasetLoader` (`src/clases_po/hf_loader.py`)

Obtiene un dataset de Hugging Face y lo devuelve como `pandas.DataFrame`.

- Recibe el identificador del dataset y, opcionalmente, el `split`, la
  configuración, el token y un límite de filas.
- La conexión y la descarga ocurren **dentro** de la clase.
- Opcionalmente guarda una copia en `csv`, `json`, `parquet` o `xlsx`.

```python
from clases_po import HFDatasetLoader

df = HFDatasetLoader("t22000t/bike-sharing-tabular", split="train").load()
```

### `DatasetSummarizer` (`src/clases_po/summarizer.py`)

Recibe un DataFrame y genera un resumen en texto: filas, columnas, tipos,
valores nulos, estadísticas descriptivas y valores más frecuentes.
Puede imprimirlo o guardarlo en un `.txt` en UTF-8.

```python
from clases_po import DatasetSummarizer

summarizer = DatasetSummarizer(dataset_id="t22000t/bike-sharing-tabular", split="train")
summarizer.guardar(df, "EA1/resultados/resumen_dataset.txt")
```

---

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Si `python -m venv` falla con *"ensurepip is not available"* (Debian/Ubuntu
> sin el paquete `python3-venv`), instala ese paquete con
> `sudo apt install python3-venv` o, alternativamente, instala las
> dependencias con `pip install --user --break-system-packages -r requirements.txt`.

## Cómo ejecutar

1. Activar el entorno (`.venv`) o tener las dependencias instaladas.
2. Abrir Jupyter y ejecutar el notebook **en orden**:

```bash
jupyter lab EA1/notebooks/EA1_carga_y_transformacion.ipynb
```

3. El notebook crea o actualiza `EA1/resultados/resumen_dataset.txt`.

También se puede ejecutar sin abrir Jupyter:

```bash
cd EA1/notebooks
jupyter nbconvert --to notebook --execute --inplace EA1_carga_y_transformacion.ipynb
```

---

## Flujo del notebook

```
HFDatasetLoader  →  DataFrame  →  5 transformaciones  →  DatasetSummarizer  →  .txt
```

Las cinco transformaciones aplicadas son:

1. **Renombrar** las columnas al español.
2. **Seleccionar** un subconjunto de columnas relevantes.
3. **Filtrar** filas: solo días laborables.
4. **Crear columnas calculadas**: fecha como `datetime`, año, temperatura en °C,
   humedad en %, franja horaria.
5. **Agrupar y agregar**: demanda promedio por temporada.

El archivo `resumen_dataset.txt` corresponde al **DataFrame transformado**
(11.865 filas × 16 columnas), no al original.

---

## Notas y limitaciones

- Los datos son reales, no sintéticos.
- Las variables categóricas vienen **codificadas numéricamente** (temporada 1–4,
  clima 1–4, año 0/1). Su significado está documentado en el README oficial de
  UCI, no se deduce de los datos.
- Temperatura, humedad y viento vienen **normalizados**: la temperatura está
  dividida entre 41, la humedad entre 100 y el viento entre 67.
- El dataset solo cubre Washington D.C. y dos años; no permite generalizar a
  otras ciudades ni hacer afirmaciones sobre años posteriores.
- No contiene información de usuarios individuales, por lo que no permite
  analizar perfiles personales.
