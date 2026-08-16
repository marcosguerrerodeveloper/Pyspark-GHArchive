# Proyecto: pipeline analítico sobre GH Archive

## Contexto

Esto es un proyecto de portfolio, no un producto. El objetivo es demostrar
competencia en PySpark, modelado dimensional y BI, con un artefacto público que
un desconocido pueda abrir en 10 segundos sin clonar nada.

El criterio de éxito no es "el código funciona". Es:

1. Hay un dashboard público con URL permanente.
2. El README explica decisiones y trade-offs, no solo cómo ejecutar.
3. Cada número del proyecto (volumen, tiempos, ratios) está medido, no estimado.

## Restricciones duras

- Coste total: 0 €. Nada de cloud de pago.
- Todo lo que corra en producción debe correr en GitHub Actions (repo público).
- El backfill grande corre en la máquina local del autor y sus salidas se publican.
- Nada de streaming. Batch programado.
- No se commitea nunca el JSON crudo al repo.

## Stack fijo (no proponer alternativas salvo que algo sea inviable)

| Capa | Herramienta |
|---|---|
| Ingesta | Python + `httpx`, descargas concurrentes |
| Proceso | PySpark (local, modo standalone) |
| Almacenamiento | Parquet / Delta particionado por fecha |
| Modelado | dbt-duckdb |
| Dashboard público | Evidence.dev desplegado en GitHub Pages |
| BI secundario | Power BI (.pbix + capturas en el repo) |
| Orquestación | GitHub Actions con cron diario |

## Preguntas de negocio que el proyecto debe responder

Estas tres, y solo estas tres. Cualquier métrica que no sirva a una de ellas no
entra en el dashboard.

1. **¿Qué parte de la actividad de PRs la generan bots y agentes automáticos, y
   cómo ha evolucionado en el tiempo?**
2. **¿Cuánto tarda un PR en recibir su primer review y en mergearse? ¿Difiere
   entre PRs de bot y de humano?**
3. **¿Qué proyectos ganan o pierden contribuyentes activos? Retención por
   cohortes de contribuyente nuevo.**

## Reglas de trabajo (importantes)

### 1. Nunca escribas código de parseo sin haber inspeccionado datos reales

Antes de definir un solo esquema, descarga un fichero horario real, ábrelo, y
muestra la estructura observada. Si no has visto el campo con tus propios ojos en
los datos, no existe. No infieras el esquema de la documentación ni de memoria.

### 2. Fases con checkpoint humano

No avances a la siguiente fase sin que yo lo apruebe explícitamente. Al final de
cada fase, para y resume qué has hecho y qué decisiones quedan abiertas.

### 3. Registra las decisiones

Cada decisión no trivial va a `docs/decisions.md` en 5 líneas: qué decidí, qué
alternativas había, por qué elegí esa, qué me cuesta.

Ejemplos de decisión no trivial: clave de particionado, formato de la capa
silver, cómo detecto bots, qué hago con eventos duplicados, dónde corto el
histórico.

### 4. Mide todo

Cualquier afirmación numérica en el código o en la documentación viene de una
medición registrada en `docs/metrics.md`: filas procesadas, duración del job,
tamaño en disco antes y después, ratio de compresión.

### 5. Código explicable antes que código elegante

Prefiero 40 líneas que yo pueda explicar en una entrevista a 15 líneas con tres
abstracciones. Sin frameworks propios, sin capas de configuración, sin clases
base abstractas.

### 6. No borres ni sobrescribas datos descargados sin avisar

## Fases

### Fase 0 — Reconocimiento (empezar aquí)

Objetivo: entender los datos reales antes de construir nada.

1. Descarga **un solo fichero horario** de GH Archive.
2. Reporta: tamaño comprimido, tamaño descomprimido, número de eventos.
3. Lista los tipos de evento presentes y su frecuencia.
4. Para `PullRequestEvent`, `PullRequestReviewEvent`, `IssuesEvent` y
   `PushEvent`: vuelca el esquema completo observado del `payload`, con un
   ejemplo real de cada uno.
5. **Verifica explícitamente** si el lenguaje del repo está disponible en el
   payload de `PullRequestEvent` y en qué ruta exacta. Es un supuesto crítico
   para la pregunta 1 y no lo doy por bueno.
6. Verifica si hay eventos duplicados por `id` dentro del fichero.
7. Comprueba si el array de commits de `PushEvent` está truncado comparándolo
   con el campo de tamaño.

Entregable: un documento `docs/exploracion.md` con los hallazgos. **Sin código de
pipeline todavía.**

### Fase 1 — Ingesta

Descarga idempotente y reanudable de un rango de fechas. Concurrencia máxima 6
conexiones, con reintentos y backoff exponencial. GH Archive es un servicio
gratuito mantenido por una persona: no lo satures.

Debe poder ejecutarse dos veces sin duplicar trabajo ni corromper nada.

### Fase 2 — Bronze y Silver

- Bronze: eventos crudos a Parquet particionado por fecha, sin transformar.
- Silver: tipado, deduplicado por `id`, columnas seleccionadas, flag `is_bot`.
- Borra el `.gz` en cuanto la hora esté escrita en bronze.

Tests de calidad obligatorios: unicidad de `id`, `created_at` dentro del rango
esperado, cobertura de las 24 horas de cada día, tasa de nulos por columna.

### Fase 3 — Gold y modelo dimensional

Esquema en estrella explícito con dbt-duckdb. Tablas de hechos con grano
documentado en el YAML de cada modelo. Tests de dbt en las claves.

### Fase 4 — Dashboard

Evidence.dev, tres páginas, una por pregunta de negocio. Desplegado en GitHub
Pages vía Actions.

### Fase 5 — Automatización

Workflow con cron diario que procesa el día anterior de forma incremental y
regenera el dashboard.

## Bitácora de sesiones

### Al empezar una sesión

Antes de tocar nada, lee los ficheros `docs/sesiones/sesionN.md` existentes (todos,
en orden). Sirven para no repetir trabajo ya hecho ni volver a caer en errores ya
diagnosticados. Si contradicen al código actual, manda el código.

### Al terminar una sesión

1. Escribe `docs/sesiones/sesionN.md` con el siguiente número libre (`sesion1.md`,
   `sesion2.md`, ...). Nunca sobrescribas una sesión anterior.
2. Contenido: qué se hizo, qué decisiones se tomaron, qué errores se cometieron y
   cómo se resolvieron, qué queda pendiente y en qué punto exacto se retoma.
3. Apaga todos los servicios que se hayan quedado corriendo: sesiones de Spark,
   procesos en background, servidores de Evidence, descargas, contenedores, y
   cualquier tarea lanzada durante la sesión. Confirma en el resumen que no queda
   nada vivo.

## Lo que escribo yo, no tú

- El README principal.
- Las conclusiones y la interpretación de los resultados.

Tú puedes proponer borradores, pero la voz del README es mía.
