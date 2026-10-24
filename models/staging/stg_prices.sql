select
    cast(timestamp_utc as timestamp) as timestamp_utc,
    cast(timestamp_utc as date) as price_date_utc,
    extract(hour from cast(timestamp_utc as timestamp))::integer as hour_utc,
    bidding_zone,
    cast(price_eur_per_mwh as decimal(12, 2)) as price_eur_per_mwh
from {{ ref('raw_prices') }}
