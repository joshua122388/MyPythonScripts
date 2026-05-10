import io
import pandas as pd
from sqlalchemy import create_engine, text

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
DB_URL = "postgresql://postgres:123@localhost:5432/warehouse"
CSV_FILE = r"d:\dataWarehouse\raw_sales.xlsx"

engine = create_engine(DB_URL)


# ─────────────────────────────────────────
# EXTRACT
# ─────────────────────────────────────────
def extract(filepath: str) -> pd.DataFrame:
    print("Extracting data...")
    raw = pd.read_excel(filepath, header=None)
    csv_text = "\n".join(raw.iloc[:, 0].astype(str).tolist())
    df = pd.read_csv(io.StringIO(csv_text), parse_dates=["sale_date"])
    print(f"  {len(df)} rows loaded from {filepath}")
    return df


# ─────────────────────────────────────────
# TRANSFORM
# ─────────────────────────────────────────
def transform(df: pd.DataFrame) -> dict:
    print("Transforming data...")

    # --- dim_date ---
    dim_date = df[["sale_date"]].drop_duplicates().copy()
    dim_date.columns = ["full_date"]
    dim_date["year"]       = dim_date["full_date"].dt.year
    dim_date["quarter"]    = dim_date["full_date"].dt.quarter
    dim_date["month"]      = dim_date["full_date"].dt.month
    dim_date["month_name"] = dim_date["full_date"].dt.strftime("%B")

    # --- dim_product ---
    dim_product = df[["product_name", "category", "sub_category", "unit_price"]] \
        .drop_duplicates().copy()

    # --- dim_customer ---
    dim_customer = df[["customer_name", "segment", "email"]] \
        .drop_duplicates().copy()
    dim_customer.columns = ["full_name", "segment", "email"]

    # --- dim_location ---
    dim_location = df[["city", "country", "region"]] \
        .drop_duplicates().copy()

    print(f"  dim_date:     {len(dim_date)} rows")
    print(f"  dim_product:  {len(dim_product)} rows")
    print(f"  dim_customer: {len(dim_customer)} rows")
    print(f"  dim_location: {len(dim_location)} rows")

    return {
        "dim_date":     dim_date,
        "dim_product":  dim_product,
        "dim_customer": dim_customer,
        "dim_location": dim_location,
        "raw":          df,
    }


# ─────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────
def load(data: dict):
    print("Loading data...")

    with engine.begin() as conn:

        # Load dimensions and capture the IDs Postgres assigns
        data["dim_date"].to_sql(
            "dim_date", conn,
            if_exists="append", index=False
        )
        data["dim_product"].to_sql(
            "dim_product", conn,
            if_exists="append", index=False
        )
        data["dim_customer"].to_sql(
            "dim_customer", conn,
            if_exists="append", index=False
        )
        data["dim_location"].to_sql(
            "dim_location", conn,
            if_exists="append", index=False
        )

        # Read back IDs to use as foreign keys in the fact table
        dates     = pd.read_sql("SELECT date_id, full_date FROM dim_date", conn)
        products  = pd.read_sql("SELECT product_id, product_name FROM dim_product", conn)
        customers = pd.read_sql("SELECT customer_id, email FROM dim_customer", conn)
        locations = pd.read_sql("SELECT location_id, city, country FROM dim_location", conn)

        # Build fact table by joining IDs back onto raw data
        raw = data["raw"].copy()
        raw["full_date"] = raw["sale_date"].dt.date.astype(str)
        dates["full_date"] = dates["full_date"].astype(str)

        fact = raw \
            .merge(dates,     on="full_date",                           how="left") \
            .merge(products,  on="product_name",                        how="left") \
            .merge(customers, on="email",                               how="left") \
            .merge(locations, left_on=["city", "country"],
                              right_on=["city", "country"],             how="left")

        fact_sales = fact[["sale_id" if "sale_id" in fact.columns
                           else "date_id",
                           "date_id", "product_id",
                           "customer_id", "location_id",
                           "revenue", "quantity"]].copy()

        # Keep only the columns the fact table needs
        fact_sales = fact[["date_id", "product_id",
                            "customer_id", "location_id",
                            "revenue", "quantity"]]

        fact_sales.to_sql(
            "fact_sales", conn,
            if_exists="append", index=False
        )

        print(f"  fact_sales: {len(fact_sales)} rows loaded")


# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    raw_df    = extract(CSV_FILE)
    data      = transform(raw_df)
    load(data)
    print("Pipeline complete.")