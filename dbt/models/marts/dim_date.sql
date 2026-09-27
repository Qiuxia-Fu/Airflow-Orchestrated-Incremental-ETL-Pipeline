with date_spine as (
    select generate_series(
        '2016-01-01'::date, '2018-12-31'::date, '1 day'::interval
    )::date as date_day
)
select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    to_char(date_day, 'Day') as day_name,
    extract(dow from date_day) in (0,6) as is_weekend
from date_spine