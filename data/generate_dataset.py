import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random, os

random.seed(42)
np.random.seed(42)

REGIONS = {
    "North America": ["USA", "Canada", "Mexico"],
    "Europe": ["Germany", "France", "UK", "Italy", "Spain"],
    "Asia Pacific": ["Japan", "Australia", "Singapore", "India"],
    "Latin America": ["Brazil", "Argentina", "Colombia"]
}

PRODUCTS = {
    "Electronics": ["Laptops", "Smartphones", "Tablets", "Accessories"],
    "Furniture": ["Chairs", "Desks", "Shelving", "Lighting"],
    "Office Supplies": ["Paper", "Pens", "Binders", "Storage"],
    "Clothing": ["Tops", "Bottoms", "Outerwear", "Footwear"]
}

SEGMENTS = ["Consumer", "Corporate", "Home Office"]

rows = []
start = datetime(2022, 1, 1)

for i in range(10000):
    date = start + timedelta(days=random.randint(0, 1094))
    region = random.choice(list(REGIONS.keys()))
    country = random.choice(REGIONS[region])
    category = random.choice(list(PRODUCTS.keys()))
    subcategory = random.choice(PRODUCTS[category])
    segment = random.choice(SEGMENTS)
    qty = random.randint(1, 20)
    price = round(random.uniform(10, 2000), 2)
    revenue = round(qty * price, 2)
    cost = round(revenue * random.uniform(0.4, 0.75), 2)
    profit = round(revenue - cost, 2)

    rows.append({
        "order_id": f"ORD-{i+1:05d}",
        "order_date": date.strftime("%Y-%m-%d"),
        "year": date.year,
        "quarter": f"Q{(date.month-1)//3+1}",
        "month": date.month,
        "month_name": date.strftime("%B"),
        "week": date.isocalendar()[1],
        "region": region,
        "country": country,
        "category": category,
        "subcategory": subcategory,
        "customer_segment": segment,
        "quantity": qty,
        "unit_price": price,
        "revenue": revenue,
        "cost": cost,
        "profit": profit,
        "profit_margin": round(profit / revenue * 100, 2)
    })

df = pd.DataFrame(rows)
script_dir = os.path.dirname(os.path.abspath(__file__))
raw_dir = os.path.join(script_dir, "raw")
os.makedirs(raw_dir, exist_ok=True)
df.to_csv(os.path.join(raw_dir, "global_retail_sales.csv"), index=False)
# Backend star-schema loader expects integer quarter and sales_data.csv
df_sales = df.copy()
df_sales["quarter"] = df_sales["month"].apply(lambda m: (m - 1) // 3 + 1)
sales_path = os.path.join(script_dir, "sales_data.csv")
df_sales.to_csv(sales_path, index=False)
print(f"Generated {len(df)} rows -> {raw_dir}/global_retail_sales.csv, {sales_path}")
