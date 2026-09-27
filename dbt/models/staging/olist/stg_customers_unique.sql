with ranked as (
    select
        customer_unique_id,
        customer_city,
        customer_state,
        row_number() over (
            partition by customer_unique_id
            order by customer_id
        ) as rn
    from {{ ref('stg_customers') }}
)
select
    customer_unique_id,
    customer_city,
    customer_state
from ranked
where rn = 1