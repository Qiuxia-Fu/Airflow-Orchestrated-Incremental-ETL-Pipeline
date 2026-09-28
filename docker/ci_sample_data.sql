INSERT INTO raw.raw_orders_incremental (
    order_id, customer_id, order_status, order_purchase_timestamp,
    order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date
) VALUES
    ('ci_test_001', 'cust_001', 'delivered', '2018-05-01 10:00:00', '2018-05-01 11:00:00', '2018-05-02 09:00:00', '2018-05-05 14:00:00', '2018-05-10'),
    ('ci_test_002', 'cust_002', 'delivered', '2018-05-02 10:00:00', '2018-05-02 11:00:00', '2018-05-03 09:00:00', '2018-05-06 14:00:00', '2018-05-11'),
    ('ci_test_003', 'cust_003', 'shipped',   '2018-05-03 10:00:00', '2018-05-03 11:00:00', '2018-05-04 09:00:00', NULL,                  '2018-05-12'),
    ('ci_test_004', 'cust_004', 'delivered', '2018-05-04 10:00:00', '2018-05-04 11:00:00', '2018-05-05 09:00:00', '2018-05-08 14:00:00', '2018-05-13'),
    ('ci_test_005', 'cust_005', 'canceled',  '2018-05-05 10:00:00', NULL,                  NULL,                  NULL,                  '2018-05-14');
