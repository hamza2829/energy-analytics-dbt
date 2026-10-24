{# Keep the original test file and its assertions unchanged. Translate only its
   hourly-series syntax when BigQuery executes the test materialization. #}
{% macro energy_bigquery_calendar_sql(main_sql) -%}
  {% if 'from generate_series(' not in main_sql or ') as hours(expected_hour)' not in main_sql %}
    {{ exceptions.raise_compiler_error('The frozen hourly calendar SQL changed; review the BigQuery translation.') }}
  {% endif %}
  {{ return(main_sql
      | replace('from generate_series(', 'from unnest(generate_timestamp_array(')
      | replace("interval '1 hour'", 'interval 1 hour')
      | replace(') as hours(expected_hour)', ')) as expected_hour')) }}
{%- endmacro %}

{% macro bigquery__get_test_sql(main_sql, fail_calc, warn_if, error_if, limit) -%}
  {% if model.name == 'no_missing_price_hours' %}
    {% set main_sql = energy_bigquery_calendar_sql(main_sql) %}
  {% endif %}
  {{ return(dbt.default__get_test_sql(main_sql, fail_calc, warn_if, error_if, limit)) }}
{%- endmacro %}
