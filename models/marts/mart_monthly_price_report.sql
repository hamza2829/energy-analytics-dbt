select
    date_trunc('month', price_date_utc)::date as month,
    count(*) as day_count,
    sum(hour_count)::integer as hour_count,
    min(min_price_eur_per_mwh) as min_price_eur_per_mwh,
    max(max_price_eur_per_mwh) as max_price_eur_per_mwh,
    round(sum(avg_price_eur_per_mwh * hour_count) / sum(hour_count), 6) as avg_price_eur_per_mwh,
    sum(negative_price_hours)::integer as negative_price_hours
from {{ ref('int_daily_price_stats') }}
group by 1
