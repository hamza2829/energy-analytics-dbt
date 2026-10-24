with ranked as (
    select *, row_number() over (
        partition by price_date_utc order by price_eur_per_mwh, timestamp_utc
    ) as price_rank
    from {{ ref('stg_prices') }}
)
select
    price_date_utc,
    count(*) as hour_count,
    min(price_eur_per_mwh) as min_price_eur_per_mwh,
    max(price_eur_per_mwh) as max_price_eur_per_mwh,
    avg(price_eur_per_mwh) as avg_price_eur_per_mwh,
    list(hour_utc order by price_rank) filter (where price_rank <= 3) as cheapest_3_hours_utc,
    avg(price_eur_per_mwh) filter (where price_rank <= 3) as cheapest_3_avg_eur_per_mwh,
    count(*) filter (where price_eur_per_mwh < 0) as negative_price_hours
from ranked
group by price_date_utc
