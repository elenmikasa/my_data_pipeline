{% macro format_power_demand(source_node, area_name) %}
    {%- set source_relation = source(source_node[0], source_node[1]) -%}
    {%- set columns = adapter.get_columns_in_relation(source_relation) -%}

    select
        '{{ area_name }}' as area_name,
        
        -- エリアごとのフォーマットの違い（スラッシュ or ハイフンなし等）をここで吸収して DATE 型に統一
        COALESCE(
            SAFE.PARSE_DATE('%Y/%m/%d', CAST(`date` AS STRING)),
            SAFE.PARSE_DATE('%Y-%m-%d', CAST(`date` AS STRING)),
            SAFE.PARSE_DATE('%Y%m%d', CAST(`date` AS STRING))
        ) AS `date`,

        FORMAT_TIME('%H:%M', PARSE_TIME('%H:%M', `time`)) AS `time`,
        
        -- date と time 以外の全カラムを、動的に取得してすべて FLOAT64 に一括変換
        {%- for col in columns %}
            {%- if col.name not in ['date', 'time'] %}
            SAFE_CAST({{ col.name }} AS FLOAT64) AS {{ col.name }}{% if not loop.last %},{% endif %}
            {%- endif %}
        {%- endfor %}

    from {{ source_relation }}
    WHERE `date` IS NOT NULL AND `time` IS NOT NULL
{% endmacro %}