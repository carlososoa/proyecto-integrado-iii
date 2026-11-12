# Proyecto Integrado III — Analítica de Datos

Repositorio del proyecto del curso **Proyecto Integrado III - Analítica de Datos**
(IU Digital de Antioquia, 2026-Q4).

Contiene las **clases reutilizables** del proyecto, los notebooks de las tres
primeras etapas —carga y transformación (EA1), reconocimiento del dataset (AE2)
y transformación con enriquecimiento (AE3)— y la **aplicación en Streamlit** de
la etapa final (AE4), que responde las seis preguntas de negocio del proyecto.

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
│       ├── __init__.py        # expone las clases del paquete
│       ├── hf_loader.py       # HFDatasetLoader   → obtiene el DataFrame
│       ├── summarizer.py      # DatasetSummarizer → genera el .txt de la EA1
│       ├── reportes.py        # Reportes          → .txt descriptivo (formato Triple A)
│       ├── transformador.py   # TransformadorBikes → reglas de calidad
│       └── enriquecedor.py    # EnriquecedorBikes  → variables derivadas y cruce diario
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
├── AE3/
│   ├── datos/
│   │   └── dataset_preparado.csv
│   ├── documento/
│   │   ├── EA3_proyecto_integrador_etapa2.docx
│   │   └── EA3_proyecto_integrador_etapa2.pdf
│   ├── notebooks/
│   │   └── EA3_transformacion_enriquecimiento.ipynb
│   └── resultados/
│       ├── resumen_dataframe.txt
│       └── tabla_*.csv
├── AE4/
│   ├── app.py                  # aplicación Streamlit de la etapa 4
│   ├── metricas.py             # cálculo de métricas (fuente única de los números)
│   ├── verificar_metricas.py   # contrasta las cifras contra las tablas de la AE3
│   ├── probar_app.py           # recorre las 7 vistas y valida que no fallen
│   ├── construir_documento_final.py  # genera el informe integral (Word y PDF)
│   ├── GUIA_EQUIPO.md          # guía de estudio y preguntas del docente
│   ├── GUION_PRESENTACION.md   # guion cronometrado de la sustentación
│   └── documento/
│       ├── PI3_proyecto_integrador_analitica_datos_grupo3.pdf
│       └── figuras/            # figuras y captura de la aplicación
├── requirements.txt
└── README.md
```

---

## Las clases

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

### `TransformadorBikes` (`src/clases_po/transformador.py`)

Aplica las reglas de calidad de la AE3, una por método, y registra **cuántos
registros afecta** cada una (incluidos los controles que no encuentran
problemas):

- convierte `dteday` a fecha y construye `fecha_hora`;
- devuelve `temp`, `atemp`, `hum` y `windspeed` a su escala original;
- traduce los códigos de temporada, clima, día y año a etiquetas;
- verifica tipos numéricos, duplicados por hora y que `cnt = casual + registered`;
- informa la cobertura (17.379 de 17.544 horas) **sin imputar** los faltantes.

```python
from clases_po import TransformadorBikes

transformador = TransformadorBikes(df_crudo)
df_transformado = transformador.procesar()
transformador.tabla_reglas()
```

### `EnriquecedorBikes` (`src/clases_po/enriquecedor.py`)

Construye variables nuevas a partir de las existentes y cruza la tabla diaria:

- `mes`, `es_fin_de_semana`, `franja_horaria`, `es_hora_pico`;
- `pct_casual`, `pct_registered`;
- `rango_temperatura`, `clima_adverso`;
- `total_dia`, `promedio_hora_dia`, `horas_registradas_dia`, `pct_hora_del_dia`.

La unión con la tabla diaria usa `dteday` como clave y se valida con
`validate="many_to_one"`: el notebook comprueba que filas y total de rentas no
cambien (17.379 antes y después).

```python
from clases_po import EnriquecedorBikes

enriquecedor = EnriquecedorBikes(df_transformado)
df = enriquecedor.procesar()
enriquecedor.validacion_union
```

### `Reportes` (`src/clases_po/reportes.py`)

Genera el `.txt` descriptivo del DataFrame final con el formato trabajado en
Triple A: filas, columnas, duplicados, columnas y tipos, nulos por columna y
estadísticas numéricas.

```python
from clases_po import Reportes

Reportes().guardar_reporte(df, "AE3/resultados/resumen_dataframe.txt")
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

Cada notebook se ejecuta **desde su propia carpeta**, porque las rutas de
salida son relativas (`../resultados`, `../datos`).

```bash
# EA1
cd EA1/notebooks
jupyter nbconvert --to notebook --execute --inplace EA1_carga_y_transformacion.ipynb

# AE2
cd ../../AE2/notebooks
jupyter nbconvert --to notebook --execute --inplace EA2_reconocimiento_dataset.ipynb

# AE3
cd ../../AE3/notebooks
jupyter nbconvert --to notebook --execute --inplace EA3_transformacion_enriquecimiento.ipynb
```

### Aplicación en Streamlit (AE4)

```bash
# desde la raíz del repositorio
streamlit run AE4/app.py
```

La aplicación abre en `http://localhost:8501`. Recorre nueve secciones —proyecto
y datos, resumen del periodo, las seis preguntas de negocio y conclusiones y
recomendaciones—; los filtros de la barra lateral (periodo, temporada, tipo de
día y clima) recalculan todos los indicadores y gráficos, y permiten hacer la
sustentación completa sin diapositivas.

- **Cálculo:** `AE4/metricas.py` concentra las métricas. La app, el documento y
  el script de verificación usan las mismas funciones, de modo que una cifra no
  puede decir cosas distintas en dos lugares.
- **Verificación de cifras:** `python AE4/verificar_metricas.py` compara los
  cálculos contra las tablas `.csv` de la AE3 y falla si alguna cifra no cuadra.
- **Prueba de la interfaz:** `python AE4/probar_app.py` ejecuta las siete vistas
  con el `AppTest` de Streamlit y reporta cualquier excepción.

**Aplicación publicada:** <https://proyecto-integrado-iii-team3-preica2602b020038.streamlit.app/>

### Informe final

El informe integral del proyecto está en
`AE4/documento/PI3_proyecto_integrador_analitica_datos_grupo3.pdf` (28 páginas,
21 tablas y 7 figuras). Reúne las cuatro etapas en un solo documento y se
regenera con `python AE4/construir_documento_final.py`, que calcula las cifras
con el mismo módulo de la aplicación.

El guion cronometrado de la sustentación está en `AE4/GUION_PRESENTACION.md`.

El notebook de la AE3 regenera en cada ejecución:

- `AE3/datos/dataset_preparado.csv` — DataFrame final (17.379 × 40).
- `AE3/resultados/tabla_*.csv` — una tabla por pregunta de negocio y las de control.
- `AE3/resultados/resumen_dataframe.txt` — reporte descriptivo del DataFrame final.

---

## Etapas

### EA1 · Carga y transformación

```
HFDatasetLoader  →  DataFrame  →  5 transformaciones  →  DatasetSummarizer  →  .txt
```

Las cinco transformaciones de la EA1 son: renombrar columnas al español,
seleccionar un subconjunto, filtrar días laborables, crear columnas calculadas
y agrupar por temporada. El `resumen_dataset.txt` corresponde a ese DataFrame
transformado (11.865 filas × 16 columnas).

### AE2 · Reconocimiento del dataset

Describe el dataset (metadata descriptiva): estructura, tipos, dominios,
cobertura y calidad. Genera `AE2/resultados/resumen_dataframe.txt` desde el
DataFrame original (17.379 × 17).

### AE3 · Transformación y enriquecimiento

Prepara el dataset para responder las preguntas de negocio de la AE2:

1. **Transforma** y valida: fechas, escalas, códigos, tipos, duplicados,
   consistencia del total y cobertura. Registra el efecto de cada regla.
2. **Enriquece**: variables de calendario, participación de cada tipo de
   usuario, rangos de temperatura y cruce con la tabla diaria.
3. **Responde**: una tabla por pregunta (franja horaria, tipo de día,
   temporada, año, clima, tipo de usuario) exportada a `.csv`.
4. **Documenta** las decisiones en el notebook y en el documento de la etapa.

Resultado: 8 reglas de transformación (0 registros eliminados), 12 variables
nuevas y un DataFrame final de **17.379 × 40**.

| Tabla | Pregunta que responde |
|---|---|
| `tabla_1a_franjas_horarias.csv` | ¿Cómo se reparte la demanda en el día? |
| `tabla_1b_por_hora.csv` | ¿Cuál es la demanda promedio de cada hora? |
| `tabla_2_tipo_dia.csv` | ¿Cambia entre días laborables y no laborables? |
| `tabla_3a_temporada.csv` | ¿Cambia con la temporada? |
| `tabla_3b_anio.csv` | ¿Cambia entre 2011 y 2012? |
| `tabla_3c_temporada_por_anio.csv` | ¿Y dentro de cada temporada? |
| `tabla_4a_clima.csv` | ¿Cambia con la condición climática? |
| `tabla_4b_rango_temperatura.csv` | ¿Cambia con la temperatura? |
| `tabla_5a_tipo_usuario.csv` | ¿Qué peso tienen casuales y registrados? |
| `tabla_5b_usuario_por_tipo_dia.csv` | ¿Y según el tipo de día? |
| `tabla_6a_concentracion_horaria.csv` | ¿Cuánto pesa una hora dentro de su día? |
| `tabla_6b_dias_mayor_demanda.csv` | ¿Qué días concentran más rentas? |

### AE4 · Métricas y visualización

Convierte las tablas de la AE3 en una aplicación que responde las seis preguntas
de negocio: cada sección declara la métrica, su unidad, el gráfico, la lectura de
los datos, la decisión que puede apoyar y la limitación del análisis.

| # | Pregunta | Métrica | Unidad |
|---|---|---|---|
| 1 | ¿Cuánta demanda hay y cómo se reparte en el día? | rentas totales, promedio y mediana por hora | rentas/hora |
| 2 | ¿En qué franjas horarias se concentra? | participación de cada franja y veces el promedio | % y múltiplo |
| 3 | ¿Cambia según el tipo de día? | promedio por hora y peso del usuario ocasional | rentas/hora y % |
| 4 | ¿Cambia con la temporada y entre 2011 y 2012? | promedio por temporada y variación anual | rentas/hora y % |
| 5 | ¿Cambia con el clima y la temperatura? | promedio por condición y por rango de temperatura | rentas/hora |
| 6 | ¿Qué peso tienen casuales y registrados? | participación de cada tipo de usuario | % |

---

## Notas y limitaciones

- Los datos son reales, no sintéticos. El enriquecimiento se hizo con variables
  derivadas del propio dataset; **no se usaron fuentes externas** porque las 17
  variables originales cubren las preguntas planteadas.
- Las variables categóricas vienen **codificadas numéricamente** (temporada 1–4,
  clima 1–4, año 0/1). Su significado está documentado en el README oficial de
  UCI, no se deduce de los datos.
- Temperatura, humedad y viento vienen **normalizados**: la temperatura está
  dividida entre 41, la humedad entre 100 y el viento entre 67.
- Faltan **165 horas** de las 17.544 esperadas, repartidas en 76 días
  incompletos. No se imputaron: se marcan con `dia_completo`.
- La condición climática de tormenta solo aparece en **3 registros**, por lo que
  su promedio no es representativo.
- El dataset solo cubre Washington D.C. y dos años; no permite generalizar a
  otras ciudades ni hacer afirmaciones sobre años posteriores.
- No contiene información de estaciones, flota ni usuarios individuales, por lo
  que no permite analizar la oferta ni perfiles personales.
