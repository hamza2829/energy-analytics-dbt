with monthly_sales as (
    select month, partner_id, count(distinct customer_id) as customer_count, sum(kwh) as total_kwh
    from {{ ref('stg_partner_sales') }}
    group by month, partner_id
)
select
    strftime(s.month, '%Y-%m') || '_' || s.partner_id as statement_id,
    s.month,
    s.partner_id,
    r.partner_name,
    s.customer_count,
    s.total_kwh,
    r.retail_rate_eur_per_kwh,
    r.commission_pct,
    round(s.total_kwh * r.retail_rate_eur_per_kwh, 2)::decimal(14, 2) as sales_eur,
    round(s.total_kwh * r.retail_rate_eur_per_kwh * r.commission_pct, 2)::decimal(14, 2) as commission_eur
from monthly_sales s
join {{ ref('commission_rules') }} r using (partner_id)
