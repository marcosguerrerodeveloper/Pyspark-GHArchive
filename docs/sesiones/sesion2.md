# Sesión 2 — 2026-08-16 / 17

De bronze funcionando a **dashboard público en línea**. Fases 2, 3 y 4 cerradas,
backfill completo, y una regeneración de silver a medias.

**https://mguerrerov.github.io/Pyspark-GHArchive/**

## Qué se hizo

**Fase 2 · Silver.** `silver.py` escribe dos tablas: `eventos` (sostiene la
pregunta 3) y `pr_eventos` (preguntas 1 y 2). La detección de los dos formatos
funciona por presencia de campos, sin la fecha del cambio escrita en el código.
Se añadieron `bots.py` (cinco clases de actor) y `tests_calidad.py`.

**Backfill.** 359 días, **1.311.676.396 eventos**, 149,4 GiB en bronze, sin un
solo fallo, en 3 horas. `backfill.py` encadena descarga → bronze → borrado del
crudo día a día, porque bajarlo todo antes de procesar son ~412 GiB.

**Fase 3 · Modelo dimensional.** dbt-duckdb, estrella con tres hechos —uno por
pregunta— y su grano documentado en el YAML. **8 modelos, 40 tests en verde.**

**Fase 4 · Dashboard.** Evidence con cuatro páginas, desplegado en GitHub Pages
vía Actions. Los avisos sobre el cambio de formato y el hueco de octubre salen
en la propia interfaz.

## Decisiones tomadas

D16–D31 en `decisions.md`. Las que más condicionan lo que viene:

- **D27 · `id` no es único.** GH Archive reutiliza identificadores en el formato
  reducido. La clave de un evento es **(evento_id, event_date)**, y por eso
  `evento_id` no puede ser clave primaria en gold.
- **D17 · zstd** y **D18 · proyección del JSON por tipo**: juntas dejan bronze
  en 0,536× el tamaño del `.gz`.
- **D24 y D25 · el shuffle**: `spark.local.dir` en `D:` y deduplicar después de
  proyectar.
- **D26 · conciliación bronze↔silver** en los tests.
- **D19 quater · ventana** `2025-08-15 → 2025-10-08` (tramo A) y
  `2025-10-15 → 2026-08-15` (tramo B).

## Errores cometidos, y cómo se resolvieron

1. **El `dropDuplicates` iba sobre bronze entero**, arrastrando `evento_json` al
   shuffle: 581 GiB en un solo `blockmgr` que dejó **`C:` en 0,5 GB libres**.
   → Deduplicar después de proyectar (D25) y mover el scratch a `D:` (D24).
   Liberados 610 GiB. El mismo rango que agotaba el disco pasó a 112 s.
2. **Deduplicar por `id` borraba 3.582.807 eventos reales.** No era una pérdida
   del job: silver coincidía exactamente con los ids únicos del lote, así que
   hacía lo que se le pedía y lo que se le pedía estaba mal. → D27.
3. **Los 16 tests pasaron sobre datos incompletos.** Todos miraban la coherencia
   interna de silver; ninguno preguntaba si silver tenía lo que bronze tenía.
   Un dataset truncado es internamente coherente. → D26.
4. **Un test acusó un desfase horario inexistente**: `.first()` convierte el
   timestamp a la zona del sistema operativo e ignora `session.timeZone`. Los
   datos estaban bien, el test estaba mal.
5. **Estimar en vez de medir**, otra vez: el coste del tramo B salió del único
   día más barato del año y erraba por tres veces.
6. **Lanzar procesos de horas en una sola pieza.** Se cortaron cinco veces. Con
   `silver_todo.py` cada lote se anota y se reanuda.
7. **Dos instancias de `silver_todo.py` corriendo a la vez** al final de la
   sesión: los cortes mataban la envoltura pero no el proceso hijo. Se
   detuvieron y **se verificó que no hubo corrupción** (los descuadres eran de
   1 a 9 filas, deduplicación legítima).

El patrón de 2, 3 y 5 es el mismo: **dar por buena una regla razonable sin
comprobarla contra los datos**. "Deduplicar por id" lo dice la especificación y
lo hace todo el mundo con GH Archive; aquí es incorrecto.

## Estado de los datos

| Capa | Estado |
|---|---|
| `raw/` | vacío salvo 2 días de pruebas (~3 GiB) |
| `bronze/` | **completo**, 361 particiones, 149,4 GiB |
| `silver/` | **INCOMPLETO** — 26 días de 361 regenerados con la dedup correcta |
| `gold/` | construido sobre la ventana de desarrollo (6 días) |
| dashboard | en línea, con los datos de esos 6 días |

Discos al cerrar: `C:` 593,4 GB libres, `D:` 1.229,5 GB.

## Qué queda pendiente y por dónde se retoma

**Punto exacto de retome: terminar la regeneración de silver.**

Los procesos largos lanzados desde Claude Code se cortan. Hay que ejecutarlo en
una PowerShell propia:

    cd C:\Users\marco\Desktop\W\Proyectos\Pyspark-GHArchive
    $env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot"
    $env:HADOOP_HOME="C:\hadoop"
    $env:GHA_DATA_DIR="D:/gharchive-data"
    $env:PATH="C:\hadoop\bin;$env:PATH"
    .\.venv\Scripts\python.exe -u silver_todo.py --desde 2025-08-13 --hasta 2026-08-15 --dias-por-lote 7

Es reanudable: si se corta, se repite el mismo comando. Empieza por el día 27 y
son unas 7 horas. **Comprobar antes que no haya otra instancia corriendo.**

Después, el cierre son tres pasos de minutos:

1. `dbt run` y `dbt test` con la ventana completa.
2. `python exportar_gold.py`.
3. `git add dashboard/sources && git commit && git push` — Pages se regenera solo.

Luego:

4. **Revisar las latencias de la pregunta 2.** Con 6 días salían absurdas
   (mediana de 1 minuto hasta merge) por la censura. Con 12,5 meses hay que
   mirarlas antes de darlas por buenas.
5. **Afinar los gráficos** con datos reales: ahora las series tienen 3 puntos.
6. **Fase 5** — cron diario. Hay una decisión abierta: el runner no tiene acceso
   al lago, así que la retención por cohortes no se puede recalcular allí. La
   propuesta es que el cron actualice solo las preguntas 1 y 2 y que la 3 se
   regenere en local, documentándolo.
7. **Power BI** (.pbix y capturas) y el **README**, que lo escribe Marcos.

## Servicios al cerrar

- Sesiones de Spark: **ninguna viva** (se detuvieron las dos instancias
  duplicadas y su JVM).
- Descargas y procesos en background: ninguno.
- Servidor de Evidence: no quedó ninguno; el sitio es estático en Pages.
- Scratch de Spark: **39,90 GiB liberados** de `D:/gharchive-data/spark-tmp`.
- **WARP queda conectado a propósito**: es la condición para alcanzar GH
  Archive (D10). Es lo único activo.
