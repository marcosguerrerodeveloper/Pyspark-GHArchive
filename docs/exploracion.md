# Fase 0 — Reconocimiento: hallazgos y sus implicaciones

Fichero inspeccionado: `2026-08-12-14.json.gz` (miércoles, 14:00–14:59 UTC).
Fecha del análisis: 2026-08-16.

Este documento recoge las conclusiones. Las tablas completas —esquema de cada
payload, frecuencias, ejemplos crudos— están en el anexo
[`exploracion_datos.md`](exploracion_datos.md), generado por
`exploracion/analizar_hora.py`.

---

## El hallazgo que cambia el proyecto

**GH Archive sirve los payloads recortados.** No traen ni de lejos lo que
devuelve la API de eventos de GitHub, y esto invalida dos supuestos sobre los
que estaban formuladas las preguntas de negocio.

`payload.pull_request` contiene exactamente cinco claves, en el 100 % de los
770 `PullRequestEvent` del fichero:

    url, id, number, head, base

Y nada más. **No existen** `created_at`, `updated_at`, `closed_at`,
`merged_at`, `merged`, `user`, `additions`, `deletions`, `comments`,
`review_comments` ni `language`.

`payload` de `PushEvent` contiene otras cinco, en los 148.551 eventos:

    repository_id, push_id, ref, head, before

**No existen** `commits` ni `size` ni `distinct_size`.

Verificado dos veces: primero con el analizador, y después leyendo eventos
crudos del `.gz` a mano, porque un resultado así parece antes un fallo del
código que un hecho de los datos. No lo es.

---

## Efecto sobre las tres preguntas de negocio

### Pregunta 1 — actividad de PRs generada por bots · **viable, pero recortada**

La parte de bots se sostiene y bien. De los 162.301 eventos, **16.547 (10,20 %)
los generan cuentas con login terminado en `[bot]`**, repartidos en 380 cuentas
distintas. La cabeza de la distribución:

| Bot | Eventos |
|---|---:|
| `github-actions[bot]` | 12.875 |
| `dependabot[bot]` | 847 |
| `renovate[bot]` | 380 |
| `pull[bot]` | 357 |
| `cursor[bot]` | 265 |

Y hay señal aprovechable para la parte de *agentes*, que era la mitad
interesante de la pregunta: `cursor[bot]`, `devin-ai-integration[bot]`,
`chatgpt-codex-connector[bot]`, `claude[bot]`, `coderabbitai[bot]`,
`arena-ai-coding-agent[bot]`. Son distinguibles por login, así que la
separación entre automatización clásica (CI, dependencias) y agentes de IA es
defendible con los datos, sin heurísticas frágiles.

**Lo que se pierde: el corte por lenguaje del repo.** Se comprobaron cuatro
rutas candidatas y **ninguna existe**, con 0 % de cobertura. El objeto `repo`
solo trae `id`, `name` y `url`. Era el supuesto que `CLAUDE.md` marcaba como
crítico y no dado por bueno; hizo bien en no darlo por bueno.

Salidas posibles, en orden de coste:

1. **Reformular la pregunta sin lenguaje** — evolución de bots por tiempo, tipo
   de bot y tamaño de repo. Coste cero, y sigue respondiendo a lo esencial.
2. **Enriquecer con la API de GitHub** — 5.000 peticiones/hora autenticado, y
   el número de repos distintos es alto. Introduce una dependencia de red y de
   token que choca con «todo corre en Actions gratis».
3. **Derivar un proxy del lenguaje** desde las extensiones de fichero, que no
   están: no hay array de commits. Descartada.

Recomiendo la 1, con la limitación dicha en el README. Es tuya la decisión.

### Pregunta 2 — latencia hasta primer review y hasta merge · **viable por otra vía**

No se puede leer de ningún campo, porque no hay campos temporales. Pero **sí se
puede derivar de los `created_at` de los propios eventos**, uniéndolos por
`payload.pull_request.id`, que está presente al 100 % en `PullRequestEvent`,
`PullRequestReviewEvent` y `PullRequestReviewCommentEvent`.

Y hay una facilidad inesperada: `payload.action` trae **`merged` como valor
propio**, no hay que inferirlo de `closed` + flag.

| Acción | Eventos |
|---|---:|
| `opened` | 265 |
| `merged` | 245 |
| `labeled` | 216 |
| `unlabeled` | 25 |
| `closed` | 10 |
| `assigned` | 8 |
| `reopened` | 1 |

Así que la latencia sale de restar marcas de tiempo entre eventos del mismo
`pull_request.id`. Es más trabajo que leer un campo y en realidad es una
construcción más honesta: mide cuándo GitHub emitió el hecho, no cuándo alguien
dice que ocurrió.

**El precio es que esto amplifica el problema de la censura por los bordes**,
que ya estaba anotado en el plan. Un PR abierto antes del inicio de la ventana
no tiene evento `opened` observable, y su merge aparecerá huérfano. Un PR
abierto al final no tiene aún su merge. Ambos casos hay que excluirlos
explícitamente por cohorte de apertura, no dejarlos entrar y sesgar la media.

### Pregunta 3 — retención de contribuyentes por cohortes · **intacta**

No la afecta el recorte. Necesita `actor.login`, `repo.name` y `created_at`,
los tres presentes al 100 %. Es la pregunta más sólida de las tres.

---

## Otros puntos del entregable

**Duplicados por `id`.** Uno solo en 162.301 eventos: el `id` `13173052275`
aparece dos veces, y las dos líneas son **byte a byte idénticas**. Es un
duplicado exacto, no dos versiones divergentes del mismo evento, así que
deduplicar por `id` es seguro y no hay que decidir cuál gana.

**Cobertura temporal.** `created_at` va de `14:00:00Z` a `14:59:59Z`: el
fichero cubre su hora completa y no se desborda. Cero líneas no parseables.

**Distribución de tipos.** `PushEvent` es el 91,53 % de los eventos, y ahora su
payload es diminuto. Los cuatro tipos que sostienen las preguntas de negocio
(`PullRequestEvent`, `PullRequestReviewEvent`, `IssuesEvent`,
`PullRequestReviewCommentEvent`) suman **1.606 eventos, el 0,99 %**.

---

## Volumen, y qué implica para la ventana histórica

Medido sobre esta hora:

| Medida | Valor |
|---|---|
| Comprimido | 22.891.223 B (21,83 MiB) |
| Descomprimido | 111.671.173 B (106,50 MiB) |
| Ratio | 4,88× |
| Eventos | 162.301 |

Extrapolado a 24 h y a un año — **y esto es una extrapolación, no una
medición**: 14:00 UTC de un miércoles es franja punta (solape Europa/EEUU), así
que estas cifras son una cota alta, probablemente por bastante margen.

| Horizonte | Comprimido | Eventos |
|---|---:|---:|
| 1 día | ~0,51 GiB | ~3,9 M |
| 1 mes | ~15,3 GiB | ~117 M |
| 1 año | ~187 GiB | ~1.422 M |

Con 1.378 GB libres en `D:`, **un año entero cabe con holgura** incluso en el
escenario pesimista, y eso antes de convertir a Parquet, donde el recorte de
payloads juega a favor. La restricción real no será el disco, sino el tiempo de
descarga con el tope de 6 conexiones.

---

## Decisiones que quedan abiertas para el checkpoint

1. **Qué hacemos con la pregunta 1**: reformularla sin lenguaje (recomendado),
   o aceptar la dependencia de la API de GitHub para enriquecer.
2. **Ventana histórica**: ya hay cifras para decidirla. Para cohortes de
   retención con sentido, cuanto más largo mejor; un año parece el punto
   razonable entre señal y tiempo de descarga.
3. **Qué guarda bronze**: con `PushEvent` al 91,53 % de las filas pero con un
   payload de cinco campos, guardarlo todo ya no es caro. Se inclina la balanza
   hacia no filtrar por tipo, contra lo que suponía el plan.
4. **Si una sola hora basta**: este recorte de payloads no estaba documentado
   ni era esperable. Cabe la duda razonable de si el formato cambió en algún
   momento del histórico, y eso rompería el backfill a mitad. Revisar una hora
   de hace uno y tres años cuesta minutos y ahora sale casi gratis, porque el
   workflow de Actions ya está montado y parametrizado por fecha.
