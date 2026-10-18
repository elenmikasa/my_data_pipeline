{{
    config(
        materialized='incremental',
        unique_key=['date', 'time', 'area_name'],
        incremental_strategy='merge',
        partition_by={
            "field": "date",
            "data_type": "date",
            "granularity": "day"
        }
    )
}}


SELECT
    *,
    DATETIME(CURRENT_TIMESTAMP(), "Asia/Tokyo") AS updated_at_jst

FROM {{ ref('int_eria_jukyu_last_month_all_area') }}