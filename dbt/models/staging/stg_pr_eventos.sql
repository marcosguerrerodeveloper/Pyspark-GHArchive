-- Vista sobre silver/pr_eventos: eventos de PR con el payload ya extraido.
-- Sostiene las preguntas de negocio 1 y 2.

{{ config(materialized='view') }}

select
    evento_id,
    event_date::date          as fecha,
    tipo,
    creado_en,
    actor,
    actor_es_bot,
    actor_clase,
    repo,
    pr_id,
    pr_numero,
    accion,
    es_merge,
    esquema,
    repo_lenguaje,
    pr_autor,
    pr_autor_tipo,
    pr_abierto_en,
    pr_mergeado_en,
    pr_cerrado_en,
    pr_lineas_add,
    pr_lineas_del,
    review_estado,
    review_enviado_en
from read_parquet(
    '{{ env_var("GHA_DATA_DIR", "D:/gharchive-data") }}/silver/pr_eventos/**/*.parquet',
    hive_partitioning = true
)
where event_date between '{{ var("fecha_desde") }}' and '{{ var("fecha_hasta") }}'
