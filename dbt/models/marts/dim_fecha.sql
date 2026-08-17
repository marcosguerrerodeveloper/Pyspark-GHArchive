-- Grano: un dia natural de la ventana analizada.
--
-- Marca el tramo de formato y los huecos conocidos, para que el dashboard
-- pueda avisar en vez de dibujar una serie continua sobre datos que no lo son.

{{ config(materialized='table') }}

with dias as (
    select unnest(generate_series(
        date '{{ var("fecha_desde") }}',
        date '{{ var("fecha_hasta") }}',
        interval 1 day
    ))::date as fecha
),

con_datos as (
    select distinct fecha from {{ ref('stg_eventos') }}
)

select
    d.fecha,
    year(d.fecha)                       as anio,
    month(d.fecha)                      as mes,
    date_trunc('month', d.fecha)::date  as primer_dia_mes,
    dayofweek(d.fecha)                  as dia_semana,
    dayofweek(d.fecha) in (0, 6)        as es_fin_de_semana,

    -- El formato de la fuente cambio el 2025-10-09 (D27 y anexos de la Fase 0).
    case when d.fecha <= date '2025-10-08' then 'completo' else 'reducido' end
        as formato_fuente,

    -- Hueco de D13: GH Archive sirvio estos dias practicamente vacios.
    d.fecha between date '2025-10-09' and date '2025-10-14'
        as es_hueco_conocido,

    c.fecha is not null                 as tiene_datos
from dias d
left join con_datos c on c.fecha = d.fecha
