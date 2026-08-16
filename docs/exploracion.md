# Fase 0 — Reconocimiento: hallazgos y sus implicaciones

Fecha del análisis: 2026-08-16.
Fichero de partida: `2026-08-12-14.json.gz` (miércoles, 14:00–14:59 UTC).

Tablas completas en los anexos, generados por los scripts de `exploracion/`:

- [`exploracion_datos.md`](exploracion_datos.md) — esquema, frecuencias y
  ejemplos crudos de la hora de 2026.
- [`exploracion_historico.md`](exploracion_historico.md) — comparación del
  esquema entre 2016 y 2026.

---

## El hallazgo: GH Archive cambió de formato el 9 de octubre de 2025

La inspección de la hora de 2026 mostró unos payloads mucho más pobres de lo
que documenta la API de eventos de GitHub. `payload.pull_request` traía cinco
claves —`url`, `id`, `number`, `head`, `base`— y el `payload` de `PushEvent`
otras cinco —`repository_id`, `push_id`, `ref`, `head`, `before`—, sin rastro
de `created_at`, `merged_at`, `merged`, `user`, `language`, `commits` ni `size`.

Como eso no estaba documentado en ningún sitio, la duda era si el formato había
sido siempre así o si cambió en algún punto. **Cambió**, y localizarlo por
bisección costó cinco tandas en Actions:

| Periodo | Payload | Eventos/hora | Lenguaje del repo |
|---|---|---:|---|
| 2016 → **2025-10-08** | **completo** | ~55.000 → 171.588 | **~90 %** |
| 2025-10-09 → 2025-10-14 | recortado | **588 – 1.346** | no |
| 2025-10-15 → 2026 | recortado | ~142.000 – 162.000 | no |

Dos cosas ocurrieron a la vez el 9 de octubre de 2025: el payload se redujo, y
el volumen se desplomó durante seis días antes de recuperarse. Tiene toda la
pinta de una migración de la fuente que salió mal y se estabilizó en un formato
nuevo y más pobre.

### El tramo 2025-10-09 → 2025-10-14 es inservible

No está recortado: está **vacío**. 588 eventos en una hora que debería tener
150.000 es un 0,4 % de lo esperado. Esos seis días hay que excluirlos
explícitamente, y no tratarlos como «días con poca actividad», porque
contaminarían cualquier serie temporal y cualquier cohorte que los cruce.

---

## Efecto sobre las tres preguntas de negocio

La conclusión práctica es que **el histórico anterior a octubre de 2025 responde
a las tres preguntas por completo**, y el periodo posterior solo responde a una
parte. Eso convierte la elección de ventana en la decisión central del proyecto.

### Pregunta 1 — actividad de PRs generada por bots · **viable y completa**

En el histórico rico, `payload.pull_request.base.repo.language` está poblado en
torno al **90 %** de forma estable desde 2016. **El corte por lenguaje sí es
posible**, al contrario de lo que parecía al mirar solo 2026.

La detección de bots por sufijo `[bot]` funciona en todo el histórico, y su
evolución es una serie interesante por sí misma:

| Año | Eventos de cuentas `[bot]` |
|---|---:|
| 2016 | 0,00 % |
| 2018 | 1,12 % |
| 2020 | 8,51 % |
| 2022 | 12,47 % |
| 2023 | 13,68 % |
| 2024 | 18,09 % |
| 2025 | 20,30 % |

Y en la muestra de 2026 aparecen agentes de IA identificables por login
—`cursor[bot]`, `devin-ai-integration[bot]`, `chatgpt-codex-connector[bot]`,
`claude[bot]`, `coderabbitai[bot]`—, lo que permite separar automatización
clásica de agentes sin heurísticas frágiles.

**Cuidado al leer esa tabla**: el 10,20 % de la hora de 2026 **no es
comparable** con las cifras anteriores, porque la composición de eventos cambió
con el formato. No es que los bots hayan bajado.

### Pregunta 2 — latencia hasta primer review y hasta merge · **viable**

En el histórico rico están `created_at`, `merged_at` y `closed_at` al 100 %, así
que la latencia se lee directamente.

Aun así conviene **derivarla también de las marcas de tiempo de los eventos**,
uniendo por `payload.pull_request.id`: es la única vía que funciona en ambos
formatos, y mide cuándo GitHub emitió el hecho en lugar de cuándo alguien dice
que ocurrió. Tener las dos permite además contrastarlas, que es un control de
calidad gratis.

Ojo con un detalle que cambia con el formato: hasta 2025-10-08 las acciones
observadas son solo `opened`, `closed` y `reopened`, y el merge se infiere de
`closed` + `merged=true`. Desde el formato nuevo aparece `merged` como acción
propia, junto a `labeled`, `unlabeled` y `assigned`. **El código que interprete
acciones tiene que soportar ambos convenios.**

### Pregunta 3 — retención de contribuyentes por cohortes · **intacta**

Solo necesita `actor.login`, `repo.name` y `created_at`, presentes al 100 % en
todo el rango. Es la pregunta más sólida, y la única que no sufre el cambio.

---

## Otros puntos del entregable

**Duplicados por `id`.** Uno solo en 162.301 eventos (`13173052275`), y las dos
líneas son **byte a byte idénticas**. Deduplicar por `id` es seguro y no hay que
decidir qué versión gana.

**Cobertura temporal.** `created_at` va de `14:00:00Z` a `14:59:59Z`: la hora
está completa y no se desborda. Cero líneas no parseables.

**Truncamiento de commits en `PushEvent`.** En el histórico rico existen
`commits`, `size` y `distinct_size` al 100 %, así que la comprobación de
truncamiento aplica ahí y hay que contar con `size`, nunca con `len(commits)`.
En el formato nuevo la pregunta desaparece: no hay array que truncar.

**Volumen.** El pico está en 2024 (122,55 MiB comprimidos por hora punta) y el
formato nuevo pesa una quinta parte (21,83 MiB). Extrapolando el formato
completo a ~110 MiB por hora, un año ronda los **940 GiB** comprimidos, contra
los 1.378 GB libres de `D:`. El `.gz` se borra en cuanto la hora entra en
bronze, así que el pico real es bastante menor que esa suma, pero **el margen
deja de ser holgado** y depende de que el borrado vaya al día. Es la restricción
que decide la ventana, y hay que medirla sobre un día completo antes de
comprometerse.

---

## Lo que propongo

1. **Ventana histórica: un año que termine el 2025-10-08**, es decir
   `2024-10-09 → 2025-10-08`. Esquema homogéneo, payload completo, lenguaje
   disponible, cohortes de doce meses para retención, y evita de un plumazo
   tanto el tramo degradado como el cambio de formato.
2. **El pipeline soporta los dos esquemas** desde el principio, con el formato
   detectado por presencia de campos y no por fecha. El incremental diario de
   la Fase 5 vivirá en el formato nuevo, así que no es opcional.
3. **El tramo 2025-10-09 → 2025-10-14 se excluye explícitamente**, registrado
   como hueco conocido y propagado como metadato hasta el dashboard.
4. **El dashboard marca visualmente el corte** del 9 de octubre de 2025. Una
   serie que cruce esa fecha sin avisar sería engañosa.
5. **Antes de la Fase 1 hay que medir un día completo** para sustituir la
   extrapolación por una cifra real y cerrar el tamaño del backfill.

Y sigue pendiente el bloqueo de red (D10): el backfill corre en local por
diseño, y esta máquina no alcanza a GH Archive.
