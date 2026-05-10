from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum, countDistinct, desc

spark = SparkSession.builder.appName("CustomerAnalysis").getOrCreate()

df = spark.read.csv("customers_large.csv", header=True, inferSchema=True)

print("=== Total Revenue by Country ===")
df.groupBy("country").agg(sum("revenue").alias("total_revenue")) \
  .orderBy(desc("total_revenue")).show(truncate=False)

print("=== Top 3 Best-Selling Products ===")
df.groupBy("product_name").agg(sum("revenue").alias("total_revenue")) \
  .orderBy(desc("total_revenue")).limit(3).show(truncate=False)

print("=== Corporate Customers with Revenue > $500 ===")
df.filter((col("segment") == "Corporate") & (col("revenue") > 500)).show(truncate=False)

print("=== Unique Customers per City ===")
df.groupBy("city").agg(countDistinct("customer_id").alias("unique_customers")) \
  .orderBy(desc("unique_customers")).show(truncate=False)

spark.stop()
