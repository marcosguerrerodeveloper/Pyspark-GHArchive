---
title: 1 · Actividad de PRs generada por bots y agentes
---

Cada evento de pull request se atribuye a una clase de actor. La señal que
decide si un actor es automático es el sufijo `[bot]` que GitHub añade a las
cuentas de App; la clase concreta sale de una lista de servicios conocidos.

```sql por_clase
select actor_clase, sum(eventos) as eventos
from gharchive.p1_actividad_mensual
group by 1 order by 2 desc
```

```sql total
select sum(eventos) as eventos from gharchive.p1_actividad_mensual
```

<BigValue data={total} value=eventos title="Eventos de PR analizados" fmt=num0/>

<ECharts config={{
    tooltip: { trigger: 'item' },
    series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: [...por_clase].map(d => ({ name: d.actor_clase, value: d.eventos }))
    }]
}}/>

## Evolución en el tiempo

```sql mensual
select mes, actor_clase, eventos
from gharchive.p1_actividad_mensual
order by mes
```

<AreaChart
    data={mensual}
    x=mes
    y=eventos
    series=actor_clase
    title="Eventos de PR por mes y clase de actor"
/>

<AreaChart
    data={mensual}
    x=mes
    y=eventos
    series=actor_clase
    type=stacked100
    title="Reparto porcentual"
/>

## Agentes de IA

Categoría aparte de la automatización clásica: no son CI ni actualizadores de
dependencias, sino agentes que abren y revisan código.

```sql agentes
select actor, sum(eventos) as eventos, max(repos) as repos
from gharchive.p1_top_agentes
group by 1 order by 2 desc limit 15
```

<DataTable data={agentes} rows=15>
    <Column id=actor title="Agente"/>
    <Column id=eventos title="Eventos" fmt=num0 contentType=bar/>
    <Column id=repos title="Repos" fmt=num0/>
</DataTable>

## Por lenguaje del repositorio

<Alert status=info>

El lenguaje solo está disponible en el tramo anterior al 9 de octubre de 2025.
Desde entonces la fuente no lo publica.

</Alert>

```sql lenguajes
select
    lenguaje,
    sum(eventos)                                                  as eventos,
    sum(case when actor_clase <> 'humano' then eventos else 0 end) as automaticos,
    round(100.0 * sum(case when actor_clase <> 'humano' then eventos else 0 end)
          / sum(eventos), 1)                                       as pct_automatico
from gharchive.p1_por_lenguaje
group by 1
having sum(eventos) >= 500
order by 2 desc
limit 20
```

<DataTable data={lenguajes} rows=20>
    <Column id=lenguaje title="Lenguaje"/>
    <Column id=eventos title="Eventos" fmt=num0/>
    <Column id=pct_automatico title="% automático" fmt=num1 contentType=colorscale/>
</DataTable>
