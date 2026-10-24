{% macro energy_numeric_type(precision, scale) -%}
  {{ return(adapter.dispatch('energy_numeric_type', 'energy_analytics')(precision, scale)) }}
{%- endmacro %}

{% macro duckdb__energy_numeric_type(precision, scale) -%}
  {{ return('decimal(' ~ precision ~ ', ' ~ scale ~ ')') }}
{%- endmacro %}

{% macro bigquery__energy_numeric_type(precision, scale) -%}
  {{ return('numeric') }}
{%- endmacro %}

{% macro energy_month_start(expression) -%}
  {{ return(adapter.dispatch('energy_month_start', 'energy_analytics')(expression)) }}
{%- endmacro %}

{% macro duckdb__energy_month_start(expression) -%}
  cast(date_trunc('month', {{ expression }}) as date)
{%- endmacro %}

{% macro bigquery__energy_month_start(expression) -%}
  date_trunc(cast({{ expression }} as date), month)
{%- endmacro %}

{% macro energy_month_key(expression) -%}
  {{ return(adapter.dispatch('energy_month_key', 'energy_analytics')(expression)) }}
{%- endmacro %}

{% macro duckdb__energy_month_key(expression) -%}
  strftime({{ expression }}, '%Y-%m')
{%- endmacro %}

{% macro bigquery__energy_month_key(expression) -%}
  format_date('%Y-%m', cast({{ expression }} as date))
{%- endmacro %}

{% macro energy_cheapest_hours() -%}
  {{ return(adapter.dispatch('energy_cheapest_hours', 'energy_analytics')()) }}
{%- endmacro %}

{% macro duckdb__energy_cheapest_hours() -%}
  list(hour_utc order by price_rank) filter (where price_rank <= 3)
{%- endmacro %}

{% macro bigquery__energy_cheapest_hours() -%}
  array_agg(if(price_rank <= 3, hour_utc, null) ignore nulls order by price_rank)
{%- endmacro %}
