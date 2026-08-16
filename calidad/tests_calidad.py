"""Fase 2 - tests de calidad sobre silver.

Los cuatro que el plan marca como obligatorios: unicidad de `id`, `created_at`
dentro del rango esperado, cobertura de las 24 horas de cada dia, y tasa de
nulos por columna.

El cuarto no puede exigir cobertura uniforme: en el tramo reducido (D12) hay
columnas nulas por diseno, no por error. Cada comprobacion de nulos se declara
por esquema.

Devuelve 0 si todo pasa, 1 si algo falla. Pensado para bloquear la promocion a
gold, asi que falla ruidosamente y dice por que.

Uso:
    python calidad/tests_calidad.py --desde 2025-08-13 --hasta 2026-08-12
"""

import argparse
import sys
from pathlib import Path

from pyspark.sql import functions as F

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spark_jobs"))
from sesion import crear_sesion, raiz_datos  # noqa: E402

# Columnas que deben venir siempre pobladas, sea cual sea el formato. Un solo
# nulo aqui es un fallo del pipeline.
NO_NULAS_SIEMPRE = ["evento_id", "tipo", "creado_en", "actor", "actor_clase"]

# Columnas que la fuente puede traer vacias en casos aislados. Se observo un
# ForkEvent sin repo.name en el origen: es un dato real de GH Archive, no un
# error de proceso, y exigir cero nulos haria fallar la calidad por un evento
# entre casi ocho millones. Se vigila la tasa, que es lo que pide el plan.
TASA_NULOS_MAXIMA = {"repo": 0.01}  # porcentaje

# Columnas que solo existen en el formato completo. Se exige cobertura alta ahi
# y se acepta que esten vacias en el reducido.
SOLO_ESQUEMA_COMPLETO = {
    "pr_abierto_en": 99.0,
    "pr_autor": 99.0,
    "repo_lenguaje": 80.0,   # ~90% observado; se deja margen
}


class Resultado:
    def __init__(self):
        self.fallos = []
        self.pasados = 0

    def comprobar(self, nombre, condicion, detalle=""):
        if condicion:
            self.pasados += 1
            print(f"  OK    {nombre}")
        else:
            self.fallos.append(f"{nombre}: {detalle}")
            print(f"  FALLO {nombre} -- {detalle}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desde", required=True)
    p.add_argument("--hasta", required=True)
    args = p.parse_args()

    raiz = Path(raiz_datos())
    spark = crear_sesion("calidad")
    r = Resultado()

    eventos = (spark.read.parquet(str(raiz / "silver" / "eventos"))
               .filter((F.col("event_date") >= args.desde)
                       & (F.col("event_date") <= args.hasta)))
    pr = (spark.read.parquet(str(raiz / "silver" / "pr_eventos"))
          .filter((F.col("event_date") >= args.desde)
                  & (F.col("event_date") <= args.hasta)))

    total = eventos.count()
    print(f"\nRango {args.desde} .. {args.hasta}: {total:,} eventos\n")
    if total == 0:
        print("No hay datos en el rango")
        return 1

    print("1. Unicidad de evento_id")
    distintos = eventos.select("evento_id").distinct().count()
    r.comprobar("evento_id sin duplicados", distintos == total,
                f"{total:,} filas pero {distintos:,} ids distintos")

    print("\n2. created_at dentro del rango esperado")
    # Se formatea en Spark y se traen cadenas, no datetime. Traer un timestamp
    # a Python lo convierte a la zona del sistema operativo e ignora
    # session.timeZone, y entonces el test acusa de un desfase horario que solo
    # existe en el propio test.
    limites = eventos.select(
        F.date_format(F.min("creado_en"), "yyyy-MM-dd HH:mm:ss").alias("min"),
        F.date_format(F.max("creado_en"), "yyyy-MM-dd HH:mm:ss").alias("max"),
    ).first()
    r.comprobar("creado_en >= inicio del rango",
                limites["min"][:10] >= args.desde,
                f"minimo observado {limites['min']}")
    r.comprobar("creado_en <= fin del rango",
                limites["max"][:10] <= args.hasta,
                f"maximo observado {limites['max']}")
    # Si el dia no empieza a medianoche, la zona horaria esta mal configurada.
    r.comprobar("el primer instante es medianoche UTC",
                limites["min"][11:] == "00:00:00",
                f"empieza en {limites['min'][11:]}, revisa session.timeZone")

    print("\n3. Cobertura de las 24 horas de cada dia")
    por_hora = (eventos
                .withColumn("hora", F.hour("creado_en"))
                .groupBy("event_date")
                .agg(F.countDistinct("hora").alias("horas"))
                .filter(F.col("horas") < 24)
                .collect())
    r.comprobar("todos los dias tienen 24 horas", len(por_hora) == 0,
                "; ".join(f"{f['event_date']} tiene {f['horas']}" for f in por_hora))

    print("\n4. Nulos en columnas obligatorias")
    for col in NO_NULAS_SIEMPRE:
        nulos = eventos.filter(F.col(col).isNull()).count()
        r.comprobar(f"{col} sin nulos", nulos == 0, f"{nulos:,} nulos")

    print("\n4b. Tasa de nulos en columnas tolerantes")
    for col, maximo in TASA_NULOS_MAXIMA.items():
        nulos = eventos.filter(F.col(col).isNull()).count()
        pct = 100.0 * nulos / total
        r.comprobar(f"{col} con nulos <= {maximo}%", pct <= maximo,
                    f"{nulos:,} nulos ({pct:.4f}%)")

    print("\n5. Nulos en columnas del formato completo")
    completo = pr.filter(F.col("esquema") == "completo")
    n_completo = completo.count()
    if n_completo == 0:
        print("  (no hay filas de esquema completo en el rango, se omite)")
    else:
        for col, minimo in SOLO_ESQUEMA_COMPLETO.items():
            pct = 100.0 * completo.filter(F.col(col).isNotNull()).count() / n_completo
            r.comprobar(f"{col} cubierto >= {minimo}%", pct >= minimo,
                        f"cobertura real {pct:.1f}%")

    print("\n6. Coherencia entre esquemas")
    # pr_id es la clave que une eventos de un mismo PR: sin ella no hay
    # pregunta 2, y tiene que estar en los dos formatos.
    sin_pr_id = pr.filter(F.col("pr_id").isNull()).count()
    r.comprobar("pr_id sin nulos en ningun esquema", sin_pr_id == 0,
                f"{sin_pr_id:,} nulos")
    # es_merge nunca puede quedar en un tercer estado.
    r.comprobar("es_merge sin nulos",
                pr.filter(F.col("es_merge").isNull()).count() == 0,
                "hay es_merge nulos: revisa el coalesce")

    print(f"\n{r.pasados} comprobaciones pasadas, {len(r.fallos)} fallidas")
    spark.stop()
    if r.fallos:
        print("\nFALLOS:")
        for f in r.fallos:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
