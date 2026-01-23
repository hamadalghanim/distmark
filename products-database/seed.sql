CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    price DECIMAL(10, 2)
);

INSERT INTO
    products (name, price)
VALUES
    ('Product A', 19.99),
    ('Product B', 29.99),
    ('Product C', 39.99);