{{ config(materialized='view') }}

{{ format_power_demand(['power_demand', 'eria_jukyu_last_month_01_converted_header'], '北海道') }}