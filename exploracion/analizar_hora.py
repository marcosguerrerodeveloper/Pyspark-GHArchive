"""Fase 0 - inspeccion de un fichero horario de GH Archive.

No escribe pipeline ni define esquemas: solo observa y reporta lo que hay,
para que el esquema de la Fase 2 se disene sobre datos vistos y no sobre
suposiciones.

Cubre los nueve puntos del entregable de la Fase 0 y vuelca el resultado en
docs/exploracion.md.

Uso:
    .venv\\Scripts\\python.exe exploracion\\analizar_hora.py D:\\gharchive-data\\raw\\exploracion\\2026-08-12-14.json.gz
"""

import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Tipos cuyo payload hay que volcar entero, segun el entregable de la Fase 0.
TIPOS_DETALLE = [
    "PullRequestEvent",
    "PullRequestReviewEvent",
    "IssuesEvent",
    "PushEvent",
]

# Punto 4: rutas donde el lenguaje del repo PODRIA estar. No se da ninguna por
# buena; el script mide la cobertura real de cada una y el informe reporta
# cual existe de verdad.
RUTAS_LENGUAJE_CANDIDATAS = [
    "payload.pull_request.base.repo.language",
    "payload.pull_request.head.repo.language",
    "repo.language",
    "payload.repository.language",
]

MAX_PROFUNDIDAD = 8


def tipo_json(valor) -> str:
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "bool"
    if isinstance(valor, int):
        return "int"
    if isinstance(valor, float):
        return "float"
    if isinstance(valor, str):
        return "str"
    if isinstance(valor, list):
        return "list"
    if isinstance(valor, dict):
        return "dict"
    return type(valor).__name__


def recorrer(obj, prefijo, acumulador, profundidad=0):
    """Acumula rutas observadas -> Counter de tipos.

    De las listas solo se inspecciona el primer elemento: basta para conocer la
    forma y evita recorrer arrays de miles de commits.
    """
    if profundidad > MAX_PROFUNDIDAD:
        return
    if isinstance(obj, dict):
        for clave, valor in obj.items():
            ruta = f"{prefijo}.{clave}" if prefijo else clave
            acumulador[ruta][tipo_json(valor)] += 1
            recorrer(valor, ruta, acumulador, profundidad + 1)
    elif isinstance(obj, list) and obj:
        ruta = f"{prefijo}[]"
        acumulador[ruta][tipo_json(obj[0])] += 1
        recorrer(obj[0], ruta, acumulador, profundidad + 1)


def leer_ruta(obj, ruta):
    """Devuelve (encontrada, valor) siguiendo una ruta con puntos."""
    actual = obj
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return False, None
        actual = actual[parte]
    return True, actual


def bloque_json(obj, limite=6000) -> str:
    texto = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True)
    if len(texto) > limite:
        texto = texto[:limite] + "\n... (truncado en el informe)"
    return texto


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ruta_gz = Path(sys.argv[1])
    if not ruta_gz.exists():
        print(f"No existe: {ruta_gz}")
        return 1

    tam_comprimido = ruta_gz.stat().st_size

    total = 0
    bytes_descomprimidos = 0
    lineas_invalidas = 0
    tipos = Counter()
    ids = Counter()
    ids_contenido = defaultdict(set)          # punto 5: duplicado identico o divergente
    esquemas = {t: defaultdict(Counter) for t in TIPOS_DETALLE}
    ejemplos = {}
    fechas = []

    # Punto 4
    lenguaje_visto = Counter()
    lenguaje_no_nulo = Counter()
    lenguaje_valores = Counter()
    total_pr = 0

    # Punto 6
    push_total = 0
    push_truncados = 0
    push_tam_max_visto = 0
    push_ejemplo_truncado = None
    push_claves = Counter()          # que trae de verdad el payload de PushEvent

    # Claves realmente presentes en payload.pull_request. Se mide en vez de
    # suponerse: el payload de GH Archive puede venir recortado.
    pr_claves = Counter()
    pr_acciones = Counter()

    # Punto 7
    actores_bot_sufijo = Counter()
    total_actores = 0
    tipos_usuario = Counter()

    # Punto 8
    campos_temporales = defaultdict(Counter)  # accion -> campo poblado

    # Punto 9
    identificadores_pr = defaultdict(Counter)  # tipo de evento -> ruta id disponible

    with gzip.open(ruta_gz, "rt", encoding="utf-8") as f:
        for linea in f:
            bytes_descomprimidos += len(linea.encode("utf-8"))
            linea = linea.strip()
            if not linea:
                continue
            try:
                ev = json.loads(linea)
            except json.JSONDecodeError:
                lineas_invalidas += 1
                continue

            total += 1
            tipo = ev.get("type", "(sin type)")
            tipos[tipo] += 1

            ident = ev.get("id")
            if ident is not None:
                ids[ident] += 1
                if ids[ident] > 1:
                    ids_contenido[ident].add(hash(linea))

            if ev.get("created_at"):
                fechas.append(ev["created_at"])

            # Punto 7: senales de bot
            actor = ev.get("actor") or {}
            login = actor.get("login")
            if login:
                total_actores += 1
                if login.endswith("[bot]"):
                    actores_bot_sufijo[login] += 1
            for ruta_tipo in ("payload.pull_request.user.type", "payload.issue.user.type",
                              "payload.sender.type", "actor.type"):
                hay, valor = leer_ruta(ev, ruta_tipo)
                if hay and valor is not None:
                    tipos_usuario[f"{ruta_tipo}={valor}"] += 1

            if tipo in esquemas:
                recorrer(ev.get("payload"), "payload", esquemas[tipo])
                if tipo not in ejemplos:
                    ejemplos[tipo] = ev

            if tipo == "PullRequestEvent":
                total_pr += 1
                pr = (ev.get("payload") or {}).get("pull_request") or {}
                pr_claves.update(pr.keys())
                pr_acciones[(ev.get("payload") or {}).get("action")] += 1
                for ruta in RUTAS_LENGUAJE_CANDIDATAS:
                    hay, valor = leer_ruta(ev, ruta)
                    if hay:
                        lenguaje_visto[ruta] += 1
                        if valor is not None:
                            lenguaje_no_nulo[ruta] += 1
                            if ruta == RUTAS_LENGUAJE_CANDIDATAS[0]:
                                lenguaje_valores[valor] += 1

                # Punto 8: que campos temporales trae cada accion
                accion = (ev.get("payload") or {}).get("action", "(sin action)")
                for campo in ("created_at", "updated_at", "closed_at", "merged_at", "merged"):
                    hay, valor = leer_ruta(ev, f"payload.pull_request.{campo}")
                    if hay and valor is not None:
                        campos_temporales[accion][campo] += 1
                campos_temporales[accion]["(total eventos)"] += 1

            # Punto 9: identificador que permite unir eventos de un mismo PR
            if tipo in ("PullRequestEvent", "PullRequestReviewEvent",
                        "PullRequestReviewCommentEvent"):
                for ruta in ("payload.pull_request.id", "payload.pull_request.number",
                             "payload.pull_request.node_id", "payload.number"):
                    hay, valor = leer_ruta(ev, ruta)
                    if hay and valor is not None:
                        identificadores_pr[tipo][ruta] += 1

            # Punto 6: truncamiento de commits
            if tipo == "PushEvent":
                push_total += 1
                p = ev.get("payload") or {}
                push_claves.update(p.keys())
                commits = p.get("commits") or []
                tam = p.get("size")
                push_tam_max_visto = max(push_tam_max_visto, len(commits))
                if isinstance(tam, int) and tam > len(commits):
                    push_truncados += 1
                    if push_ejemplo_truncado is None:
                        push_ejemplo_truncado = {
                            "size": tam,
                            "distinct_size": p.get("distinct_size"),
                            "len(commits)": len(commits),
                        }

    duplicados = {i: c for i, c in ids.items() if c > 1}
    ratio = bytes_descomprimidos / tam_comprimido if tam_comprimido else 0

    # ------------------------------------------------------------------ informe
    out = []
    a = out.append
    a("# Fase 0 — Exploración de un fichero horario de GH Archive\n")
    a(f"Fichero inspeccionado: `{ruta_gz.name}`\n")
    a("Generado por `exploracion/analizar_hora.py`. Todo lo que sigue está")
    a("observado en los datos, no inferido de la documentación.\n")

    a("\n## 1. Volumen\n")
    a("| Medida | Valor |")
    a("|---|---|")
    a(f"| Tamaño comprimido | {tam_comprimido:,} bytes ({tam_comprimido/1024/1024:.2f} MiB) |")
    a(f"| Tamaño descomprimido | {bytes_descomprimidos:,} bytes ({bytes_descomprimidos/1024/1024:.2f} MiB) |")
    a(f"| Ratio de compresión | {ratio:.2f}× |")
    a(f"| Eventos | {total:,} |")
    a(f"| Líneas no parseables | {lineas_invalidas:,} |")
    if fechas:
        a(f"| `created_at` mínimo | {min(fechas)} |")
        a(f"| `created_at` máximo | {max(fechas)} |")

    a("\n## 2. Tipos de evento\n")
    a("| Tipo | Eventos | % |")
    a("|---|---:|---:|")
    for t, c in tipos.most_common():
        a(f"| `{t}` | {c:,} | {100*c/total:.2f}% |")

    a("\n## 5. Duplicados por `id`\n")
    if not duplicados:
        a(f"No hay duplicados: {len(ids):,} `id` distintos para {total:,} eventos.\n")
    else:
        a(f"**{len(duplicados):,} `id` aparecen más de una vez** "
          f"({sum(duplicados.values()):,} eventos implicados).\n")
        a("| `id` | Repeticiones | ¿Contenido idéntico? |")
        a("|---|---:|---|")
        for i, c in list(duplicados.items())[:20]:
            identico = "sí" if len(ids_contenido[i]) <= 1 else "**no, difieren**"
            a(f"| `{i}` | {c} | {identico} |")

    a("\n## 6. Truncamiento de commits en `PushEvent`\n")
    a(f"`PushEvent` analizados: **{push_total:,}**\n")
    a("Claves realmente presentes en `payload`:\n")
    a("| Clave | Ocurrencias | Cobertura |")
    a("|---|---:|---:|")
    for k, c in push_claves.most_common():
        a(f"| `{k}` | {c:,} | {100*c/push_total:.2f}% |")

    hay_commits = "commits" in push_claves
    hay_size = "size" in push_claves
    a("")
    if not hay_commits and not hay_size:
        a("**Ni `commits` ni `size` existen en el payload.** La pregunta del")
        a("truncamiento queda respondida por la vía inesperada: no hay array de")
        a("commits que truncar. `PushEvent` aporta el hecho del push (quién, a qué")
        a("repo, a qué rama, cuándo) y los SHA `head`/`before`, pero no el detalle")
        a("de los commits ni su número.")
    else:
        a(f"- Con `payload.size` > `len(payload.commits)` (truncados): **{push_truncados:,}**"
          + (f" ({100*push_truncados/push_total:.2f}%)" if push_total else ""))
        a(f"- Máximo `len(commits)` observado: **{push_tam_max_visto}**")
        if push_ejemplo_truncado:
            a(f"- Ejemplo real: `{push_ejemplo_truncado}`")
        a("")
        a("Si el máximo observado se apelmaza en un número redondo, ese es el tope")
        a("que aplica GH Archive y hay que contarlo con `size`, nunca con `len(commits)`.")

    a("\n## 4. ¿Está el lenguaje del repo en `PullRequestEvent`?\n")
    a("**Es el supuesto crítico de la pregunta de negocio 1.**\n")
    a(f"`PullRequestEvent` analizados: {total_pr:,}\n")
    a("Antes de buscar el lenguaje, qué trae de verdad `payload.pull_request`:\n")
    a("| Clave | Ocurrencias | Cobertura |")
    a("|---|---:|---:|")
    for k, c in pr_claves.most_common():
        a(f"| `{k}` | {c:,} | {100*c/total_pr:.2f}% |" if total_pr else f"| `{k}` | {c:,} | — |")
    a("")
    a("| Ruta candidata | Existe la clave | No nula | Cobertura |")
    a("|---|---:|---:|---:|")
    for ruta in RUTAS_LENGUAJE_CANDIDATAS:
        vistos = lenguaje_visto[ruta]
        no_nulos = lenguaje_no_nulo[ruta]
        cob = f"{100*no_nulos/total_pr:.2f}%" if total_pr else "—"
        a(f"| `{ruta}` | {vistos:,} | {no_nulos:,} | {cob} |")
    if lenguaje_valores:
        a(f"\nValores más frecuentes en `{RUTAS_LENGUAJE_CANDIDATAS[0]}`:\n")
        a("| Lenguaje | PRs |")
        a("|---|---:|")
        for lang, c in lenguaje_valores.most_common(15):
            a(f"| {lang} | {c:,} |")

    a("\n## 7. Señales de bot disponibles\n")
    a(f"- Actores con login: **{total_actores:,}**")
    a(f"- Logins terminados en `[bot]`: **{sum(actores_bot_sufijo.values()):,}** "
      f"de **{len(actores_bot_sufijo):,}** cuentas distintas"
      + (f" ({100*sum(actores_bot_sufijo.values())/total_actores:.2f}% de los eventos)"
         if total_actores else ""))
    if actores_bot_sufijo:
        a("\n| Bot | Eventos |")
        a("|---|---:|")
        for login, c in actores_bot_sufijo.most_common(20):
            a(f"| `{login}` | {c:,} |")
    a("\nCampos de tipo de usuario observados:\n")
    if tipos_usuario:
        a("| Ruta y valor | Ocurrencias |")
        a("|---|---:|")
        for k, c in tipos_usuario.most_common(20):
            a(f"| `{k}` | {c:,} |")
    else:
        a("Ninguno de los candidatos aparece poblado.")

    a("\n## 8. Campos temporales del PR por acción\n")
    a("Sin esto no hay pregunta de negocio 2 (latencia hasta review y hasta merge).\n")
    a("Acciones observadas en `PullRequestEvent`:\n")
    a("| Acción | Eventos |")
    a("|---|---:|")
    for accion, c in pr_acciones.most_common():
        a(f"| `{accion}` | {c:,} |")
    temporales_presentes = [c for c in ("created_at", "updated_at", "closed_at",
                                        "merged_at", "merged") if c in pr_claves]
    a("")
    if not temporales_presentes:
        a("**Ningún campo temporal del PR está presente en el payload.** La latencia")
        a("no se puede leer: hay que derivarla del `created_at` de los propios")
        a("eventos, uniéndolos por `payload.pull_request.id`.")
    a("")
    if campos_temporales:
        campos = ["(total eventos)", "created_at", "updated_at", "closed_at", "merged_at", "merged"]
        a("| Acción | " + " | ".join(f"`{c}`" for c in campos[1:]) + " | Total |")
        a("|---|" + "---:|" * len(campos))
        for accion, cuenta in sorted(campos_temporales.items()):
            fila = " | ".join(f"{cuenta.get(c, 0):,}" for c in campos[1:])
            a(f"| `{accion}` | {fila} | {cuenta.get('(total eventos)', 0):,} |")

    a("\n## 9. Identificador estable de PR entre eventos\n")
    a("Determina con qué clave se unen `PullRequestEvent` y `PullRequestReviewEvent`.\n")
    if identificadores_pr:
        a("| Tipo de evento | Ruta | Presente |")
        a("|---|---|---:|")
        for tipo_ev, rutas in sorted(identificadores_pr.items()):
            for ruta, c in rutas.most_common():
                a(f"| `{tipo_ev}` | `{ruta}` | {c:,} |")

    a("\n## 3. Esquema observado del `payload`\n")
    for tipo in TIPOS_DETALLE:
        acumulador = esquemas[tipo]
        a(f"\n### `{tipo}`  ({tipos.get(tipo, 0):,} eventos)\n")
        if not acumulador:
            a("No aparece en este fichero.\n")
            continue
        a("| Ruta | Tipos observados | Ocurrencias |")
        a("|---|---|---:|")
        for ruta in sorted(acumulador):
            conteo = acumulador[ruta]
            tipos_txt = ", ".join(f"`{t}`×{n:,}" for t, n in conteo.most_common())
            a(f"| `{ruta}` | {tipos_txt} | {sum(conteo.values()):,} |")
        if tipo in ejemplos:
            a(f"\n<details><summary>Ejemplo real de <code>{tipo}</code></summary>\n")
            a("```json")
            a(bloque_json(ejemplos[tipo]))
            a("```\n")
            a("</details>\n")

    # Anexo de hallazgos crudos. Las conclusiones y sus implicaciones se
    # escriben a mano en docs/exploracion.md, que es el entregable de la fase.
    destino = Path(__file__).resolve().parent.parent / "docs" / "exploracion_datos.md"
    destino.write_text("\n".join(out), encoding="utf-8")
    print(f"Informe escrito en {destino}")
    print(f"Eventos: {total:,} | tipos: {len(tipos)} | duplicados: {len(duplicados)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
