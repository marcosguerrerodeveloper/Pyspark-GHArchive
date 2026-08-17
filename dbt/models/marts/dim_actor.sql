-- Grano: un actor (cuenta de GitHub) observado en la ventana.
--
-- La clase de actor se resuelve en silver y aqui solo se consolida. Un mismo
-- login siempre tiene la misma clase, asi que se toma cualquiera: se usa
-- max() en vez de un group by mas elaborado porque la clase no varia.

{{ config(materialized='table') }}

select
    actor                               as actor,
    max(actor_clase)                    as actor_clase,
    max(actor_es_bot)                   as es_bot,
    count(*)                            as eventos_totales,
    count(distinct repo)                as repos_distintos,
    min(fecha)                          as primera_actividad,
    max(fecha)                          as ultima_actividad,
    date_trunc('month', min(fecha))::date as cohorte_mes
from {{ ref('stg_eventos') }}
group by actor
