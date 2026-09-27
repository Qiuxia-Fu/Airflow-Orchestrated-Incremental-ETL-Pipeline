select
    product_id,
    product_category_name
from {{source('raw', 'raw_products')}}