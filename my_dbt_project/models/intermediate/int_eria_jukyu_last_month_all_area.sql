{{
    config(
        materialized='view'
    )
}}

SELECT * EXCEPT(_dbt_source_relation) FROM (
    {{ dbt_utils.union_relations(
        relations=[
            ref('stg_eria_jukyu_last_month_01'),
            ref('stg_eria_jukyu_last_month_03')
            ]
    )}}
)