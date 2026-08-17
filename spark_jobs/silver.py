"""Fase 2 - silver: tipado, deduplicado y clasificado.

Escribe dos tablas, ambas particionadas por fecha:

  silver/eventos     un registro por evento, de cualquier tipo. Sostiene la
                     pregunta 3 (quien contribuye, donde y cuando).
  silver/pr_eventos  un registro por evento relacionado con un PR, con los
                     campos del payload ya extraidos. Sostiene las preguntas
                     1 y 2.

Los dos formatos de GH Archive conviven aqui. El formato no se decide por
fecha sino mirando si el payload trae los campos temporales del PR (D12): asi
el codigo no lleva el 2025-10-09 escrito dentro y no hay que tocarlo si la
fuente vuelve a cambiar.

Uso:
    python spark_jobs/silver.py --fecha 2025-08-13
    python spark_jobs/silver.py --desde 2025-06-01 --hasta 2025-10-08
"""

import argparse
import sys
import time
from pathlib import Path

from pyspark.sql import functions as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bots import CLASE_BOT_OTRO, CLASE_HUMANO, mapa_clases  # noqa: E402
from sesion import crear_sesion, limpiar_staging, raiz_datos  # noqa: E402

# Tipos que hablan de un PR. PullRequestReviewEvent es el que responde "cuando
# llego el primer review", asi que no puede faltar.
TIPOS_PR = [
    "PullRequestEvent",
    "PullRequestReviewEvent",
    "PullRequestReviewCommentEvent",
]


def json_str(columna, ruta):
    return F.get_json_object(columna, ruta)


def clasificar_actor(col_login):
    """humano / agente_ia / bot_dependencias / bot_ci / bot_otro.

    El sufijo "[bot]" lo pone GitHub a las cuentas de App, asi que es una senal
    fuerte y es la que decide si algo es automatico. La lista solo decide de
    que tipo, y lo que no reconoce cae en bot_otro en vez de colarse como
    humano.
    """
    login_base = F.regexp_replace(col_login, r"\[bot\]$", "")
    es_bot = col_login.endswith("[bot]")

    expresion = F.when(~es_bot, F.lit(CLASE_HUMANO))
    for login, clase in sorted(mapa_clases().items()):
        expresion = expresion.when(es_bot & (login_base == login), F.lit(clase))
    return expresion.otherwise(F.lit(CLASE_BOT_OTRO))


def construir_eventos(bronze):
    """Tabla de eventos: tipado, sin el JSON, con el actor clasificado.

    El dropDuplicates va DESPUES del select. Hacerlo antes obliga a Spark a
    barajar tambien evento_json, que es el texto integro y casi todo el peso de
    bronze: sobre el backfill completo eso genero 581 GiB de shuffle y lleno el
    disco de sistema. Proyectando primero, se barajan seis columnas cortas.
    """
    return (
        bronze
        .select(
            F.col("id").cast("long").alias("evento_id"),
            F.col("type").alias("tipo"),
            F.to_timestamp("created_at").alias("creado_en"),
            F.col("actor_login").alias("actor"),
            F.col("repo_name").alias("repo"),
            F.substring_index(F.col("repo_name"), "/", 1).alias("repo_owner"),
            F.col("event_date"),
        )
        .withColumn("actor_es_bot", F.col("actor").endswith("[bot]"))
        .withColumn("actor_clase", clasificar_actor(F.col("actor")))
        # Por (evento_id, event_date), NO solo por evento_id: en el formato
        # reducido GH Archive reutiliza identificadores, y se comprobo que un
        # mismo id designa un PushEvent el 2025-11-18 y un PullRequestEvent el
        # 2026-01-23. Deduplicar globalmente borraba eventos reales.
        .dropDuplicates(["evento_id", "event_date"])
    )


def construir_pr_eventos(bronze):
    """Tabla de eventos de PR con el payload ya extraido.

    Solo puede trabajar sobre filas que conserven evento_json, que por D18 son
    exactamente los tipos que aparecen en TIPOS_PR.
    """
    j = F.col("evento_json")

    pr = (
        bronze
        .filter(F.col("type").isin(TIPOS_PR) & j.isNotNull())
        .select(
            F.col("id").cast("long").alias("evento_id"),
            F.col("type").alias("tipo"),
            F.to_timestamp("created_at").alias("creado_en"),
            F.col("actor_login").alias("actor"),
            F.col("repo_name").alias("repo"),
            F.col("event_date"),

            # Identidad del PR. Es la clave que une los eventos entre si y a
            # traves de los dias (D8).
            json_str(j, "$.payload.pull_request.id").cast("long").alias("pr_id"),
            json_str(j, "$.payload.pull_request.number").cast("int").alias("pr_numero"),
            json_str(j, "$.payload.action").alias("accion"),

            # Solo en el formato completo.
            json_str(j, "$.payload.pull_request.created_at").alias("pr_abierto_en_txt"),
            json_str(j, "$.payload.pull_request.merged_at").alias("pr_mergeado_en_txt"),
            json_str(j, "$.payload.pull_request.closed_at").alias("pr_cerrado_en_txt"),
            json_str(j, "$.payload.pull_request.merged").alias("pr_merged_txt"),
            json_str(j, "$.payload.pull_request.base.repo.language").alias("repo_lenguaje"),
            json_str(j, "$.payload.pull_request.user.login").alias("pr_autor"),
            json_str(j, "$.payload.pull_request.user.type").alias("pr_autor_tipo"),
            json_str(j, "$.payload.pull_request.additions").cast("int").alias("pr_lineas_add"),
            json_str(j, "$.payload.pull_request.deletions").cast("int").alias("pr_lineas_del"),

            # Del review, cuando el evento es de review.
            json_str(j, "$.payload.review.state").alias("review_estado"),
            json_str(j, "$.payload.review.submitted_at").alias("review_enviado_en_txt"),
        )
    )

    return (
        pr
        .withColumn("pr_abierto_en", F.to_timestamp("pr_abierto_en_txt"))
        .withColumn("pr_mergeado_en", F.to_timestamp("pr_mergeado_en_txt"))
        .withColumn("pr_cerrado_en", F.to_timestamp("pr_cerrado_en_txt"))
        .withColumn("review_enviado_en", F.to_timestamp("review_enviado_en_txt"))
        .withColumn("pr_merged", F.col("pr_merged_txt") == "true")

        # Deteccion del formato por presencia de campo, nunca por fecha (D12).
        .withColumn(
            "esquema",
            F.when(F.col("pr_abierto_en_txt").isNotNull(), F.lit("completo"))
             .otherwise(F.lit("reducido")),
        )

        # El merge se expresa distinto en cada formato: antes era closed con
        # merged=true, y en el formato nuevo hay una accion "merged" propia.
        # Esta columna unifica ambos convenios para que gold no tenga que saber
        # en que epoca esta.
        # coalesce a false: en el formato reducido pr_merged es nulo y la
        # comparacion propagaba NULL a es_merge, dejando 335 cierres en un
        # tercer estado que no es ni si ni no. Ahi "closed" significa cerrado
        # sin mergear, porque el merge tiene su propia accion.
        .withColumn(
            "es_merge",
            F.coalesce(
                (F.col("accion") == "merged")
                | ((F.col("accion") == "closed") & (F.col("pr_merged") == True)),  # noqa: E712
                F.lit(False),
            ),
        )
        .withColumn("actor_es_bot", F.col("actor").endswith("[bot]"))
        .withColumn("actor_clase", clasificar_actor(F.col("actor")))
        .drop("pr_abierto_en_txt", "pr_mergeado_en_txt", "pr_cerrado_en_txt",
              "pr_merged_txt", "review_enviado_en_txt")
        # Igual que en eventos: sobre columnas ya extraidas, nunca arrastrando
        # evento_json al shuffle, y acotado al dia porque el id no es unico
        # entre fechas en el formato reducido.
        .dropDuplicates(["evento_id", "event_date"])
    )


def escribir(df, destino: Path, etiqueta: str) -> int:
    limpiar_staging(destino)
    (df.write
        .mode("overwrite")
        .partitionBy("event_date")
        .parquet(str(destino)))
    filas = df.sparkSession.read.parquet(str(destino)).count()
    print(f"{etiqueta}: {filas:,} filas -> {destino}")
    return filas


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fecha", help="un solo dia, YYYY-MM-DD")
    p.add_argument("--desde", help="YYYY-MM-DD")
    p.add_argument("--hasta", help="YYYY-MM-DD")
    # Las dos tablas se escriben por separado para poder reanudar. Sobre 360
    # dias una sola pasada dura demasiado, y si se corta a mitad se pierde
    # tambien la tabla que ya estaba escrita.
    p.add_argument("--tabla", default="ambas",
                   choices=["ambas", "eventos", "pr_eventos"])
    args = p.parse_args()

    if not args.fecha and not (args.desde and args.hasta):
        print("Indica --fecha, o bien --desde y --hasta")
        return 2

    raiz = Path(raiz_datos())
    origen = raiz / "bronze"
    if not origen.exists():
        print(f"No hay bronze en {origen}")
        return 1

    spark = crear_sesion("silver")
    inicio = time.monotonic()

    bronze = spark.read.parquet(str(origen))
    if args.fecha:
        bronze = bronze.filter(F.col("event_date") == args.fecha)
    else:
        bronze = bronze.filter(
            (F.col("event_date") >= args.desde) & (F.col("event_date") <= args.hasta))

    leidas = bronze.count()
    if leidas == 0:
        print("El rango pedido no tiene datos en bronze")
        spark.stop()
        return 1

    # La deduplicacion por id ocurre dentro de cada constructor, ya sobre las
    # columnas proyectadas. En la Fase 0 se vio que los duplicados son copias
    # byte a byte, asi que quedarse con cualquiera es correcto y no hay que
    # decidir cual gana.
    n_eventos = n_pr = None
    if args.tabla in ("ambas", "eventos"):
        n_eventos = escribir(construir_eventos(bronze),
                             raiz / "silver" / "eventos", "eventos")
    if args.tabla in ("ambas", "pr_eventos"):
        n_pr = escribir(construir_pr_eventos(bronze),
                        raiz / "silver" / "pr_eventos", "pr_eventos")

    duracion = time.monotonic() - inicio
    print(f"\nleidas de bronze : {leidas:,}", flush=True)
    if n_eventos is not None:
        print(f"eventos          : {n_eventos:,}")
    if n_pr is not None:
        print(f"pr_eventos       : {n_pr:,}")
    print(f"duracion         : {duracion:.1f}s", flush=True)

    spark.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
