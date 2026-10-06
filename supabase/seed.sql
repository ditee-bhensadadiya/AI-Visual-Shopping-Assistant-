-- Synthetic fixture records; these are not live retailer offers.
insert into public.products(id,name,brand,category,color) values
('10000000-0000-4000-8000-000000000001','Everyday Canvas Backpack','Northwind','Bags','Olive'),
('10000000-0000-4000-8000-000000000002','Classic Running Shoe','Contoso Athletics','Footwear','White')
on conflict(id) do nothing;
insert into public.retailers(id,name,website) values
('20000000-0000-4000-8000-000000000001','Demo Store One','https://example.com/store-one'),
('20000000-0000-4000-8000-000000000002','Demo Store Two','https://example.com/store-two')
on conflict(id) do nothing;
insert into public.retailer_products(id,product_id,retailer_id,retailer_product_name,product_url,external_product_id,current_price,currency,availability) values
('30000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','Everyday Canvas Backpack','https://example.com/store-one/backpack','DEMO-BAG-1',49.99,'USD','in_stock'),
('30000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000002','Canvas Day Pack','https://example.com/store-two/backpack','DEMO-BAG-2',54.50,'USD','in_stock'),
('30000000-0000-4000-8000-000000000003','10000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000001','Classic Running Shoe','https://example.com/store-one/shoe','DEMO-SHOE-1',79.00,'USD','in_stock')
on conflict(id) do nothing;
insert into public.price_history(retailer_product_id,price,currency,availability,recorded_at) values
('30000000-0000-4000-8000-000000000001',49.99,'USD','in_stock',now()-interval '2 days'),
('30000000-0000-4000-8000-000000000001',47.99,'USD','in_stock',now()-interval '1 day'),
('30000000-0000-4000-8000-000000000002',54.50,'USD','in_stock',now()-interval '1 day'),
('30000000-0000-4000-8000-000000000003',79.00,'USD','in_stock',now()-interval '1 day');

