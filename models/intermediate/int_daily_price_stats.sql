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
    {{ energy_cheapest_hours() }} as cheapest_3_hours_utc,
    avg(case when price_rank <= 3 then price_eur_per_mwh end) as cheapest_3_avg_eur_per_mwh,
    count(case when price_eur_per_mwh < 0 then 1 end) as negative_price_hours
from ranked
group by price_date_utc
