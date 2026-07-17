{% macro log_dbt_run_results(results) %}
  {# Grava status de cada node do dbt em QC.DBT_RUN_RESULTS. #}
  {% if execute %}
    {% set create_sql %}
      create table if not exists {{ target.database }}.QC.DBT_RUN_RESULTS (
        invocation_id string,
        dbt_command string,
        unique_id string,
        resource_type string,
        node_name string,
        schema_name string,
        status string,
        execution_time_sec float,
        rows_affected number,
        message string,
        loaded_at timestamp_ntz default current_timestamp()
      )
    {% endset %}
    {% do run_query(create_sql) %}

    {% set cmd = flags.WHICH if flags is defined else 'unknown' %}

    {% for res in results %}
      {% set node = res.node %}
      {% set msg = (res.message | default('')) | replace("\\", "\\\\") | replace("'", "''") %}
      {% set rows_aff = none %}
      {% if res.adapter_response is mapping and res.adapter_response.get('rows_affected') is not none %}
        {% set rows_aff = res.adapter_response.get('rows_affected') %}
      {% endif %}
      {% set schema_name = node.schema if node.schema is defined else none %}
      {% set insert_sql %}
        insert into {{ target.database }}.QC.DBT_RUN_RESULTS (
          invocation_id, dbt_command, unique_id, resource_type, node_name,
          schema_name, status, execution_time_sec, rows_affected, message
        )
        values (
          '{{ invocation_id }}',
          '{{ cmd }}',
          '{{ node.unique_id }}',
          '{{ node.resource_type }}',
          '{{ node.name }}',
          {% if schema_name %}'{{ schema_name }}'{% else %}null{% endif %},
          '{{ res.status }}',
          {{ res.execution_time if res.execution_time is not none else 'null' }},
          {% if rows_aff is not none %}{{ rows_aff }}{% else %}null{% endif %},
          '{{ msg }}'
        )
      {% endset %}
      {% do run_query(insert_sql) %}
    {% endfor %}

    {{ log('dbt results gravados em ' ~ target.database ~ '.QC.DBT_RUN_RESULTS (' ~ results | length ~ ' nodes)', info=True) }}
  {% endif %}
{% endmacro %}
