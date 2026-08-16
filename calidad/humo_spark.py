"""Prueba de humo de la Fase -1.

Verifica que Spark arranca sobre la JVM correcta y que sabe escribir y releer
Parquet particionado en este sistema de ficheros. Es el punto de decision
D1: si esto falla, se migra el entorno a WSL2 antes de invertir mas.

Uso:
    .venv\\Scripts\\python.exe calidad\\humo_spark.py
"""

import os
import shutil
import sys
import tempfile

from pyspark.sql import SparkSession


def main() -> int:
    # En Windows, Spark lanza los workers de Python sin heredar el venv y falla
    # con "Python worker failed to connect back". Apuntarlos al interprete
    # actual lo resuelve, y hace el script independiente del entorno.
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    print("JAVA_HOME =", os.environ.get("JAVA_HOME", "(no definido)"))
    print("HADOOP_HOME =", os.environ.get("HADOOP_HOME", "(no definido)"))

    spark = (
        SparkSession.builder.appName("humo-fase-menos-1")
        .master("local[4]")
        .config("spark.driver.memory", "4g")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    print("Spark", spark.version)

    destino = os.path.join(tempfile.gettempdir(), "humo_spark_parquet")
    shutil.rmtree(destino, ignore_errors=True)

    # Dos fechas para ejercitar el particionado, que es como escribira bronze.
    filas = [(i, f"actor_{i % 7}", "2026-08-15" if i % 2 else "2026-08-16") for i in range(1000)]
    df = spark.createDataFrame(filas, ["id", "actor", "event_date"])

    df.write.mode("overwrite").partitionBy("event_date").parquet(destino)
    releido = spark.read.parquet(destino)

    total = releido.count()
    particiones = releido.select("event_date").distinct().count()
    print(f"filas escritas=1000 releidas={total} particiones={particiones}")

    ok = total == 1000 and particiones == 2
    shutil.rmtree(destino, ignore_errors=True)
    spark.stop()

    print("RESULTADO:", "OK" if ok else "FALLO")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
