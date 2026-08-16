"""Fase 1 - ingesta idempotente y reanudable de GH Archive.

Descarga un rango de fechas hora a hora. Ejecutarlo dos veces sobre el mismo
rango no vuelve a descargar nada ni corrompe nada: el manifiesto registra lo ya
hecho y el renombrado atomico impide que una interrupcion deje un .gz truncado
que parezca completo.

GH Archive es un servicio gratuito que mantiene una persona. Tope de 6
conexiones y backoff exponencial ante fallos: no se satura.

Uso:
    python ingest/descargar.py --desde 2025-08-13 --hasta 2025-08-13
    python ingest/descargar.py --desde 2024-10-09 --hasta 2025-10-08
"""

import argparse
import asyncio
import hashlib
import json
import os
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

BASE = "https://data.gharchive.org"
CONCURRENCIA_MAX = 6
INTENTOS_MAX = 5


def raiz_datos() -> Path:
    return Path(os.environ.get("GHA_DATA_DIR", "D:/gharchive-data"))


def ruta_manifiesto() -> Path:
    return raiz_datos() / "raw" / "manifiesto.json"


def cargar_manifiesto() -> dict:
    ruta = ruta_manifiesto()
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Un manifiesto corrupto es peor que ninguno: se avisa y se empieza de
        # cero, que como mucho cuesta redescargar.
        print("AVISO: manifiesto ilegible, se reconstruye desde cero")
        return {}


def guardar_manifiesto(manifiesto: dict) -> None:
    ruta = ruta_manifiesto()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # Escritura atomica tambien aqui: si el proceso muere a mitad, el
    # manifiesto anterior sigue siendo valido.
    tmp = ruta.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifiesto, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(ruta)


def horas_del_rango(desde: date, hasta: date):
    """Genera (clave, fecha, hora) para cada hora del rango, ambos inclusive."""
    dia = desde
    while dia <= hasta:
        for hora in range(24):
            # GH Archive nombra la hora SIN cero a la izquierda.
            yield f"{dia.isoformat()}-{hora}", dia.isoformat(), hora
        dia += timedelta(days=1)


async def descargar_una(cliente, semaforo, clave, fecha, hora, manifiesto, lock):
    """Descarga una hora. Devuelve el estado alcanzado."""
    if clave in manifiesto and manifiesto[clave].get("estado") in ("ok", "ausente"):
        return "saltada"

    url = f"{BASE}/{clave}.json.gz"
    carpeta = raiz_datos() / "raw" / fecha
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{clave}.json.gz"
    parcial = destino.with_suffix(".gz.part")

    async with semaforo:
        for intento in range(1, INTENTOS_MAX + 1):
            try:
                inicio = time.monotonic()
                sha = hashlib.sha256()
                tam = 0
                async with cliente.stream("GET", url, timeout=180.0) as r:
                    if r.status_code == 404:
                        # Hora que GH Archive nunca publico. Es un hueco real y
                        # conocido, no un fallo transitorio: no se reintenta.
                        async with lock:
                            manifiesto[clave] = {
                                "estado": "ausente",
                                "comprobado_en": datetime.now(timezone.utc).isoformat(),
                            }
                        print(f"  {clave}: AUSENTE (404)")
                        return "ausente"
                    r.raise_for_status()
                    with parcial.open("wb") as f:
                        async for trozo in r.aiter_bytes(chunk_size=1 << 20):
                            f.write(trozo)
                            sha.update(trozo)
                            tam += len(trozo)

                parcial.replace(destino)
                duracion = time.monotonic() - inicio
                async with lock:
                    manifiesto[clave] = {
                        "estado": "ok",
                        "bytes": tam,
                        "sha256": sha.hexdigest(),
                        "segundos": round(duracion, 2),
                        "descargado_en": datetime.now(timezone.utc).isoformat(),
                    }
                print(f"  {clave}: {tam:,} B en {duracion:.1f}s")
                return "ok"

            except Exception as exc:
                parcial.unlink(missing_ok=True)
                if intento == INTENTOS_MAX:
                    async with lock:
                        manifiesto[clave] = {
                            "estado": "error",
                            "detalle": f"{type(exc).__name__}: {exc}",
                            "intentos": intento,
                        }
                    print(f"  {clave}: ERROR tras {intento} intentos - {exc}")
                    return "error"
                # Backoff exponencial con jitter, para no sincronizar los
                # reintentos de las 6 conexiones contra el mismo servidor.
                espera = 2 ** intento + random.uniform(0, 1)
                print(f"  {clave}: intento {intento} fallo ({type(exc).__name__}), "
                      f"reintento en {espera:.1f}s")
                await asyncio.sleep(espera)
    return "error"


async def ejecutar(desde: date, hasta: date) -> dict:
    manifiesto = cargar_manifiesto()
    pendientes = list(horas_del_rango(desde, hasta))
    print(f"Rango {desde} .. {hasta}: {len(pendientes)} horas")

    semaforo = asyncio.Semaphore(CONCURRENCIA_MAX)
    lock = asyncio.Lock()
    limites = httpx.Limits(max_connections=CONCURRENCIA_MAX,
                           max_keepalive_connections=CONCURRENCIA_MAX)

    inicio = time.monotonic()
    async with httpx.AsyncClient(limits=limites, follow_redirects=True) as cliente:
        tareas = [descargar_una(cliente, semaforo, c, f, h, manifiesto, lock)
                  for c, f, h in pendientes]
        estados = await asyncio.gather(*tareas)
    duracion = time.monotonic() - inicio

    guardar_manifiesto(manifiesto)

    resumen = {e: estados.count(e) for e in set(estados)}
    claves = [c for c, _, _ in pendientes]
    bytes_totales = sum(manifiesto[c].get("bytes", 0) for c in claves
                        if manifiesto.get(c, {}).get("estado") == "ok")

    print(f"\nResumen: {resumen}")
    print(f"Bytes del rango: {bytes_totales:,} ({bytes_totales/1024/1024:.2f} MiB)")
    print(f"Duracion total: {duracion:.1f}s")
    if duracion > 0 and bytes_totales:
        print(f"Velocidad media: {bytes_totales/1024/1024/duracion:.2f} MiB/s")
    return resumen


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--desde", required=True, help="YYYY-MM-DD")
    p.add_argument("--hasta", required=True, help="YYYY-MM-DD")
    args = p.parse_args()

    desde = date.fromisoformat(args.desde)
    hasta = date.fromisoformat(args.hasta)
    if hasta < desde:
        print("El fin del rango es anterior al inicio")
        return 2

    resumen = asyncio.run(ejecutar(desde, hasta))
    # Solo un error de verdad hace fallar el proceso; un 404 es un hueco
    # conocido y no debe romper la ejecucion.
    return 1 if resumen.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())
