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

### Extrapolación de volumen

**No es una medición.** Se proyecta desde una única hora punta, así que es una
cota alta. Pendiente de confirmar midiendo un día completo en la Fase 1.

| Horizonte | Comprimido | Eventos |
|---|---:|---:|
| 1 día | ~0,51 GiB | ~3,9 M |
| 1 mes | ~15,3 GiB | ~117 M |
| 1 año | ~187 GiB | ~1.422 M |
