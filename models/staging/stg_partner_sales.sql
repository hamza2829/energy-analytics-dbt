select
    customer_id || '_' || month as customer_month_id,
    cast(month as date) as month,
    partner_id,
    customer_id,
    customer_type,
    cast(kwh as {{ energy_numeric_type(12, 2) }}) as kwh
from {{ ref('partner_sales') }}
