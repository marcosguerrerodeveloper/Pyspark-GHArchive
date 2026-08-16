"""Fase 2 - bronze: eventos crudos a Parquet particionado por fecha.

Bronze no transforma. Guarda la linea JSON integra en una columna de texto, y
extrae al lado solo lo imprescindible para poder particionar y localizar un
evento sin volver a parsear: id, tipo, instante, actor y repo.

Por que el JSON crudo y no el esquema inferido por Spark: el formato de GH
Archive cambio el 2025-10-09 (D12) y un esquema inferido produciria ficheros
incompatibles a un lado y otro de esa fecha. Guardando el texto, bronze es
inmune al cambio y el tipado ocurre en silver, que es donde el plan lo situa.

Uso:
    python spark_jobs/bronze.py --fecha 2025-08-13
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

from pyspark.sql import functions as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sesion import crear_sesion, raiz_datos  # noqa: E402


def tam_directorio(ruta: Path) -> int:
    return sum(f.stat().st_size for f in ruta.rglob("*") if f.is_file())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fecha", required=True, help="YYYY-MM-DD")
    p.add_argument("--borrar-crudo", action="store_true",
                   help="borra los .gz del dia una vez escrito bronze")
    p.add_argument("--json-completo", default="todos",
                   help="'todos' o lista de tipos separados por coma cuyo JSON "
                        "integro se conserva; en el resto se guardan solo las "
                        "columnas extraidas")
    args = p.parse_args()

    raiz = Path(raiz_datos())
    origen = raiz / "raw" / args.fecha
    destino = raiz / "bronze"

    if not origen.exists():
        print(f"No hay datos crudos en {origen}")
        return 1

    ficheros = sorted(origen.glob("*.json.gz"))
    bytes_origen = sum(f.stat().st_size for f in ficheros)
    print(f"{len(ficheros)} ficheros, {bytes_origen:,} B comprimidos")

    spark = crear_sesion("bronze")
    inicio = time.monotonic()

    # text() en vez de json(): no infiere esquema, no parsea, no falla si el
    # formato cambia. Una fila por evento.
    crudo = spark.read.text(str(origen))

    # get_json_object extrae campos sueltos sin construir el objeto entero.
    bronze = (
        crudo
        .withColumn("id", F.get_json_object("value", "$.id"))
        .withColumn("type", F.get_json_object("value", "$.type"))
        .withColumn("created_at", F.get_json_object("value", "$.created_at"))
        .withColumn("actor_login", F.get_json_object("value", "$.actor.login"))
        .withColumn("repo_name", F.get_json_object("value", "$.repo.name"))
        .withColumnRenamed("value", "evento_json")
        .withColumn("event_date", F.lit(args.fecha))
    )

    # Proyeccion por tipo. Las cinco columnas extraidas se conservan siempre, y
    # con ellas la pregunta 3 (quien contribuye, donde y cuando) queda completa
    # para TODOS los eventos. El JSON integro solo hace falta en los tipos que
    # alimentan las preguntas 1 y 2, y es lo que se lleva casi todo el disco.
    if args.json_completo != "todos":
        tipos = [t.strip() for t in args.json_completo.split(",") if t.strip()]
        print(f"JSON integro solo para: {tipos}")
        bronze = bronze.withColumn(
            "evento_json",
            F.when(F.col("type").isin(tipos), F.col("evento_json")),
        )

    (bronze.write
        .mode("overwrite")
        .partitionBy("event_date")
        .parquet(str(destino)))

    duracion = time.monotonic() - inicio
    particion = destino / f"event_date={args.fecha}"
    bytes_destino = tam_directorio(particion)

    # Se releen desde disco para contar: confirma que lo escrito es legible, no
    # solo que el job no reventó.
    filas = spark.read.parquet(str(particion)).count()

    print(f"\nfilas escritas      : {filas:,}")
    print(f"origen (.gz)        : {bytes_origen:,} B ({bytes_origen/1024**3:.3f} GiB)")
    print(f"bronze (parquet)    : {bytes_destino:,} B ({bytes_destino/1024**3:.3f} GiB)")
    print(f"ratio bronze/origen : {bytes_destino/bytes_origen:.3f}×")
    print(f"duracion            : {duracion:.1f}s")
    spark.stop()

    if args.borrar_crudo:
        # Solo despues de haber releido y contado: si la lectura fallara, no se
        # habria llegado hasta aqui.
        shutil.rmtree(origen)
        print(f"crudo borrado: {origen}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
