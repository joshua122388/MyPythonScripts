# PySpark Customer Analysis

Analyzes `customers_large.csv` (100,000 rows) using PySpark to answer four business questions.

## Dataset

| Column | Type | Description |
|---|---|---|
| sale_date | date | YYYY-MM-DD |
| customer_id | string | CUST-XXXXXX |
| first_name | string | |
| last_name | string | |
| email | string | |
| segment | string | Enterprise, Government, Consumer, Corporate, SMB |
| city | string | |
| country | string | |
| product_name | string | |
| category | string | |
| sub_category | string | |
| unit_price | int | |
| quantity | int | |
| revenue | double | |

## Queries

| Task | Description |
|---|---|
| A | Total revenue by country, descending |
| B | Top 3 best-selling products by total revenue |
| C | Corporate segment customers with revenue > $500 |
| D | Unique customers per city, descending |

## Requirements

- Python 3.x
- PySpark

Install PySpark:

```bash
pip install pyspark
```

## Usage

Place `customers_large.csv` in the same directory as `customers.py`, then run:

```bash
python customers.py
```
