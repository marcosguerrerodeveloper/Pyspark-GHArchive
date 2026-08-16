"""Fase 0 - comparacion del esquema entre horas de distintos anos.

Responde a una sola pregunta: el recorte de payloads que se observo en 2026,
desde cuando existe? Si el esquema cambia a mitad del histórico, el backfill se
rompe por el medio, asi que hay que saberlo antes de elegir la ventana.

Uso:
    python exploracion/comparar_horas.py fichero1.json.gz fichero2.json.gz ...
"""

import gzip
import json
import sys
from collections import Counter
from pathlib import Path

RUTAS_LENGUAJE = [
    "payload.pull_request.base.repo.language",
    "payload.pull_request.head.repo.language",
    "repo.language",
]

# Campos cuya ausencia obligo a replantear las preguntas de negocio.
CAMPOS_PR_CRITICOS = ["created_at", "merged_at", "closed_at", "merged", "user",
                      "id", "number", "head", "base", "title", "additions"]
CAMPOS_PUSH_CRITICOS = ["commits", "size", "distinct_size", "ref", "head", "before"]


def leer_ruta(obj, ruta):
    actual = obj
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return False, None
        actual = actual[parte]
    return True, actual


def analizar(ruta_gz: Path) -> dict:
    total = 0
    bytes_desc = 0
    tipos = Counter()
    pr_claves = Counter()
    push_claves = Counter()
    lenguaje_no_nulo = Counter()
    total_pr = 0
    total_push = 0
    eventos_bot = 0
    con_login = 0
    acciones_pr = Counter()

    with gzip.open(ruta_gz, "rt", encoding="utf-8", errors="replace") as f:
        for linea in f:
            bytes_desc += len(linea.encode("utf-8"))
            try:
                ev = json.loads(linea)
            except json.JSONDecodeError:
                continue
            total += 1
            tipo = ev.get("type")
            tipos[tipo] += 1

            login = (ev.get("actor") or {}).get("login")
            if login:
                con_login += 1
                if login.endswith("[bot]"):
                    eventos_bot += 1

            if tipo == "PullRequestEvent":
                total_pr += 1
                p = ev.get("payload") or {}
                pr = p.get("pull_request") or {}
                pr_claves.update(pr.keys())
                acciones_pr[p.get("action")] += 1
                for r in RUTAS_LENGUAJE:
                    hay, valor = leer_ruta(ev, r)
                    if hay and valor is not None:
                        lenguaje_no_nulo[r] += 1

            elif tipo == "PushEvent":
                total_push += 1
                push_claves.update((ev.get("payload") or {}).keys())

    return {
        "fichero": ruta_gz.name,
        "comprimido": ruta_gz.stat().st_size,
        "descomprimido": bytes_desc,
        "eventos": total,
        "tipos_distintos": len(tipos),
        "total_pr": total_pr,
        "total_push": total_push,
        "pr_claves": pr_claves,
        "push_claves": push_claves,
        "lenguaje": lenguaje_no_nulo,
        "bots": eventos_bot,
        "con_login": con_login,
        "acciones_pr": acciones_pr,
    }


def marca(clave, claves, total):
    """Devuelve la cobertura de una clave, o un guion si no aparece nunca."""
    if total == 0:
        return "—"
    n = claves.get(clave, 0)
    if n == 0:
        return "**no**"
    return f"{100*n/total:.0f}%"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    resultados = [analizar(Path(p)) for p in sys.argv[1:]]
    resultados.sort(key=lambda r: r["fichero"])

    out = []
    a = out.append
    a("# Fase 0 — ¿Cambió el esquema a lo largo del histórico?\n")
    a("Generado por `exploracion/comparar_horas.py`. Cada columna es una hora")
    a("real de un año distinto. Lo que importa no es cada celda, sino en qué")
    a("punto de la tabla cambian.\n")

    cab = " | ".join(r["fichero"].replace(".json.gz", "") for r in resultados)
    sep = "|".join(["---:"] * len(resultados))

    a("\n## Volumen\n")
    a(f"| Medida | {cab} |")
    a(f"|---|{sep}|")
    for etiqueta, clave, fmt in [
        ("Comprimido (MiB)", "comprimido", lambda v: f"{v/1024/1024:.2f}"),
        ("Descomprimido (MiB)", "descomprimido", lambda v: f"{v/1024/1024:.2f}"),
        ("Eventos", "eventos", lambda v: f"{v:,}"),
        ("Tipos distintos", "tipos_distintos", lambda v: f"{v}"),
        ("`PullRequestEvent`", "total_pr", lambda v: f"{v:,}"),
        ("`PushEvent`", "total_push", lambda v: f"{v:,}"),
    ]:
        fila = " | ".join(fmt(r[clave]) for r in resultados)
        a(f"| {etiqueta} | {fila} |")
    fila = " | ".join(
        f"{100*r['bots']/r['con_login']:.2f}%" if r["con_login"] else "—"
        for r in resultados)
    a(f"| Eventos de cuentas `[bot]` | {fila} |")

    a("\n## Claves de `payload.pull_request`\n")
    a(f"| Clave | {cab} |")
    a(f"|---|{sep}|")
    for c in CAMPOS_PR_CRITICOS:
        fila = " | ".join(marca(c, r["pr_claves"], r["total_pr"]) for r in resultados)
        a(f"| `{c}` | {fila} |")

    a("\n## Claves de `payload` en `PushEvent`\n")
    a(f"| Clave | {cab} |")
    a(f"|---|{sep}|")
    for c in CAMPOS_PUSH_CRITICOS:
        fila = " | ".join(marca(c, r["push_claves"], r["total_push"]) for r in resultados)
        a(f"| `{c}` | {fila} |")

    a("\n## Lenguaje del repo\n")
    a(f"| Ruta | {cab} |")
    a(f"|---|{sep}|")
    for r_ in RUTAS_LENGUAJE:
        fila = " | ".join(
            (f"{100*r['lenguaje'].get(r_, 0)/r['total_pr']:.0f}%"
             if r["total_pr"] and r["lenguaje"].get(r_) else "**no**")
            for r in resultados)
        a(f"| `{r_}` | {fila} |")

    a("\n## Acciones de `PullRequestEvent`\n")
    todas = sorted({a_ for r in resultados for a_ in r["acciones_pr"]}, key=str)
    a(f"| Acción | {cab} |")
    a(f"|---|{sep}|")
    for accion in todas:
        fila = " | ".join(f"{r['acciones_pr'].get(accion, 0):,}" for r in resultados)
        a(f"| `{accion}` | {fila} |")

    destino = Path(__file__).resolve().parent.parent / "docs" / "exploracion_historico.md"
    destino.write_text("\n".join(out), encoding="utf-8")
    print(f"Informe escrito en {destino}")
    for r in resultados:
        print(f"  {r['fichero']}: {r['eventos']:,} eventos, "
              f"claves de pull_request = {sorted(r['pr_claves'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
