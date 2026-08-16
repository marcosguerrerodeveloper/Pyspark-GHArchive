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
from sesion import crear_sesion, limpiar_staging, raiz_datos, tam_directorio  # noqa: E402


TIPOS_JSON_COMPLETO = ("PullRequestEvent,PullRequestReviewEvent,"
                       "PullRequestReviewCommentEvent,IssuesEvent,IssueCommentEvent")


def procesar_dia(spark, fecha: str, json_completo: str = "todos",
                 borrar_crudo: bool = False) -> dict:
    """Escribe un dia en bronze. Devuelve las metricas del dia.

    Separado de main() para que el backfill pueda encadenar cientos de dias
    reutilizando una sola sesion de Spark: arrancar la JVM por dia anadiria mas
    de una hora al total.
    """
    raiz = Path(raiz_datos())
    origen = raiz / "raw" / fecha
    destino = raiz / "bronze"

    if not origen.exists():
        raise FileNotFoundError(f"No hay datos crudos en {origen}")

    ficheros = sorted(origen.glob("*.json.gz"))
    bytes_origen = sum(f.stat().st_size for f in ficheros)

    limpiar_staging(destino)
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
        .withColumn("event_date", F.lit(fecha))
    )

    # Proyeccion por tipo. Las cinco columnas extraidas se conservan siempre, y
    # con ellas la pregunta 3 (quien contribuye, donde y cuando) queda completa
    # para TODOS los eventos. El JSON integro solo hace falta en los tipos que
    # alimentan las preguntas 1 y 2, y es lo que se lleva casi todo el disco.
    if json_completo != "todos":
        tipos = [t.strip() for t in json_completo.split(",") if t.strip()]
        bronze = bronze.withColumn(
            "evento_json",
            F.when(F.col("type").isin(tipos), F.col("evento_json")),
        )

    (bronze.write
        .mode("overwrite")
        .partitionBy("event_date")
        .parquet(str(destino)))

    duracion = time.monotonic() - inicio
    particion = destino / f"event_date={fecha}"
    bytes_destino = tam_directorio(particion)

    # Se relee desde disco para contar: confirma que lo escrito es legible, no
    # solo que el job no reventó.
    filas = spark.read.parquet(str(particion)).count()

    if borrar_crudo:
        # Solo despues de haber releido y contado: si la lectura fallara, no se
        # habria llegado hasta aqui y el crudo seguiria estando.
        shutil.rmtree(origen)

    return {
        "fecha": fecha,
        "filas": filas,
        "bytes_origen": bytes_origen,
        "bytes_bronze": bytes_destino,
        "segundos": round(duracion, 1),
        "crudo_borrado": borrar_crudo,
    }


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

    spark = crear_sesion("bronze")
    try:
        m = procesar_dia(spark, args.fecha, args.json_completo, args.borrar_crudo)
    except FileNotFoundError as exc:
        print(exc)
        spark.stop()
        return 1

    print(f"\nfilas escritas      : {m['filas']:,}")
    print(f"origen (.gz)        : {m['bytes_origen']:,} B "
          f"({m['bytes_origen']/1024**3:.3f} GiB)")
    print(f"bronze (parquet)    : {m['bytes_bronze']:,} B "
          f"({m['bytes_bronze']/1024**3:.3f} GiB)")
    print(f"ratio bronze/origen : {m['bytes_bronze']/m['bytes_origen']:.3f}x")
    print(f"duracion            : {m['segundos']}s")
    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
