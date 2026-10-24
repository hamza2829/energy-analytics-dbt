select
    {{ energy_month_start('price_date_utc') }} as month,
    count(*) as day_count,
    cast(sum(hour_count) as {{ dbt.type_int() }}) as hour_count,
    min(min_price_eur_per_mwh) as min_price_eur_per_mwh,
    max(max_price_eur_per_mwh) as max_price_eur_per_mwh,
    round(sum(avg_price_eur_per_mwh * hour_count) / sum(hour_count), 6) as avg_price_eur_per_mwh,
    cast(sum(negative_price_hours) as {{ dbt.type_int() }}) as negative_price_hours
from {{ ref('int_daily_price_stats') }}
group by 1
