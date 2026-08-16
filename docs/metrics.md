# Mediciones

Toda afirmación numérica del proyecto sale de esta tabla. Nada estimado.

---

## Fase −1 — Cimientos

Fecha: 2026-08-16.

### Máquina

| Medida | Valor |
|---|---|
| CPU | AMD Ryzen 7 5800X — 8 núcleos / 16 hilos |
| RAM | 31,9 GB |
| Disco C: libre | 90,5 GB |
| Disco D: libre | 1.378,2 GB |
| Sistema | Windows 11 Pro 10.0.26200 |

### Software instalado

| Componente | Versión | Nota |
|---|---|---|
| Python | 3.10.6 | preexistente |
| JDK | Temurin 17.0.20+8 | **64-Bit Server VM**; sustituye al JRE 1.8 de 32 bits que había |
| PySpark | 3.5.3 | wheel de 317,8 MB |
| dbt-core / dbt-duckdb | 1.9.1 / 1.9.1 | |
| DuckDB | 1.1.3 | |
| httpx | 0.28.1 | preexistente |
| winutils / hadoop.dll | rama hadoop-3.3.6 | 119.296 B y 78.848 B; ver D5 |

`winutils.exe` sha256 `496A591E…FD8553` · `hadoop.dll` sha256 `D7AB36A6…0405BE3`.

### Prueba de humo −1.5

Escritura y relectura de Parquet particionado por fecha, `local[4]`, driver 4 GB.

| Intento | Configuración | Resultado |
|---|---|---|
| 1 | JDK 17, sin `HADOOP_HOME` | **Falla** — `FileNotFoundException: HADOOP_HOME and hadoop.home.dir are unset` en `Shell.getWinUtilsPath` |
| 2 | + winutils y `HADOOP_HOME` | **Falla** — `SparkException: Python worker failed to connect back` / `SocketTimeoutException: Accept timed out` |
| 3 | + `PYSPARK_PYTHON` al intérprete del venv | **OK** |

Salida del intento 3: `filas escritas=1000 releidas=1000 particiones=2`.

Conclusión: la decisión D1 (Windows nativo) se sostiene. No hace falta WSL2.

### Variables de entorno persistidas (ámbito usuario)

    JAVA_HOME   = C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot
    HADOOP_HOME = C:\hadoop

Requieren abrir una terminal nueva para verse. `C:\hadoop\bin` debe estar en el
`PATH` de las sesiones que ejecuten Spark.

---

## Fase 0 — Reconocimiento

Fichero: `2026-08-12-14.json.gz` (miércoles, 14:00–14:59 UTC).
Descargado y analizado en un runner de GitHub Actions (`ubuntu-latest`), porque
la red local no alcanza `data.gharchive.org`; ver D10.

### Fichero

| Medida | Valor |
|---|---|
| Tamaño comprimido | 22.891.223 B (21,83 MiB) |
| Tamaño descomprimido | 111.671.173 B (106,50 MiB) |
| Ratio de compresión | 4,88× |
| Eventos | 162.301 |
| Líneas no parseables | 0 |
| `created_at` mín. / máx. | `14:00:00Z` / `14:59:59Z` |
| `id` duplicados | 1 (`13173052275`, contenido idéntico) |

### Composición

| Medida | Valor |
|---|---:|
| Tipos de evento distintos | 15 |
| `PushEvent` | 148.551 (91,53 %) |
| `PullRequestEvent` | 770 (0,47 %) |
| `PullRequestReviewEvent` | 228 (0,14 %) |
| `IssuesEvent` | 461 (0,28 %) |
| Los 4 tipos de las preguntas de negocio | 1.606 (0,99 %) |
| Eventos de cuentas `[bot]` | 16.547 (10,20 %) |
| Cuentas `[bot]` distintas | 380 |

### Cobertura de campos críticos

| Campo | Cobertura |
|---|---:|
| `payload.pull_request.id` | 100 % (770/770) |
| Lenguaje del repo (4 rutas probadas) | **0 %** |
| Campos temporales del PR | **0 %** |
| `payload.commits` / `size` en `PushEvent` | **0 %** |

### Extrapolación de volumen — ⚠️ SUPERADA

**Obsoleta.** Se conserva por trazabilidad, pero la cifra buena es la medición
de un día completo de la Fase 1: **2,012 GiB/día y ~734 GiB/año**, no los
~940 GiB que se proyectan aquí. La sobreestimación venía de asumir que la hora
punta era representativa; la variación intradía real es de solo 1,35×.

**No es una medición.** Se proyecta desde una única hora punta, así que es una
cota alta.

Hay que proyectar por separado los dos formatos, porque pesan muy distinto: una
hora punta del formato reducido son 21,83 MiB, y del formato completo entre
96 y 122 MiB. La ventana elegida en D11 cae **entera en el formato completo**.

| Horizonte | Formato reducido | Formato completo (~110 MiB/h) |
|---|---:|---:|
| 1 día | ~0,51 GiB | ~2,6 GiB |
| 1 mes | ~15,3 GiB | ~78 GiB |
| 1 año | ~187 GiB | **~940 GiB** |

**Aviso sobre D11.** Con 1.378 GB libres en `D:`, un año de histórico rico en
crudo (~940 GiB en el escenario de hora punta) deja sin sitio a bronze y
silver. El `.gz` se borra en cuanto la hora está en bronze, así que el pico real
es mucho menor que la suma, pero el margen ya no es holgado y depende de que el
borrado vaya al día. Se decide con la medición de un día completo delante:
si no cabe, las salidas son acortar la ventana a seis meses o filtrar tipos de
evento en bronze —donde ahora sí compensa, porque en formato completo el array
de commits de `PushEvent` es lo que más pesa.

### Comparación del esquema entre años

Una hora (14:00–14:59 UTC) de cada año, descargada y analizada en Actions.

| Fecha | Comprimido (MiB) | Eventos | `PullRequestEvent` | `PushEvent` | `[bot]` | Payload |
|---|---:|---:|---:|---:|---:|---|
| 2016-08-17 | 22,20 | 55.106 | 3.580 | 26.490 | 0,00 % | completo |
| 2018-08-15 | 31,27 | 75.426 | 4.878 | 38.065 | 1,12 % | completo |
| 2020-08-12 | 70,51 | 136.958 | 12.487 | 65.011 | 8,51 % | completo |
| 2022-08-17 | 98,26 | 193.991 | 14.390 | 103.021 | 12,47 % | completo |
| 2023-08-16 | 99,47 | 191.032 | 14.197 | 102.666 | 13,68 % | completo |
| 2024-08-14 | 122,55 | 233.812 | 17.235 | 133.065 | 18,09 % | completo |
| 2025-08-13 | 96,48 | 167.303 | 13.181 | 97.403 | 20,30 % | completo |
| 2026-08-12 | 21,83 | 162.301 | 770 | 148.551 | 10,20 % | **reducido** |

Cobertura de `payload.pull_request.base.repo.language` en el tramo completo:
entre **85 % y 92 %**, estable en toda la serie. En el tramo reducido, 0 %.

### Bisección del cambio de formato

Cinco tandas para pasar de un rango de diez años a un día concreto.

| Fecha | Eventos/hora | Payload |
|---|---:|---|
| 2025-09-10 | 168.867 | completo |
| **2025-10-08** | **171.588** | **completo — último observado** |
| 2025-10-09 | 1.346 | reducido |
| 2025-10-10 | 591 | reducido |
| 2025-10-11 | 592 | reducido |
| 2025-10-12 | 595 | reducido |
| 2025-10-13 | 588 | reducido |
| 2025-10-14 | 872 | reducido |
| **2025-10-15** | **141.879** | **reducido — volumen recuperado** |
| 2025-10-16 | 143.988 | reducido |
| 2025-10-17 | 144.571 | reducido |
| 2025-10-18 | 147.168 | reducido |
| 2025-10-19 | 144.785 | reducido |
| 2025-11-12 | 148.543 | reducido |
| 2026-07-08 | 159.060 | reducido |

El cambio de payload ocurre entre el **8 y el 9 de octubre de 2025**, y viene
acompañado de seis días de volumen colapsado (0,4 % de lo esperado) que se
recupera el 15 de octubre.

Resolución del acotamiento: **un día**. Sin bajar a la hora concreta, porque no
cambia ninguna decisión: el tramo entero queda excluido por D13.

---

## Fase 1 — Ingesta

Fecha: 2026-08-16. Ejecutado en `ubuntu-latest` (D10).

### Día completo medido: 2025-08-13 (formato completo)

Sustituye a la extrapolación desde una sola hora punta. **Esto sí es medición.**

| Medida | Valor |
|---|---|
| Horas descargadas | 24 de 24 |
| Horas ausentes (404) | 0 |
| Tamaño del día | 2.160.885.568 B (**2,012 GiB**) |
| Hora más pesada | 104.380.761 B (99,5 MiB) |
| Hora más ligera | 77.055.856 B (73,5 MiB) |
| Media por hora | 90.036.899 B (85,9 MiB) |
| Duración total | 15,2 s con 6 conexiones |
| Suma de tiempos por fichero | 86,8 s |
| Velocidad media | 135,91 MiB/s |

**La variación intradía es mucho menor de lo previsto**: entre la hora más
ligera y la más pesada solo hay un factor de 1,35. La extrapolación anterior
asumía que la hora punta era representativa del pico y que el resto caía mucho
más, y sobreestimaba en un 28 %.

| Proyección | Estimación previa | **Medida** |
|---|---:|---:|
| 1 día | ~2,6 GiB | **2,012 GiB** |
| 1 año | ~940 GiB | **~734 GiB (0,717 TiB)** |

### Verificación de idempotencia

| Pasada | Resumen | Duración |
|---|---|---:|
| Primera | `{'ok': 24}` | 15,2 s |
| Segunda | `{'saltada': 24}` | 0,1 s |

Criterio de aceptación de la fase **cumplido**: la segunda pasada no descarga
nada, no corrompe nada y el manifiesto queda idéntico.

### Advertencia sobre la velocidad

Los 135,91 MiB/s son del ancho de banda de un runner de GitHub, **no de la
máquina del autor**. El tiempo real del backfill depende de la conexión
doméstica y no se ha podido medir por el bloqueo de red (D10). A modo de orden
de magnitud, 734 GiB a 10 MiB/s son unas 21 horas de descarga; a 50 MiB/s, algo
más de 4. No es una cifra del proyecto hasta que se mida.

### Descarga en local con WARP (2026-08-16)

| Medida | Valor |
|---|---|
| Día descargado | 2025-08-13, 24 de 24 horas |
| Bytes | 2.160.885.568 B — **idénticos a los del runner** |
| Duración | 23,2 s con 6 conexiones |
| Velocidad | **88,70 MiB/s** |

La coincidencia byte a byte con la descarga de Actions confirma la integridad.
A esta velocidad, el tiempo de descarga deja de ser una restricción del
proyecto.

---

## Fase 2 — Bronze

Fecha: 2026-08-16. Ryzen 7 5800X, `local[8]`, driver 8 GB.
Día de prueba: 2025-08-13 (formato completo), **3.794.323 eventos**.

### Compresión y proyección: tres configuraciones medidas

| Configuración | Bronze | vs `.gz` | Duración |
|---|---:|---:|---:|
| snappy, JSON de todos los tipos | 3.864.141.412 B (3,599 GiB) | 1,788× | 222,9 s |
| **zstd**, JSON de todos los tipos | 1.850.566.027 B (1,723 GiB) | 0,856× | 135,0 s |
| **zstd + proyección por tipo** | 1.157.963.135 B (**1,078 GiB**) | **0,536×** | **53,3 s** |

Dos hallazgos que no eran obvios:

1. **Con snappy, el Parquet pesa más que el `.gz` de origen** (1,788×). Bronze
   guarda el evento como texto JSON, que es muy redundante, y snappy prioriza
   velocidad sobre ratio. Cambiar a zstd reduce a menos de la mitad **y además
   es más rápido**, porque hay menos bytes que escribir a disco.
2. La proyección por tipo quita otro 37 % y baja la duración a una cuarta parte
   de la configuración inicial.

### Proyección del backfill con estas cifras

| Formato | Bronze por día |
|---|---:|
| Completo (hasta 2025-10-08) | 1,078 GiB |
| Reducido (desde 2025-10-15) | ~0,27 GiB (sin medir, escalado por el tamaño del `.gz`) |

Presupuesto del autor: **250 GB = 232,8 GiB**.

**Silver está sin medir.** La reserva del 15 % que se aplica más abajo es una
provisión, no una medición, y hay que sustituirla en cuanto silver exista.

### Reparto del presupuesto de 250 GB (D19)

| Tramo | Días | Bronze/día | Bronze |
|---|---:|---:|---:|
| A — rico `2025-07-09 → 2025-10-08` | 92 | 1,078 GiB | 99,2 GiB |
| Hueco `2025-10-09 → 10-14` (D13) | 6 | — | 0 |
| B — actual `2025-10-15 → 2026-08-15` | 305 | ~0,27 GiB | ~82,4 GiB |
| **Bronze total** | **397** | | **~181,6 GiB** |
| Provisión de silver (15 %, **sin medir**) | | | ~27,2 GiB |
| **Total** | | | **~208,8 GiB** de 232,8 |

Margen: 10 %. Cobertura temporal: **13 meses**.

El 0,27 GiB/día del tramo B está escalado por el tamaño del `.gz` y **no está
medido**: hay que confirmarlo ejecutando bronze sobre un día del formato nuevo.

### Día del tramo B medido: 2026-08-12 (formato reducido)

| Medida | Valor |
|---|---|
| Descarga | 24 de 24 horas, 530.915.632 B (0,494 GiB), 7,0 s a 72,82 MiB/s |
| Eventos | **3.925.040** |
| Bronze (zstd + proyección) | 99.366.664 B (**0,093 GiB**) |
| Ratio bronze/origen | **0,187×** |
| Duración del job | 15,7 s |

**Tres veces más barato que la estimación** de 0,27 GiB/día. El motivo: en el
formato reducido los `PushEvent` no traen array de commits, y al proyectarlos a
las cinco columnas extraídas queda casi nada. Nótese que tiene **más eventos**
que el día del tramo A (3.925.040 frente a 3.794.323) y ocupa una décima parte.

### Reparto corregido del presupuesto (D19 enmendada)

| Tramo | Días | Bronze/día | Bronze |
|---|---:|---:|---:|
| A — rico `2025-06-01 → 2025-10-08` | 130 | 1,078 GiB (medido) | 140,1 GiB |
| Hueco `2025-10-09 → 10-14` (D13) | 6 | — | 0 |
| B — actual `2025-10-15 → 2026-08-15` | 305 | 0,093 GiB (medido) | 28,4 GiB |
| **Bronze total** | **435** | | **168,5 GiB** |
| Provisión de silver (15 %, sin medir) | | | 25,3 GiB |
| **Total** | | | **193,8 GiB** de 232,8 |

Margen: **17 %**. Cobertura temporal: **14,5 meses**.

El tramo A gana 38 días respecto al reparto anterior gracias a la medición del
tramo B. Silver sigue siendo la única cifra sin medir del cálculo.

---

## Fase 2 — Silver

Fecha: 2026-08-17. Días de prueba: 2025-08-13 (completo) y 2026-08-12 (reducido).

| Medida | Valor |
|---|---|
| Leídas de bronze | 7.719.363 |
| **Duplicados por `id`** | **10** |
| `silver/eventos` | 7.719.353 filas |
| `silver/pr_eventos` | 482.588 filas |
| Duración (2 días) | 100,9 s |

### Tamaño en disco — cierra la última incógnita del presupuesto

| Tabla | Tramo A (2025-08-13) | Tramo B (2026-08-12) |
|---|---:|---:|
| `eventos` | 0,102 GiB | 0,088 GiB |
| `pr_eventos` | 0,022 GiB | 0,001 GiB |
| **Silver total** | **0,124 GiB** | **0,089 GiB** |
| bronze (referencia) | 1,078 GiB | 0,093 GiB |
| silver / bronze | 11,5 % | **96 %** |

El contraste es el esperado: en el tramo A silver es una décima parte de bronze
porque descarta el JSON; en el tramo B bronze ya casi no tiene JSON que
descartar, así que silver pesa casi lo mismo.

**La provisión del 15 % se queda corta.** Silver real son 43,2 GiB para los 435
días, no los 25,3 provisionados.

### Verificación de la detección de esquema (D12)

| Esquema | Filas | `pr_id` | Lenguaje | `pr_abierto_en` | `pr_autor` |
|---|---:|---:|---:|---:|---:|
| completo | 463.458 | 100 % | **91,6 %** | 100 % | 100 % |
| reducido | 19.130 | 100 % | 0 % | 0 % | 0 % |

Cada día cayó en su esquema sin que el código conozca la fecha del cambio.

### `es_merge` unificado entre convenios

| Esquema | Cómo llega el merge | Merges |
|---|---|---:|
| completo | `closed` + `merged=true` | 108.866 |
| reducido | acción `merged` propia | 3.829 |

### Clasificación de actores

| Clase | Eventos | Antes de ampliar listas |
|---|---:|---:|
| humano | 6.268.266 | 6.268.266 |
| bot_ci | 1.093.101 | 1.022.500 |
| bot_dependencias | 202.030 | 202.030 |
| **agente_ia** | **58.614** | 45.293 |
| bot_otro | 97.342 | 181.264 |

Ampliar las listas con lo observado subió `agente_ia` un **29 %** y redujo
`bot_otro` a la mitad. Queda un 1,26 % de eventos en `bot_otro`: es la cola de
cuentas de bajo volumen, y es una limitación conocida del método.

### Tests de calidad

**16 comprobaciones, 16 en verde.**

### Reparto final del presupuesto — todas las cifras medidas

| Concepto | Días | GiB/día | Total |
|---|---:|---:|---:|
| Tramo A bronze | 116 | 1,078 | 125,0 |
| Tramo A silver | 116 | 0,124 | 14,4 |
| Tramo B bronze | 305 | 0,093 | 28,4 |
| Tramo B silver | 305 | 0,089 | 27,1 |
| Crudo transitorio + gold | | | ~7 |
| **Total** | **421** | | **~202 GiB** de 232,8 |

Margen: **13 %**.

---

## Fase 1 bis — El tramo B medido en serie (2026-08-17)

La cifra de 0,093 GiB/día del tramo B salía de **un solo día**, 2026-08-12, y
resultó ser el extremo barato de una serie decreciente. Medido por
`Content-Length` (peticiones HEAD, sin descargar) un día de cada mes:

| Fecha | `.gz` GiB | bronze estimado (×0,52) |
|---|---:|---:|
| 2025-10-15 | 0,824 | 0,429 |
| 2025-11-15 | 0,744 | 0,387 |
| 2025-12-15 | 0,896 | 0,466 |
| 2026-01-15 | 0,855 | 0,445 |
| 2026-02-15 | 0,876 | 0,456 |
| 2026-03-15 | 0,830 | 0,432 |
| 2026-04-15 | 0,737 | 0,383 |
| 2026-05-15 | 0,567 | 0,295 |
| 2026-06-15 | 0,526 | 0,273 |
| 2026-07-15 | 0,484 | 0,252 |
| 2026-08-12 | 0,494 | 0,257 |
| **Media** | **0,712** | **0,370** |

**El tramo B cuesta 113 GiB de bronze, no 28,4.** Casi cuatro veces más. El
volumen de GH Archive cae de forma sostenida desde diciembre de 2025, y tomar
el mes más reciente como representativo subestimaba el resto del año.

Silver del tramo B **no** escala con bronze: depende del número de filas, que se
mantiene en ~3,5 M/día. Se mantiene en ~0,09 GiB/día → 27,5 GiB.

### Reparto final (D19 quater)

| Concepto | Días | GiB/día | Total |
|---|---:|---:|---:|
| Tramo A bronze | 55 | 1,078 | 59,3 |
| Tramo A silver | 55 | 0,124 | 6,8 |
| Tramo B bronze | 305 | 0,370 | 113,0 |
| Tramo B silver | 305 | 0,090 | 27,5 |
| Crudo transitorio + gold | | | ~7 |
| **Total** | **360** | | **~213,6 GiB** de 232,8 |

Margen: **8 %**. Cobertura: **12,5 meses**.

### Prueba del encadenado (10 días sobre el hueco)

| Fecha | Filas | `.gz` GiB | bronze GiB | ratio | s |
|---|---:|---:|---:|---:|---:|
| 2025-10-07 | 3.875.261 | 1,964 | 1,036 | 0,528 | 38,4 |
| 2025-10-08 | 2.769.429 | 1,419 | 0,749 | 0,528 | 29,6 |
| 2025-10-15 | 3.465.925 | 0,824 | 0,429 | 0,521 | 19,8 |
| 2025-10-16 | 3.487.226 | 0,818 | 0,425 | 0,519 | 19,6 |

Los seis días del hueco se saltaron solos. **El 2025-10-08 tiene un 29 % menos
de eventos que el 07**, lo que sugiere que el cambio de formato ocurrió a media
jornada del día 8 y no en la frontera limpia entre el 8 y el 9.

---

## Backfill completo — 2026-08-17

Ejecutado en local con WARP. Encadenado día a día: descarga → bronze → borrado
del crudo.

| Medida | Valor |
|---|---|
| Días procesados | **359** (+1 ya hecho en pruebas = 360) |
| Días fallidos | **0** |
| Días saltados por hueco (D13) | 6 |
| **Eventos** | **1.311.676.396** |
| Bronze en disco | 149,36 GiB |
| Uso total en disco | 153,28 GiB |
| Duración del tramo B | 3,00 h |
| Tiempo de CPU en bronze | 2,34 h (suma por día) |
| Particiones en bronze | 361 |

**El backfill salió más barato de lo proyectado**: 149,36 GiB frente a los
172,2 estimados (55 × 1,078 + 305 × 0,370). La estimación por muestreo mensual
del tramo B sobreestimaba un 13 %, esta vez del lado seguro.

Ninguna partición quedó a medias, no hubo staging huérfano y el crudo se borró
solo, salvo los dos días de pruebas manuales que se ejecutaron sin
`--borrar-crudo` (~3 GiB).
