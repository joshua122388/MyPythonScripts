# Sales Data Warehouse

A star-schema data warehouse for sales analytics, built with PostgreSQL and a Python ETL pipeline.

## Project Structure

```
dataWarehouse/
├── scheme.sql        # Star schema DDL + sample data + analytical queries
├── etl_pipeline.py   # Python ETL pipeline (Extract → Transform → Load)
└── raw_sales.xlsx    # Source sales data
```

## Schema

The warehouse uses a **star schema** with one fact table and four dimension tables.

```
dim_date ──┐
dim_product──┤
             ├── fact_sales
dim_customer─┤
dim_location─┘
```

| Table | Key Columns |
|---|---|
| `dim_date` | `date_id`, `full_date`, `year`, `quarter`, `month`, `month_name` |
| `dim_product` | `product_id`, `product_name`, `category`, `sub_category`, `unit_price` |
| `dim_customer` | `customer_id`, `full_name`, `segment`, `email` |
| `dim_location` | `location_id`, `city`, `country`, `region` |
| `fact_sales` | `sale_id`, `date_id`, `product_id`, `customer_id`, `location_id`, `revenue`, `quantity` |

## Prerequisites

- Python 3.8+
- PostgreSQL (running locally on port 5432)
- Python packages:

```bash
pip install pandas sqlalchemy psycopg2-binary openpyxl
```

## Setup

1. **Create the database:**

```bash
createdb warehouse
```

2. **Apply the schema:**

```bash
psql -U postgres -d warehouse -f scheme.sql
```

3. **Configure the connection** in `etl_pipeline.py` if needed:

```python
DB_URL = "postgresql://postgres:<password>@localhost:5432/warehouse"
```

## Running the ETL Pipeline

```bash
python etl_pipeline.py
```

The pipeline will:
1. **Extract** — read `raw_sales.xlsx` into a DataFrame
2. **Transform** — split raw data into dimension tables (`dim_date`, `dim_product`, `dim_customer`, `dim_location`)
3. **Load** — insert dimensions into PostgreSQL, read back generated IDs, then build and insert `fact_sales`

## Analytical Queries

`scheme.sql` includes ready-to-run queries:

- Revenue by product category and quarter (filterable by country)
- Total revenue per country in Q1 2024
- Product category with the most units sold
- Revenue breakdown by customer segment (with percentage)
