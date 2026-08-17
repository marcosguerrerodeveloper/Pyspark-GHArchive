"""Orquesta silver dia a dia, con registro y reanudacion.

Procesar silver de una tacada sobre 361 dias dura horas y, si se corta, se
pierde todo el avance. Aqui cada dia es una unidad independiente: se anota al
terminar, y una reejecucion salta lo ya hecho.

Trocear es correcto **porque la deduplicacion es por (evento_id, event_date)**
(D27). Con la deduplicacion global anterior el resultado dependia del tamano
del lote, que era justamente el error.

Uso:
    python silver_todo.py --desde 2025-08-13 --hasta 2026-08-15
    python silver_todo.py --desde 2025-08-13 --hasta 2026-08-15 --rehacer
"""

import argparse
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "spark_jobs"))

from pyspark.sql import functions as F  # noqa: E402

from silver import construir_eventos, construir_pr_eventos  # noqa: E402
from sesion import crear_sesion, limpiar_staging, raiz_datos  # noqa: E402


def dias(desde: date, hasta: date):
    d = desde
    while d <= hasta:
        yield d.isoformat()
        d += timedelta(days=1)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desde", required=True)
    p.add_argument("--hasta", required=True)
    p.add_argument("--rehacer", action="store_true",
                   help="ignora el registro y reprocesa todo")
    args = p.parse_args()

    raiz = Path(raiz_datos())
    registro = raiz / "silver_registro.jsonl"

    hechos = set()
    if registro.exists() and not args.rehacer:
        for linea in registro.read_text(encoding="utf-8").splitlines():
            try:
                hechos.add(json.loads(linea)["fecha"])
            except Exception:
                pass

    lista = list(dias(date.fromisoformat(args.desde), date.fromisoformat(args.hasta)))
    pendientes = [f for f in lista if f not in hechos]
    print(f"{len(lista)} dias en el rango, {len(hechos)} ya hechos, "
          f"{len(pendientes)} pendientes", flush=True)
    if not pendientes:
        return 0

    spark = crear_sesion("silver-todo")
    bronze_todo = spark.read.parquet(str(raiz / "bronze"))
    inicio = time.monotonic()
    ok = fallos = 0

    for i, fecha in enumerate(pendientes, 1):
        # Bronze no cubre todos los dias del rango: el tramo A empieza el
        # 2025-08-15 y el hueco de D13 no existe. Saltarlos es normal, no un
        # fallo, y no debe contaminar el contador de errores.
        if not (raiz / "bronze" / f"event_date={fecha}").exists():
            print(f"[{i}/{len(pendientes)}] {fecha} sin bronze, se salta",
                  flush=True)
            continue

        try:
            b = bronze_todo.filter(F.col("event_date") == fecha)
            t0 = time.monotonic()

            d_ev = raiz / "silver" / "eventos"
            d_pr = raiz / "silver" / "pr_eventos"
            limpiar_staging(d_ev)
            limpiar_staging(d_pr)

            (construir_eventos(b).write.mode("overwrite")
                .partitionBy("event_date").parquet(str(d_ev)))
            (construir_pr_eventos(b).write.mode("overwrite")
                .partitionBy("event_date").parquet(str(d_pr)))

            # Se cuenta releyendo la particion: confirma que lo escrito es
            # legible, no solo que el write no lanzo excepcion.
            n_ev = spark.read.parquet(str(d_ev / f"event_date={fecha}")).count()
            n_pr = spark.read.parquet(str(d_pr / f"event_date={fecha}")).count()

            m = {"fecha": fecha, "eventos": n_ev, "pr_eventos": n_pr,
                 "segundos": round(time.monotonic() - t0, 1)}
            with registro.open("a", encoding="utf-8") as f:
                f.write(json.dumps(m) + "\n")
            ok += 1

            ritmo = (time.monotonic() - inicio) / ok
            faltan = (len(pendientes) - i) * ritmo
            print(f"[{i}/{len(pendientes)}] {fecha}: "
                  f"eventos={n_ev:,} pr={n_pr:,} {m['segundos']}s "
                  f"| faltan ~{faltan/60:.0f} min", flush=True)

        except Exception as exc:
            fallos += 1
            print(f"[{i}/{len(pendientes)}] {fecha} FALLO: "
                  f"{type(exc).__name__}: {exc}", flush=True)

    spark.stop()
    print(f"\nTerminado en {(time.monotonic()-inicio)/60:.1f} min. "
          f"ok={ok} fallos={fallos}", flush=True)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
