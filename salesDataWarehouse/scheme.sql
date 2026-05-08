-- =====================
-- STAR SCHEMA
-- =====================

-- Dimension tables first (no foreign keys yet)
CREATE TABLE dim_date (
    date_id     SERIAL PRIMARY KEY,
    full_date   DATE NOT NULL,
    year        INT,
    quarter     INT,
    month       INT,
    month_name  VARCHAR(20)
);

CREATE TABLE dim_product (
    product_id    SERIAL PRIMARY KEY,
    product_name  VARCHAR(100),
    category      VARCHAR(50),
    sub_category  VARCHAR(50),
    unit_price    DECIMAL(10,2)
);

CREATE TABLE dim_customer (
    customer_id  SERIAL PRIMARY KEY,
    full_name    VARCHAR(100),
    segment      VARCHAR(50),
    email        VARCHAR(100)
);

CREATE TABLE dim_location (
    location_id  SERIAL PRIMARY KEY,
    city         VARCHAR(100),
    country      VARCHAR(100),
    region       VARCHAR(50)
);

-- Fact table references all dimensions
CREATE TABLE fact_sales (
    sale_id      SERIAL PRIMARY KEY,
    date_id      INT REFERENCES dim_date(date_id),
    product_id   INT REFERENCES dim_product(product_id),
    customer_id  INT REFERENCES dim_customer(customer_id),
    location_id  INT REFERENCES dim_location(location_id),
    revenue      DECIMAL(12,2),
    quantity     INT
);

-- records insertion

-- Populate dimensions
INSERT INTO dim_date (full_date, year, quarter, month, month_name)
VALUES
  ('2024-01-15', 2024, 1, 1, 'January'),
  ('2024-03-22', 2024, 1, 3, 'March'),
  ('2024-07-10', 2024, 3, 7, 'July');

INSERT INTO dim_product (product_name, category, sub_category, unit_price)
VALUES
  ('Laptop Pro 15',   'Electronics', 'Computers',  1200.00),
  ('Wireless Mouse',  'Electronics', 'Accessories',  35.00),
  ('Standing Desk',   'Furniture',   'Desks',       450.00);

INSERT INTO dim_customer (full_name, segment, email)
VALUES
  ('Maria Gonzalez', 'Consumer',   'maria@email.com'),
  ('Tech Corp S.A.', 'Corporate',  'buy@techcorp.com');

INSERT INTO dim_location (city, country, region)
VALUES
  ('San José',   'Costa Rica', 'Central America'),
  ('Miami',      'USA',        'North America');

-- Populate fact table
INSERT INTO fact_sales (date_id, product_id, customer_id, location_id, revenue, quantity)
VALUES
  (1, 1, 1, 1, 1200.00, 1),
  (1, 2, 1, 1,   35.00, 2),
  (2, 3, 2, 2,  450.00, 4),
  (3, 1, 2, 2, 2400.00, 2);

  -- Revenue by category and quarter
SELECT
    dp.category,
    dd.quarter,
    dd.year,
    SUM(fs.revenue)   AS total_revenue,
    SUM(fs.quantity)  AS units_sold
FROM fact_sales fs
JOIN dim_product  dp ON fs.product_id  = dp.product_id
JOIN dim_date     dd ON fs.date_id     = dd.date_id
JOIN dim_location dl ON fs.location_id = dl.location_id
WHERE dl.country = 'Costa Rica'
GROUP BY dp.category, dd.quarter, dd.year
ORDER BY dd.year, dd.quarter, total_revenue DESC;

-- Total revenue per country in Q1 2024

SELECT
    dl.country,
    SUM(fs.revenue) AS total_revenue
FROM fact_sales fs
JOIN dim_location dl ON fs.location_id = dl.location_id
JOIN dim_date     dd ON fs.date_id     = dd.date_id
WHERE dd.year = 2024
  AND dd.quarter = 1
GROUP BY dl.country
ORDER BY total_revenue DESC;

-- Product category with the most units sold

SELECT
    dp.category,
    SUM(fs.quantity) AS units_sold
FROM fact_sales fs
JOIN dim_product dp ON fs.product_id = dp.product_id
GROUP BY dp.category
ORDER BY units_sold DESC
LIMIT 1;

-- Revenue by customer segment

SELECT
    dc.segment,
    SUM(fs.revenue)            AS total_revenue,
    ROUND(
        SUM(fs.revenue) * 100.0 /
        SUM(SUM(fs.revenue)) OVER (), 2
    ) AS revenue_pct
FROM fact_sales fs
JOIN dim_customer dc ON fs.customer_id = dc.customer_id
GROUP BY dc.segment
ORDER BY total_revenue DESC;