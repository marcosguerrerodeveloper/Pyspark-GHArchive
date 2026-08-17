"""Sesion de Spark compartida por los jobs.

Centraliza las dos correcciones de entorno que la Fase -1 destapo en Windows
(D5 y D6), para no repetirlas en cada entrypoint.
"""

import os
import shutil
import sys
from pathlib import Path

from pyspark.sql import SparkSession


def raiz_datos() -> str:
    return os.environ.get("GHA_DATA_DIR", "D:/gharchive-data")


def tam_directorio(ruta: Path) -> int:
    return sum(f.stat().st_size for f in ruta.rglob("*") if f.is_file())


def limpiar_staging(destino: Path) -> None:
    """Borra los .spark-staging huerfanos de ejecuciones que fallaron.

    Con partitionOverwriteMode=dynamic, Spark escribe primero en un directorio
    temporal y lo promueve al final. Si el job muere antes, ese temporal se
    queda ahi para siempre. Se detecto uno de 2,912 GiB, mas que la particion
    buena; en un backfill de cientos de dias eso revienta el presupuesto sin
    avisar, asi que se limpia al arrancar (D20).
    """
    if not destino.exists():
        return
    for resto in destino.glob(".spark-staging-*"):
        if resto.is_dir():
            tam = tam_directorio(resto)
            shutil.rmtree(resto, ignore_errors=True)
            print(f"staging huerfano borrado: {resto.name} ({tam/1024**3:.3f} GiB)")


def crear_sesion(nombre: str, nucleos: int = 8, memoria: str = "8g",
                 codec: str = "zstd") -> SparkSession:
    # Los workers de Python no heredan el venv en Windows y Spark muere con
    # "Python worker failed to connect back" (D6).
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    sesion = (
        SparkSession.builder.appName(nombre)
        .master(f"local[{nucleos}]")
        .config("spark.driver.memory", memoria)
        .config("spark.sql.shuffle.partitions", str(nucleos * 2))
        # GH Archive marca los instantes en UTC. Sin esto, to_timestamp los
        # convierte a la zona de la maquina (UTC+2 aqui) y un dia deja de
        # empezar a medianoche: se desplazan las agregaciones diarias y las
        # latencias. El dato es global, la zona de quien lo procesa no pinta.
        .config("spark.sql.session.timeZone", "UTC")
        # zstd sobre snappy: bronze guarda JSON en texto, muy redundante, y ahi
        # zstd rinde mucho mejor sin coste apreciable de CPU.
        .config("spark.sql.parquet.compression.codec", codec)
        # Sin esto, escribir una particion que ya existe borra el resto.
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        # El shuffle va al temporal del sistema, que aqui esta en C: con 90 GB.
        # Un dropDuplicates sobre bronze completo genero 581 GiB de blockmgr y
        # dejo el disco de sistema en 0,5 GB. El scratch vive en D:, junto a los
        # datos, donde hay sitio de sobra.
        .config("spark.local.dir", str(Path(raiz_datos()) / "spark-tmp"))
        .getOrCreate()
    )
    sesion.sparkContext.setLogLevel("WARN")
    return sesion
