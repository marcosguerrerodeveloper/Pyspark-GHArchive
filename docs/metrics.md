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
