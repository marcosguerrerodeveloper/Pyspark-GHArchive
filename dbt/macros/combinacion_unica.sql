{#
  Test generico: la combinacion de columnas es unica.

  Existe en dbt_utils, pero traer el paquete entero para una sola cosa no
  compensa: son doce lineas y asi el proyecto no tiene dependencias externas.

  Hace falta porque ninguna clave de los hechos es de una sola columna: la de
  un evento es (fecha, evento_id), no evento_id, ya que GH Archive reutiliza
  identificadores entre fechas (D27).
#}

{% test combinacion_unica(model, combination_of_columns) %}

with contado as (
    select
        {{ combination_of_columns | join(', ') }},
        count(*) as n
    from {{ model }}
    group by {{ combination_of_columns | join(', ') }}
    having count(*) > 1
)

select * from contado

{% endtest %}
