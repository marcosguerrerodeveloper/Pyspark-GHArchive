-- Vista sobre silver/eventos. No transforma nada: solo expone el Parquet
-- particionado como una tabla y acota la ventana del proyecto.
--
-- hive_partitioning recupera event_date del nombre del directorio, que es
-- donde vive: Spark no la escribe dentro del fichero.

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
    repo_owner
from read_parquet(
    '{{ env_var("GHA_DATA_DIR", "D:/gharchive-data") }}/silver/eventos/**/*.parquet',
    hive_partitioning = true
)
where event_date between '{{ var("fecha_desde") }}' and '{{ var("fecha_hasta") }}'
