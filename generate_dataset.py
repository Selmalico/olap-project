"""
Generate a synthetic Global Retail Sales dataset (10,000 transactions).
Covers Jan 2022 - Dec 2024 across regions, categories, and customer segments.
Run: python generate_dataset.py
"""

import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

REGIONS = {
    "North America": ["USA", "Canada", "Mexico"],
    "Europe": ["UK", "Germany", "France", "Spain", "Italy"],
    "Asia Pacific": ["Japan", "China", "Australia", "India", "South Korea"],
    "Latin America": ["Brazil", "Argentina", "Colombia", "Chile"],
}

PRODUCTS = {
    "Electronics": {
        "subcategories": ["Phones", "Laptops", "Tablets", "Accessories", "Audio"],
        "price_range": (50, 1500),
        "cost_ratio": (0.55, 0.75),
    },
    "Furniture": {
        "subcategories": ["Chairs", "Desks", "Shelving", "Tables", "Storage"],
        "price_range": (30, 800),
        "cost_ratio": (0.40, 0.60),
    },
    "Office Supplies": {
        "subcategories": ["Paper", "Binders", "Pens", "Organizers", "Labels"],
        "price_range": (5, 100),
        "cost_ratio": (0.35, 0.55),
    },
    "Clothing": {
        "subcategories": ["Men's Wear", "Women's Wear", "Accessories", "Footwear", "Sportswear"],
        "price_range": (15, 300),
        "cost_ratio": (0.40, 0.65),
    },
}

CUSTOMER_SEGMENTS = ["Consumer", "Corporate", "Home Office", "Small Business"]

# Seasonal weights per month (index 0 = Jan)
MONTH_WEIGHTS = [0.07, 0.06, 0.08, 0.08, 0.08, 0.09, 0.08, 0.08, 0.09, 0.09, 0.10, 0.11]


def weighted_date(start: datetime, end: datetime) -> datetime:
    """Pick a random date with month-based seasonal weighting."""
    total_days = (end - start).days
    candidate = start + timedelta(days=random.randint(0, total_days))
    month_idx = candidate.month - 1
    if random.random() > MONTH_WEIGHTS[month_idx] * 8:
        candidate = start + timedelta(days=random.randint(0, total_days))
    return candidate


def generate_dataset(n: int = 10_000, output_path: str = "data/sales_data.csv") -> pd.DataFrame:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    start_date = datetime(2022, 1, 1)
    end_date = datetime(2024, 12, 31)

    records = []
    for i in range(n):
        order_date = weighted_date(start_date, end_date)
        year = order_date.year
        quarter = (order_date.month - 1) // 3 + 1
        month = order_date.month
        month_name = order_date.strftime("%B")

        region = random.choice(list(REGIONS.keys()))
        country = random.choice(REGIONS[region])

        category = random.choice(list(PRODUCTS.keys()))
        product_info = PRODUCTS[category]
        subcategory = random.choice(product_info["subcategories"])
        min_price, max_price = product_info["price_range"]
        unit_price = round(random.uniform(min_price, max_price), 2)

        customer_segment = random.choice(CUSTOMER_SEGMENTS)

        quantity = random.randint(1, 50)
        revenue = round(unit_price * quantity, 2)

        min_cost_r, max_cost_r = product_info["cost_ratio"]
        cost_ratio = random.uniform(min_cost_r, max_cost_r)
        cost = round(revenue * cost_ratio, 2)
        profit = round(revenue - cost, 2)
        profit_margin = round((profit / revenue) * 100, 2) if revenue > 0 else 0.0

        records.append(
            {
                "order_id": f"ORD-{i + 1:05d}",
                "order_date": order_date.strftime("%Y-%m-%d"),
                "year": year,
                "quarter": quarter,
                "month": month,
                "month_name": month_name,
                "region": region,
                "country": country,
                "category": category,
                "subcategory": subcategory,
                "customer_segment": customer_segment,
                "quantity": quantity,
                "unit_price": unit_price,
                "revenue": revenue,
                "cost": cost,
                "profit": profit,
                "profit_margin": profit_margin,
            }
        )

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"✓ Generated {n:,} records → {output_path}")
    print(f"  Years: {df['year'].min()} – {df['year'].max()}")
    print(f"  Total revenue: ${df['revenue'].sum():,.2f}")
    print(f"  Total profit:  ${df['profit'].sum():,.2f}")
    print(f"  Avg margin:    {df['profit_margin'].mean():.1f}%")
    return df


if __name__ == "__main__":
    df = generate_dataset()
