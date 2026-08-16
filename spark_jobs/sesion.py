"""Sesion de Spark compartida por los jobs.

Centraliza las dos correcciones de entorno que la Fase -1 destapo en Windows
(D5 y D6), para no repetirlas en cada entrypoint.
"""

import os
import sys

from pyspark.sql import SparkSession


def raiz_datos() -> str:
    return os.environ.get("GHA_DATA_DIR", "D:/gharchive-data")


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
        # zstd sobre snappy: bronze guarda JSON en texto, muy redundante, y ahi
        # zstd rinde mucho mejor sin coste apreciable de CPU.
        .config("spark.sql.parquet.compression.codec", codec)
        # Sin esto, escribir una particion que ya existe borra el resto.
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    sesion.sparkContext.setLogLevel("WARN")
    return sesion
