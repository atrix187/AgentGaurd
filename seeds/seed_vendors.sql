
delete from vendors;

insert into vendors
    (name, relationship_months, bank_detail_changes, last_bank_change_date, total_volume_usd)
values
    ('Al Fardan Supplies', 36, 0, 'Never',       2400000),
    ('Gulf Tech Corp',     12, 1, '2023-06-15',   850000),
    ('ShadyVendor LLC',     0, 0, 'Never',              0);
