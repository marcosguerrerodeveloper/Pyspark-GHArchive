---
title: Actividad automática en GitHub
description: Bots, agentes de IA y contribuyentes humanos sobre GH Archive
---

```sql cobertura
select
    min(fecha)  as desde,
    max(fecha)  as hasta,
    count(*)    as dias,
    count(*) filter (where formato_fuente = 'completo') as dias_completos,
    count(*) filter (where es_hueco_conocido)           as dias_hueco
from gharchive.dim_fecha
```

<BigValue data={cobertura} value=dias title="Días analizados"/>
<BigValue data={cobertura} value=desde title="Desde"/>
<BigValue data={cobertura} value=hasta title="Hasta"/>

Tres preguntas, una página cada una.

<LinkButton url='/bots'>1 · ¿Cuánta actividad de PRs generan los bots?</LinkButton>
<LinkButton url='/latencias'>2 · ¿Cuánto tarda un PR en revisarse y mergearse?</LinkButton>
<LinkButton url='/retencion'>3 · ¿Qué proyectos ganan o pierden contribuyentes?</LinkButton>

## Sobre los datos

Los datos vienen de [GH Archive](https://www.gharchive.org/), que publica cada
hora el flujo de eventos públicos de GitHub.

<Alert status=warning>

**La fuente cambió de formato el 9 de octubre de 2025.** Desde esa fecha los
eventos llegan con el payload recortado: no traen el lenguaje del repositorio,
ni los instantes de apertura y merge del pull request, ni el detalle de los
commits. Las series que cruzan esa fecha lo indican.

Además, del 9 al 14 de octubre de 2025 la fuente publicó ficheros
prácticamente vacíos —unos 600 eventos por hora frente a los 150.000
habituales—. Esos seis días están **excluidos**, no son días de baja actividad.

</Alert>

```sql formato
select formato_fuente, count(*) as dias
from gharchive.dim_fecha where tiene_datos group by 1
```

<DataTable data={formato}>
    <Column id=formato_fuente title="Formato de la fuente"/>
    <Column id=dias title="Días" fmt=num0/>
</DataTable>
