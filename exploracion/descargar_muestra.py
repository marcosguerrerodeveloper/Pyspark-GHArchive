"""Fase 0 - descarga de un unico fichero horario de GH Archive.

No es codigo de pipeline: solo trae una muestra para poder inspeccionarla.
La descarga real, idempotente y reanudable, es la Fase 1.

Uso:
    .venv\\Scripts\\python.exe exploracion\\descargar_muestra.py 2026-08-12 14
"""

import os
import sys
import time
from pathlib import Path

import httpx

BASE = "https://data.gharchive.org"


def destino_base() -> Path:
    return Path(os.environ.get("GHA_DATA_DIR", "D:/gharchive-data"))


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    fecha, hora = sys.argv[1], int(sys.argv[2])

    # GH Archive nombra la hora SIN cero a la izquierda: .../2026-08-12-14.json.gz
    # y .../2026-08-12-3.json.gz. Detalle que la Fase 1 debe respetar.
    nombre = f"{fecha}-{hora}.json.gz"
    url = f"{BASE}/{nombre}"

    carpeta = destino_base() / "raw" / "exploracion"
    carpeta.mkdir(parents=True, exist_ok=True)
    salida = carpeta / nombre
    parcial = salida.with_suffix(salida.suffix + ".part")

    if salida.exists():
        print(f"Ya existe: {salida} ({salida.stat().st_size:,} bytes). No se redescarga.")
        return 0

    print(f"GET {url}")
    inicio = time.monotonic()
    with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as r:
        print("HTTP", r.status_code, "| content-type:", r.headers.get("content-type"))
        r.raise_for_status()
        with parcial.open("wb") as f:
            for trozo in r.iter_bytes(chunk_size=1 << 20):
                f.write(trozo)

    # Renombrado atomico: una interrupcion no deja un .gz truncado que parezca bueno.
    parcial.replace(salida)
    duracion = time.monotonic() - inicio
    tam = salida.stat().st_size

    print(f"Guardado en {salida}")
    print(f"Tamano comprimido: {tam:,} bytes ({tam / 1024 / 1024:.2f} MiB)")
    print(f"Duracion: {duracion:.1f} s ({tam / 1024 / 1024 / duracion:.2f} MiB/s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
