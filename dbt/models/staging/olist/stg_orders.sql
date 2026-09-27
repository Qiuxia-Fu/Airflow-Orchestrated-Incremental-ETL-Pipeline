select
    order_id,
    customer_id,
    order_status,
    cast(order_purchase_timestamp as timestamp) as order_purchase_ts,
    cast(order_delivered_customer_date as timestamp) as delivered_ts
from {{source('raw','raw_orders')}}