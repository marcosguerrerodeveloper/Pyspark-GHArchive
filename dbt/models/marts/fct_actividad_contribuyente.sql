-- PREGUNTA DE NEGOCIO 3: que proyectos ganan o pierden contribuyentes activos,
-- y retencion por cohortes de contribuyente nuevo.
--
-- GRANO: un actor, en un repo, en un mes.
-- CLAVE: (mes, repo, actor).
--
-- La cohorte es el primer mes en que se ve al actor EN ESE REPO, no en todo
-- GitHub: la pregunta es sobre proyectos que ganan o pierden gente, asi que
-- "nuevo" significa nuevo para el proyecto.
--
-- LIMITACION: "nuevo" solo lo es respecto a la ventana observada. Alguien que
-- lleva años en un repo aparece como nuevo si su primera actividad dentro de
-- la ventana es el primer mes. El dashboard tiene que decirlo.

{{ config(materialized='table') }}

with por_mes as (
    select
        date_trunc('month', fecha)::date as mes,
        repo,
        actor,
        max(actor_clase)                 as actor_clase,
        max(actor_es_bot)                as es_bot,
        count(*)                         as eventos,
        count(distinct fecha)            as dias_activos,
        count(distinct tipo)             as tipos_distintos
    from {{ ref('stg_eventos') }}
    group by 1, 2, 3
),

cohortes as (
    select
        repo,
        actor,
        min(mes) as cohorte_mes
    from por_mes
    group by repo, actor
)

select
    m.mes,
    m.repo,
    m.actor,
    m.actor_clase,
    m.es_bot,
    m.eventos,
    m.dias_activos,
    m.tipos_distintos,
    c.cohorte_mes,

    -- Meses transcurridos desde que el actor apareció en el repo. Es el eje
    -- horizontal de la curva de retencion.
    date_diff('month', c.cohorte_mes, m.mes) as mes_de_vida,

    m.mes = c.cohorte_mes                    as es_primer_mes
from por_mes m
join cohortes c
  on c.repo = m.repo
 and c.actor = m.actor
