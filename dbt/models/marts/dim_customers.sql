select
    s.customer_id,
    cs.customer_unique_id,
    cs.customer_city,
    cs.customer_state,
    cs.dbt_valid_from as valid_from,
    coalesce(cs.dbt_valid_to, '9999-12-31'::timestamp) as valid_to,
    cs.dbt_valid_to is null as is_current
from {{ ref('customers_snapshot') }} cs
inner join {{ ref('stg_customers') }} s
    on cs.customer_unique_id = s.customer_unique_id