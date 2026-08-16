# Sesión 1 — 2026-08-16

Del repositorio vacío a bronze funcionando. Fases −1, 0 y 1 cerradas, Fase 2 a
medias.

## Qué se hizo

**Fase −1 · Cimientos.** `git init`, repo público, estructura y entorno. El
equipo tenía un **JRE 1.8 de 32 bits**, inservible para Spark (topa en ~1,5 GB
de heap y además no es un JDK); sustituido por Temurin 17 x64.

**Fase 0 · Reconocimiento.** Descarga e inspección de una hora real. El hallazgo
grande: **GH Archive cambió de formato el 2025-10-09** y desde entonces sirve
los payloads recortados. Acotado por bisección en cinco tandas sobre Actions, de
un rango de diez años a un día.

**Fase 1 · Ingesta.** `ingest/descargar.py`, idempotente y reanudable, validada
sobre un día real: primera pasada `{'ok': 24}`, segunda `{'saltada': 24}`.

**Fase 2 · Bronze.** `spark_jobs/bronze.py` funcionando y medido en tres
configuraciones. Silver aún no existe.

## Decisiones tomadas

D1–D20 en `decisions.md`. Las que más condicionan lo que viene:

- **D19 + D19 bis · La ventana**, en dos tramos a un lado y otro del cambio de
  formato: **A rico** `2025-06-01 → 2025-10-08` (130 días) y **B actual**
  `2025-10-15 → ayer` (~305 días), con el hueco de D13 en medio. 14,5 meses de
  cobertura. El criterio fue que el dashboard **termine en el presente**: uno
  cuyo último dato es de octubre de 2025 se lee como proyecto abandonado.
- **D16 · Presupuesto de 250 GB**, fijado por el autor. Revocó D11 y D15.
- **D17 · zstd** en lugar de snappy, y **D18 · proyección del JSON por tipo**.
- **D7 revocada**: el lenguaje del repo **sí** existe en el histórico rico.

## Errores cometidos, y cómo se resolvieron

1. **Di por bueno que el payload recortado era el de siempre.** Lo era solo en
   2026. Al comparar contra otros años apareció completo desde 2016, con el
   lenguaje al ~90 %. → Corregido revocando D7. **Lección: una sola muestra no
   describe una serie temporal.**
2. **Extrapolé el volumen desde una hora punta** y salió ~940 GiB/año. Medido de
   verdad son ~734 GiB: sobreestimaba un 28 %, porque la variación intradía es
   de solo 1,35×, no la que supuse. → Sustituido por la medición, dejando la
   cifra vieja marcada como superada.
3. **Estimé el coste del tramo B escalando por el tamaño del `.gz`** y salió tres
   veces más caro de lo real (0,27 vs 0,093 GiB/día). → Medido, y los ~54 GiB
   liberados se reinvirtieron en ampliar el tramo A de 92 a 130 días.
4. **Snappy hacía que el Parquet pesara más que el `.gz`** de origen (1,788×).
   → zstd lo deja en 0,856× y encima tarda menos.
5. **Un job fallido dejó 2,912 GiB de `.spark-staging` huérfano**, más que la
   partición buena. Habría reventado el presupuesto en silencio a lo largo del
   backfill. → `limpiar_staging()` en el arranque del job (D20).

El patrón que se repite en 1, 2 y 3: **estimar en lugar de medir**. La regla 4
del proyecto existe por algo.

## Estado del entorno

    JAVA_HOME   = C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot
    HADOOP_HOME = C:\hadoop            (winutils + hadoop.dll, D5)
    GHA_DATA_DIR= D:/gharchive-data
    venv        = .venv (PySpark 3.5.3, dbt-duckdb 1.9.1)

`C:\hadoop\bin` debe estar en el `PATH` de la sesión que ejecute Spark.

**Cloudflare WARP instalado y conectado.** Sin él, esta red no alcanza
`data.gharchive.org`: las IPs del servicio caen en un rango de Cloudflare
bloqueado aguas arriba del router (D10). **Hay que comprobar que WARP está
conectado antes de cualquier ingesta.**

Datos en disco al cerrar: `raw/` 2,53 GiB y `bronze/` 1,17 GiB, de los dos días
de prueba (2025-08-13 del tramo A y 2026-08-12 del tramo B).

## Qué queda pendiente y por dónde se retoma

**Punto exacto de retome: escribir `spark_jobs/silver.py`.**

1. **Silver** — tipado, dedup por `id`, columnas seleccionadas, flag `is_bot`.
   Tiene que resolver los dos esquemas (D12) detectando por campos, no por
   fecha, y derivar las latencias de PR de los `created_at` de los eventos
   unidos por `payload.pull_request.id` (D8).
2. **Medir silver.** Es la única cifra del reparto de presupuesto que sigue
   siendo una provisión (15 %) y no una medición. Si se pasa, se recorta el
   tramo A, que es el caro.
3. **Tests de calidad** — unicidad de `id`, `created_at` en rango, cobertura de
   las 24 horas, tasa de nulos por columna. Deben tolerar que el tramo B tenga
   columnas nulas por diseño, en vez de exigir cobertura uniforme.
4. **Lanzar el backfill** de los 435 días. A 88,70 MiB/s la descarga no es el
   cuello de botella; bronze tarda ~53 s por día del tramo A.
5. Fases 3, 4 y 5 sin empezar.

## Servicios al cerrar

- Sesiones de Spark: **ninguna viva** (sin procesos `java` ni `python`).
- Descargas: terminadas.
- Procesos en background: ninguno.
- Servidores de Evidence, contenedores: no se lanzó ninguno.
- **WARP queda conectado a propósito**, porque es la condición para que la
  ingesta funcione. Es lo único que sigue activo.
