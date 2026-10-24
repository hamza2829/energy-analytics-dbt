-- Returning any row fails the test. Nulls are covered by the mart's not_null test.
select statement_id, commission_eur
from {{ ref('mart_monthly_partner_commission') }}
where commission_eur < 0
