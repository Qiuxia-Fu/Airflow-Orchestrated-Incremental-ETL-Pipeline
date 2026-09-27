select distinct
    product_id,
    coalesce(product_category_name, 'unknown') as category
from {{ ref('stg_products') }}