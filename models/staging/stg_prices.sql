select
    cast(timestamp_utc as timestamp) as timestamp_utc,
    cast(cast(timestamp_utc as timestamp) as date) as price_date_utc,
    cast(extract(hour from cast(timestamp_utc as timestamp)) as {{ dbt.type_int() }}) as hour_utc,
    bidding_zone,
    cast(price_eur_per_mwh as {{ energy_numeric_type(12, 2) }}) as price_eur_per_mwh
from {{ ref('raw_prices') }}
