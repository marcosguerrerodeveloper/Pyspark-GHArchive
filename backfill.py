"""Backfill: encadena descarga, bronze y borrado del crudo, dia a dia.

Por que dia a dia y no en dos fases: descargar los 421 dias de la ventana antes
de procesar nada son ~412 GiB de .gz, muy por encima del presupuesto de 250 GB
(D16). Encadenando, el crudo nunca acumula mas de un dia y lo que crece es solo
bronze.

Es reanudable: los dias ya escritos en bronze se saltan, asi que se puede parar
con Ctrl+C y volver a lanzarlo.

Lleva un freno de presupuesto. Si el uso de disco supera el limite, para y lo
dice, en vez de llenar el disco a las cuatro horas de haberlo dejado solo.

Uso:
    python backfill.py --desde 2025-06-15 --hasta 2025-10-08
    python backfill.py --desde 2025-10-15 --hasta 2026-08-15
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "ingest"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "spark_jobs"))

from bronze import TIPOS_JSON_COMPLETO, procesar_dia  # noqa: E402
from descargar import ejecutar as descargar_rango  # noqa: E402
from sesion import crear_sesion, raiz_datos, tam_directorio  # noqa: E402

# Tope duro. Por debajo del presupuesto de 250 GB (232,8 GiB) para dejar sitio
# a gold y al crudo transitorio.
LIMITE_GIB = 215.0

# D13: GH Archive sirvio estos dias practicamente vacios, entre 588 y 1.346
# eventos por hora frente a los ~150.000 esperados. No son dias flojos, son
# datos ausentes, y contaminarian cualquier serie temporal.
HUECOS = {f"2025-10-{d:02d}" for d in range(9, 15)}


def dias(desde: date, hasta: date):
    d = desde
    while d <= hasta:
        yield d.isoformat()
        d += timedelta(days=1)


def uso_gib(raiz: Path) -> float:
    return tam_directorio(raiz) / 1024 ** 3


def ya_en_bronze(raiz: Path, fecha: str) -> bool:
    particion = raiz / "bronze" / f"event_date={fecha}"
    if not particion.exists():
        return False
    # _SUCCESS lo escribe Spark al terminar bien; sin el, la particion quedo a
    # medias y hay que rehacerla.
    return any(particion.glob("*.parquet"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desde", required=True)
    p.add_argument("--hasta", required=True)
    p.add_argument("--limite-gib", type=float, default=LIMITE_GIB)
    args = p.parse_args()

    raiz = Path(raiz_datos())
    registro = raiz / "backfill_registro.jsonl"
    lista = [f for f in dias(date.fromisoformat(args.desde),
                             date.fromisoformat(args.hasta))]

    print(f"Backfill {args.desde} .. {args.hasta}: {len(lista)} dias")
    print(f"Limite de disco: {args.limite_gib:.1f} GiB "
          f"(uso actual {uso_gib(raiz):.2f} GiB)\n")

    spark = crear_sesion("backfill")
    inicio_global = time.monotonic()
    hechos = saltados = fallidos = 0

    for i, fecha in enumerate(lista, 1):
        if fecha in HUECOS:
            print(f"[{i}/{len(lista)}] {fecha} HUECO CONOCIDO (D13), se salta")
            saltados += 1
            continue

        if ya_en_bronze(raiz, fecha):
            print(f"[{i}/{len(lista)}] {fecha} ya en bronze, se salta")
            saltados += 1
            continue

        usado = uso_gib(raiz)
        if usado >= args.limite_gib:
            print(f"\nFRENO: el uso de disco ({usado:.2f} GiB) alcanza el "
                  f"limite de {args.limite_gib:.1f} GiB. Se para aqui.")
            print(f"Retomar con: --desde {fecha} --hasta {args.hasta}")
            break

        try:
            d = date.fromisoformat(fecha)
            asyncio.run(descargar_rango(d, d))
            m = procesar_dia(spark, fecha, TIPOS_JSON_COMPLETO, borrar_crudo=True)
            hechos += 1

            with registro.open("a", encoding="utf-8") as f:
                f.write(json.dumps(m) + "\n")

            transcurrido = time.monotonic() - inicio_global
            ritmo = transcurrido / hechos
            faltan = (len(lista) - i) * ritmo
            print(f"[{i}/{len(lista)}] {fecha}: {m['filas']:,} filas, "
                  f"{m['bytes_bronze']/1024**3:.3f} GiB, {m['segundos']}s "
                  f"| disco {uso_gib(raiz):.1f} GiB "
                  f"| faltan ~{faltan/3600:.1f}h")

        except Exception as exc:
            fallidos += 1
            print(f"[{i}/{len(lista)}] {fecha} FALLO: {type(exc).__name__}: {exc}")
            # Se continua: un dia roto no debe tumbar un backfill de horas. El
            # dia queda sin bronze y una reejecucion lo reintenta.

    total = time.monotonic() - inicio_global
    spark.stop()
    print(f"\n=== Backfill terminado en {total/3600:.2f}h ===")
    print(f"procesados: {hechos} | saltados: {saltados} | fallidos: {fallidos}")
    print(f"uso de disco: {uso_gib(raiz):.2f} GiB")
    return 1 if fallidos else 0


if __name__ == "__main__":
    sys.exit(main())
