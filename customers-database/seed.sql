CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100)
);

INSERT INTO
    customers (name, email, password)
VALUES
    ('Alpha', 'alpha@example.com', 'hash1'),
    ('Beta', 'beta@example.com', 'hunter2'),
    ('Gamma', 'gamma@example.com', 'test') ON CONFLICT (email) DO NOTHING;