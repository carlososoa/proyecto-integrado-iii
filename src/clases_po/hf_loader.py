"""
Carga datasets de Hugging Face y, opcionalmente, los guarda en disco.

=========================================================================
¿QUÉ HACE ESTE ARCHIVO EN LA VIDA REAL?
=========================================================================

Hugging Face (huggingface.co) es una página web donde personas y empresas
publican DATASETS (tablas de datos en formato CSV/Parquet) y MODELOS de IA.
Cualquiera puede descargar un dataset con una función llamada load_dataset().

El problema: load_dataset() devuelve un objeto "Dataset" propio de la
librería `datasets`, NO un DataFrame de pandas. Entonces, para trabajar
cómodo con pandas uno tendría que hacer la conversión a mano cada vez.

La clase HFDatasetLoader de abajo es un "envoltorio" (wrapper) que resuelve
eso de una vez y para siempre. Tiene 3 beneficios:
    1. Todo se configura desde el constructor (__init__).
    2. .load() devuelve directamente un pandas.DataFrame.
    3. Opcionalmente guarda ese DataFrame en csv / json / parquet / xlsx.

Así, cada semana del curso solo hay que escribir:

    loader = HFDatasetLoader("nombre/del/dataset", filename="datos/x.csv")
    df = loader.load()

y ya se tiene el DataFrame listo, sin repetir código.
=========================================================================
"""

# Esta línea es una "importación diferida de anotaciones". Sirve para que las
# anotaciones de tipos que usan sintaxis moderna (por ejemplo `str | None`,
# que significa "texto o nada") NO se evalúen en tiempo de ejecución.
# Sin ella, en versiones viejas de Python habría error, porque la barra
# vertical no se entendía antes de Python 3.10.
from __future__ import annotations

# Path: viene de la librería estándar. Su trabajo es representar rutas de
# archivos y carpetas como objetos, en vez de manejar strings sueltos.
# Ventaja: Path("datos/archivo.csv").parent te da "datos" sin hacer malabares
# con split("/"), y .mkdir() crea carpetas. Funciona igual en Windows, Linux
# y macOS.
from pathlib import Path

# Literal: es una herramienta SOLO para el editor y para quien lea el código.
# `Literal["csv", "json"]` significa "este parámetro sólo acepta exactamente
# esos textos". No valida nada en tiempo de ejecución; es documentación
# que el autocompletado del editor entiende.
from typing import Literal

# load_dataset: la función de la librería `datasets` que descarga el dataset
# desde internet (o desde la caché local si ya se descargó antes).
from datasets import load_dataset

# pandas: la librería de tablas de datos. Se importa con el alias pd, que es
# la convención universal en la comunidad, para no escribir "pandas."
# completo cada vez.
import pandas as pd

# Aquí se define un ALIAS de tipo (type alias). Básicamente se le pone nombre
# a la restricción "solo vale csv, json, parquet o xlsx".
# ¿Para qué? Para no repetir la lista larga en cada parámetro; se escribe
# FileType una sola vez y queda más legible.
FileType = Literal["csv", "json", "parquet", "xlsx"]


# `class` crea un molde (una plantilla) para fabricar objetos.
# Un objeto es una "cajita" que tiene datos (atributos) y acciones (métodos).
# En este caso la cajita se llamará HFDatasetLoader y sabrá descargar datasets.
class HFDatasetLoader:
    """Descarga un dataset de Hugging Face y lo devuelve como DataFrame.

    Lo que va entre las tres comillas dobles justo debajo de `class` es el
    DOCSTRING: la documentación del objeto. Python lo guarda en memoria y
    herramientas como Jupyter o el comando help() lo muestran al usuario.
    No afecta la ejecución, es solo documentación legible.

    Args:
        dataset_name: Identificador del dataset en Hugging Face. El formato es
            "usuario/nombre-del-dataset", por ejemplo
            "JasonZhouTI/Fast_Food_Restaurants".
        config: Si el dataset tiene varias "configuraciones" (sub-versiones),
            aquí se elige cuál. Si no tiene, se deja en None.
        split: Qué división cargar. En machine learning los datasets se parten
            en "train" (entrenamiento), "test" (prueba) y a veces "validation"
            (validación). Por defecto se usa "train".
        token: Contraseña/clave de Hugging Face para datasets privados.
            Si el dataset es público, queda en None.
        cache_dir: Carpeta donde Hugging Face guarda lo descargado para no
            volver a bajarlo. Si es None, usa la carpeta por defecto del sistema.
        max_rows: Cantidad máxima de filas a cargar. Útil para no gastar
            memoria cuando el dataset tiene millones de filas.
        filename: Ruta opcional donde se guardará el DataFrame ya descargado.
        file_type: Formato opcional de salida: csv, json, parquet o xlsx.
            Si no se indica, se adivina a partir de la extensión de filename.
    """

    # El guion bajo al inicio del nombre (_SUPPORTED_FILE_TYPES) es una
    # CONVENCIÓN de Python que dice: "esto es interno, no lo uses desde fuera".
    # Python NO lo impide (no es privado de verdad, como en Java), es solo un
    # aviso para otros programadores.
    #
    # Las llaves {...} crean un `set` (conjunto): una colección SIN orden y
    # SIN duplicados. Es ideal para preguntar "¿este valor está en la lista?"
    # porque la búsqueda es instantánea.
    _SUPPORTED_FILE_TYPES = {"csv", "json", "parquet", "xlsx"}

    # DEF __INIT__ es el CONSTRUCTOR: el método que se ejecuta automáticamente
    # cuando se crea el objeto, es decir, al escribir HFDatasetLoader(...).
    # `self` es SIEMPRE el primer parámetro y representa al objeto que se está
    # creando. Es la manera en que el objeto se refiere a sí mismo.
    # (Por eso cada método de la clase lo recibe como primer argumento.)
    def __init__(
        self,  # referencia al objeto mismo (automático, no se pasa a mano)
        dataset_name: str,  # nombre del dataset en Hugging Face, obligatorio
        config: str | None = None,  # "texto o None", opcional, por defecto None
        split: str = "train",  # qué división cargar, por defecto "train"
        token: str | None = None,  # clave para datasets privados, opcional
        cache_dir: str | None = None,  # carpeta de caché, opcional
        max_rows: int | None = None,  # límite de filas, opcional
        filename: str | Path | None = None,  # ruta de salida, opcional
        file_type: str | None = None,  # formato de salida, opcional
    ) -> None:  # -> None significa "no devuelve nada", solo guarda datos
        # Cada línea `self.algo = ...` GUARDA el valor dentro del objeto.
        # Al hacerlo, ese valor queda disponible para todos los demás métodos
        # de la clase. Es el equivalente a "propiedades" en otros lenguajes.
        # Ojo con el nombre repetido: a la izquierda es el atributo del objeto,
        # a la derecha es el parámetro que llegó al constructor.
        self.dataset_name = dataset_name
        self.config = config
        self.split = split
        self.token = token
        self.cache_dir = cache_dir
        self.max_rows = max_rows

        # Aquí hay una conversión: sea que llegue un texto ("datos/x.csv") o
        # un Path ya armado, se guarda SIEMPRE como Path, para que los métodos
        # puedan usar .parent, .mkdir(), .suffix, etc. Si no llegó nada (None)
        # se guarda None, porque no hay ruta de salida configurada.
        self.filename = Path(filename) if filename is not None else None

        # Se llama al método de validación que está más abajo. Se usa `self.`
        # porque es un método de la propia clase. Nos aseguramos de que el
        # tipo de archivo sea válido desde que se crea el objeto, no después.
        self.file_type = self._normalize_file_type(file_type)

        # Aquí el objeto "aparta el espacio" para el DataFrame. Se inicializa
        # en None porque todavía no se ha descargado nada. Cuando se llame a
        # .load(), aquí quedará el DataFrame real. Es como un casillero vacío.
        # La anotación `pd.DataFrame | None` aclara: "aquí habrá una tabla
        # o estará vacío".
        self.df: pd.DataFrame | None = None

        # VALIDACIONES. Regla de oro: detectar el error lo más pronto posible,
        # en el constructor, y no tres métodos después cuando es más difícil
        # saber de dónde vino el problema.
        #
        # `is not None` = "sí se indicó un límite de filas".
        # `and self.max_rows < 0` = "y además ese límite es negativo".
        # Si ambas cosas se cumplen, se lanza un error que detiene el programa.
        if self.max_rows is not None and self.max_rows < 0:
            # raise ValueError lanza una EXCEPCIÓN: un error controlado que
            # interrumpe la ejecución y muestra el mensaje al usuario.
            # Se usa ValueError porque el valor recibido no es válido.
            raise ValueError("max_rows debe ser mayor o igual que cero.")

        # Segundo chequeo: si dijiste el formato ("parquet") pero no dijiste
        # dónde guardarlo, es una contradicción. Sin ruta, ¿dónde escribiría?
        # Por eso se prohíbe esa combinación.
        if self.file_type is not None and self.filename is None:
            raise ValueError("filename es obligatorio cuando se indica file_type.")

    # Método principal. La anotación `-> pd.DataFrame` promete que devuelve
    # una tabla de pandas. Se declara SIN decorador, así que es un método
    # normal de instancia: recibe `self`.
    def load(self) -> pd.DataFrame:
        """Descarga el dataset, lo guarda si se configuró una salida y retorna el DataFrame."""

        # LA LÍNEA MÁS IMPORTANTE DEL ARCHIVO. Esta función es la que
        # realmente va a internet, descarga los archivos del dataset y los
        # convierte al objeto "Dataset" de la librería datasets.
        # Cada argumento es un parámetro POSICIONAL: el orden importa.
        #   1) self.dataset_name -> "JasonZhouTI/Fast_Food_Restaurants"
        #   2) self.config       -> la sub-configuración (aquí None)
        #   3) split=...         -> qué parte cargar ("train")
        #   4) token=...         -> credencial (None = público)
        #   5) cache_dir=...     -> dónde cachear (None = carpeta por defecto)
        # Si ya se descargó antes, NO vuelve a bajar nada: lee de la caché,
        # y por eso la segunda ejecución es rapidísima.
        dataset = load_dataset(
            self.dataset_name,
            self.config,
            split=self.split,
            token=self.token,
            cache_dir=self.cache_dir,
        )

        # Si el usuario pidió un límite de filas, se recorta el dataset.
        if self.max_rows is not None:
            # `.select(range(...))` toma las posiciones indicadas.
            # `min(self.max_rows, len(dataset))` evita el error de "índice
            # fuera de rango": si el dataset tiene 10 000 filas y pides 50 000,
            # se usan las 10 000 (el mínimo de los dos números) y no explota.
            # range(10000) genera 0,1,2,...,9999, que son las posiciones.
            dataset = dataset.select(range(min(self.max_rows, len(dataset))))

        # TRADUCCIÓN DE FORMATO. to_pandas() convierte el Dataset de Hugging
        # Face en un DataFrame de pandas, que es el formato con el que se
        # trabaja en todo el resto del curso (filtros, gráficas, etc.).
        self.df = dataset.to_pandas()

        # Condicional en UNA sola línea, se lee de derecha a izquierda:
        # "si hay una ruta de salida configurada (filename no es None),
        #  entonces ejecuta la función _save".
        # Se guarda en el atributo `self.df` y además se escribe en disco.
        if self.filename is not None:
            self._save(self.df)

        # `return` entrega el resultado a quien llamó al método.
        # En el notebook:  df = loader.load()  ->  df recibe este DataFrame.
        return self.df

    # Método informativo. Devuelve un diccionario (dict) con datos resumidos.
    # La anotación `dict[str, str | int | None]` se lee: "diccionario donde
    #  las claves son texto y los valores son texto, entero o None".
    def info(self) -> dict[str, str | int | None]:
        """Devuelve información básica del último DataFrame cargado."""

        # Protección contra el uso incorrecto: si todavía nadie llamó a
        # load(), self.df sigue siendo None (el casillero vacío).
        # len(None) fallaría con un error confuso, así que se lanza antes un
        # mensaje claro que explica qué hacer.
        if self.df is None:
            raise RuntimeError("Llama a load() primero.")

        # Se construye y se devuelve un diccionario literal.
        # Cada bloque "clave": valor es una entrada.
        #   len(self.df)          -> cuántas filas tiene la tabla
        #   len(self.df.columns)  -> cuántas columnas tiene la tabla
        return {
            "dataset": self.dataset_name,
            "config": self.config,
            "split": self.split,
            "filas": len(self.df),
            "columnas": len(self.df.columns),
        }

    # @classmethod hace que el método se llame sobre la CLASE y no sobre un
    # objeto:  HFDatasetLoader._normalize_file_type("csv")
    # Se usa `cls` (no `self`) como primer parámetro. `cls` es la propia clase.
    # Ventaja: se puede usar antes de tener un objeto creado, justamente
    # porque __init__ necesita normalizar el tipo antes de terminar de existir.
    @classmethod
    def _normalize_file_type(cls, file_type: str | None) -> str | None:
        # Si no se indicó formato, no hay nada que normalizar: se devuelve
        # None tal cual y el objeto decide después si puede inferirlo de la
        # extensión del archivo.
        if file_type is None:
            return None

        # Encadenamiento de métodos (se lee de izquierda a derecha):
        #   1. file_type.lower()   -> pasa todo a minúsculas: "CSV" -> "csv"
        #   2. .lstrip(".")        -> quita puntos del inicio: ".csv" -> "csv"
        # Así "CSV", ".csv" y "csv" se tratan por igual. Tolerancia con el
        # usuario: no lanzar error por una mayúscula o un punto.
        normalized = file_type.lower().lstrip(".")

        # Comodidad: si alguien escribe "excel" (que es como lo llama Microsoft),
        # se traduce al nombre técnico real del formato: xlsx.
        if normalized == "excel":
            normalized = "xlsx"

        # Verificación final contra el conjunto de formatos permitidos.
        # `not in` responde: "¿este valor NO está dentro del set?".
        if normalized not in cls._SUPPORTED_FILE_TYPES:
            # `", ".join(sorted(...))` arma un texto legible. Paso a paso:
            #   sorted() ordena alfabéticamente -> ['csv','json','parquet','xlsx']
            #   ", ".join(...) los pega con coma -> "csv, json, parquet, xlsx"
            # Se usa en el mensaje de error para decirle al usuario qué sí vale.
            supported = ", ".join(sorted(cls._SUPPORTED_FILE_TYPES))
            # f"..." es un f-string: el texto entre llaves {file_type} se
            # reemplaza por el valor real de esa variable al ejecutar.
            raise ValueError(f"Tipo de archivo no soportado: {file_type}. Use: {supported}.")

        # Se devuelve el valor ya limpio y validado ("csv", no " CSV ").
        return normalized

    # Método privado (empieza con _) que escribe el DataFrame en disco.
    def _save(self, df: pd.DataFrame) -> None:
        # `assert` es una afirmación para el programador: "yo garantizo que
        # aquí self.filename NO es None". Si lo fuera, el programa explota con
        # AssertionError. No es validación para el usuario, es una red de
        # seguridad interna. El verificador del editor también lo entiende
        # y deja de avisar que self.filename podría ser None.
        assert self.filename is not None

        # OR: se usa el formato que pidió el usuario (self.file_type); si no
        # pidió ninguno (None), se ADIVINA a partir de la extensión del archivo.
        # .suffix de un Path devuelve la extensión CON el punto: ".csv".
        # Por eso _normalize_file_type se encarga de quitarle el punto (lstrip).
        # Resultado: guardar en "datos/x.csv" funciona sin indicar file_type.
        file_type = self.file_type or self._normalize_file_type(self.filename.suffix)

        # Si después de todo no se pudo saber el formato (por ejemplo, el
        # archivo se llamaba "datos" sin extensión), no se puede escribir:
        # se detiene con un mensaje que dice cómo solucionarlo.
        if file_type is None:
            raise ValueError(
                "No se pudo inferir el tipo de archivo. Indique file_type "
                "o use una extensión compatible en filename."
            )

        # Se crea la carpeta destino si no existe.
        # .parent -> la carpeta que contiene al archivo ("datos/x.csv" -> "datos")
        # parents=True  -> crea también las carpetas intermedias (a/b/c)
        # exist_ok=True -> si la carpeta ya existe, NO lanza error (sin esto,
        #                  un segundo guardado fallaría).
        self.filename.parent.mkdir(parents=True, exist_ok=True)

        # Cadena de if/elif: se comprueba el formato y se usa el método de
        # pandas que corresponde. `index=False` en todos significa "NO escribas
        # la columna de números de fila (0,1,2...) a la izquierda", porque esa
        # no es un dato real del dataset.
        if file_type == "csv":
            df.to_csv(self.filename, index=False)
        elif file_type == "json":
            # orient="records" escribe una lista de objetos: [{...}, {...}],
            # que es el JSON natural y el que entienden las APIs.
            # force_ascii=False conserva tildes y ñ en vez de escribir \u00f1.
            df.to_json(self.filename, orient="records", force_ascii=False)
        elif file_type == "parquet":
            # Parquet es un formato binario comprimido: muchísimo más rápido
            # y liviano que CSV para datasets grandes. Necesita la librería
            # pyarrow (por eso el README y el workflow la instalan aparte).
            df.to_parquet(self.filename, index=False)
        elif file_type == "xlsx":
            # Excel. Necesita la librería openpyxl (instalada aparte también).
            df.to_excel(self.filename, index=False)
