-- Grano: un repositorio observado en la ventana.
--
-- El lenguaje solo existe en el tramo de formato completo (hasta 2025-10-08),
-- asi que se toma el ultimo valor no nulo visto. Los repos que solo aparecen
-- en el tramo reducido tendran lenguaje nulo: es una limitacion de la fuente,
-- no un fallo, y el dashboard debe decirlo.

{{ config(materialized='table') }}

with lenguaje as (
    select
        repo,
        arg_max(repo_lenguaje, fecha) as lenguaje
    from {{ ref('stg_pr_eventos') }}
    where repo_lenguaje is not null
    group by repo
)

select
    e.repo                              as repo,
    e.repo_owner                        as propietario,
    l.lenguaje                          as lenguaje,
    l.lenguaje is not null              as tiene_lenguaje,
    count(*)                            as eventos_totales,
    count(distinct e.actor)             as actores_distintos,
    min(e.fecha)                        as primera_actividad,
    max(e.fecha)                        as ultima_actividad
from {{ ref('stg_eventos') }} e
left join lenguaje l on l.repo = e.repo
group by e.repo, e.repo_owner, l.lenguaje
