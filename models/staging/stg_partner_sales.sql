select
    customer_id || '_' || month as customer_month_id,
    cast(month as date) as month,
    partner_id,
    customer_id,
    customer_type,
    cast(kwh as decimal(12, 2)) as kwh
from {{ ref('partner_sales') }}
