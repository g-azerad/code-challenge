CREATE DATABASE uni;

\c uni;

-- Creates user and grants rights
\set db_password 'kuuli'
CREATE ROLE hoodie WITH LOGIN PASSWORD :'db_password';
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO hoodie;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO hoodie;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO hoodie;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TYPES TO hoodie;

-- Create tables
CREATE TYPE cart_status AS ENUM ('active', 'ordered', 'inactive', 'deleted');

CREATE TABLE carts(
    id UUID PRIMARY KEY,
    session_id TEXT,
    status cart_status,
    session_storage JSONB
);

CREATE TABLE products(
    id UUID PRIMARY KEY,
    cart_id UUID REFERENCES carts (id),
    product_url TEXT NOT NULL,
    product_variant TEXT,
    quantity INTEGER,
    msrp FLOAT(3),
    price FLOAT(3)
);

CREATE TABLE orders(
    id UUID PRIMARY KEY,
    cart_id UUID REFERENCES carts(id),
    order_type TEXT,        -- Pickup, Drive-thru, pick-up, etc
    payment_type TEXT,      -- Cash, Credit card, Debit card, etc
    pickup_time TEXT
);