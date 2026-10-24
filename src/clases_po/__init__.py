"""
Este archivo convierte la carpeta `clases_po` en un PAQUETE de Python.

=========================================================================
¿QUÉ ES UN PAQUETE Y PARA QUÉ SIRVE EL __init__.py?
=========================================================================

Un paquete es simplemente una carpeta llena de archivos .py que Python
puede importar. El archivo __init__.py es lo PRIMERO que Python ejecuta
cuando alguien hace:

    from clases_po import ...

Sin __init__.py, Python (en versiones anteriores a la 3.3) no reconocía
la carpeta como paquete. Hoy técnicamente es opcional, pero se sigue
usando porque permite "reexportar" cosas cómodamente, como se hace abajo.

En vez de escribir la ruta completa al archivo interno:

    from clases_po.hf_loader import HFDatasetLoader
    from clases_po.summarizer import DatasetSummarizer

...los usuarios del paquete escriben simplemente:

    from clases_po import HFDatasetLoader, DatasetSummarizer

Es más corto, más limpio, y si algún día se reorganizan los archivos
internos, quien usa el paquete no tiene que cambiar nada. Se convierte en
una "fachada": el paquete decide qué muestra hacia afuera.
=========================================================================
"""

# Sintaxis del import:
#   `from .`   -> el punto significa "desde este MISMO paquete" (import relativo).
#                La diferencia con "from clases_po..." es que el punto no
#                depende del nombre de la carpeta: si el paquete se renombra,
#                el import sigue funcionando.
#   `hf_loader` -> el archivo (módulo) hf_loader.py
#   `import HFDatasetLoader` -> la clase que está dentro de ese archivo
from .hf_loader import HFDatasetLoader

# Igual, pero desde el archivo summarizer.py, trayendo la clase DatasetSummarizer.
from .summarizer import DatasetSummarizer

# __all__ define la LISTA PÚBLICA del paquete. Es lo que se exporta cuando
# alguien escribe `from clases_po import *`.
# También le dice a los editores (VS Code, PyCharm) y a herramientas como
# los linters cuáles nombres son de uso público y cuáles son internos.
# Ojo: los nombres NO listados aquí siguen siendo accesibles si se escriben
# explícitamente; __all__ solo controla el atajo del asterisco.
__all__ = ["HFDatasetLoader", "DatasetSummarizer"]
