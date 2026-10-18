{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}

    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {# プレフィックスを付けず、カスタムスキーマ名をそのまま使う場合 #}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}