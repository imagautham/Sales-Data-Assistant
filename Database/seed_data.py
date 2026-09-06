import sqlite3
import random
import os
from datetime import date, datetime, timedelta
from faker import Faker
from create_schema import create_schema

DB_NAME = "sales.db"

# Categorized product names with realistic price ranges (min_price, max_price)
PRODUCT_CATALOG = {
    "Electronics": {
        "price_range": (50.0, 1500.0),
        "items": [
            "Wireless Noise-Canceling Headphones",
            "Smart 4K LED TV 55-Inch",
            "USB-C Multi-Port Fast Charging Hub",
            "Mechanical RGB Gaming Keyboard",
            "Portable Waterproof Bluetooth Speaker",
            "Smartphone 128GB OLED Display",
            "Ultra-Slim Laptop 14-Inch 16GB RAM",
            "Smartwatch Fitness & Heart-Rate Tracker",
            "External NVMe Solid State Drive 1TB",
            "Wireless Ergonomic Optical Mouse",
        ]
    },
    "Apparel": {
        "price_range": (15.0, 200.0),
        "items": [
            "Classic Organic Cotton Crewneck T-Shirt",
            "Slim-Fit Stretch Denim Jeans",
            "Waterproof Breathable Rain Jacket",
            "Fleece Full-Zip Athletic Hoodie",
            "Merino Wool Crewneck Winter Sweater",
            "Casual Linen Long-Sleeve Shirt",
            "Quick-Dry Athletic Running Shorts",
            "Thermal Base-Layer Compression Tights",
            "Insulated Lightweight Puffer Coat",
            "Tailored Wrinkle-Free Dress Shirt",
        ]
    },
    "Home": {
        "price_range": (20.0, 500.0),
        "items": [
            "10-Piece Stainless Steel Cookware Set",
            "Ergonomic Memory Foam Bed Pillow (2-Pack)",
            "Ultrasonic Aromatherapy Essential Oil Diffuser",
            "Ceramic Non-Stick Frying Pan 12-Inch",
            "Smart Robotic Vacuum Cleaner with Mapping",
            "Precision Electric Gooseneck Pour-Over Kettle",
            "100% Turkish Cotton Bath Towel 4-Piece Set",
            "LED Dimmable Architect Desk Lamp",
            "Enameled Cast Iron Dutch Oven 6-Quart",
            "True HEPA Air Purifier for Large Rooms",
        ]
    },
    "Sports": {
        "price_range": (10.0, 300.0),
        "items": [
            "Non-Slip High-Density Exercise Yoga Mat",
            "Adjustable Quick-Select Dumbbell Pair (50 lbs)",
            "Vacuum-Insulated Stainless Steel Water Bottle 32oz",
            "All-Terrain Trail Running Shoes",
            "Heavy-Duty Resistance Exercise Loop Bands",
            "Ultra-Light Carbon Fiber Trekking Poles",
            "Inflatable Stand-Up Touring Paddleboard",
            "Weatherproof 4-Person Camping Dome Tent",
            "Match Grade Pro Soccer Ball Size 5",
            "High-Speed Ball Bearing Jump Rope",
        ]
    },
    "Books": {
        "price_range": (5.0, 40.0),
        "items": [
            "Modern Data Engineering with Python & SQL",
            "Designing Data-Intensive Applications: The Definitive Guide",
            "Mastering Database Performance & Query Optimization",
            "The Clean Architecture & Domain-Driven Design",
            "System Design & Scalable Architecture Handbook",
            "Building Generative AI Applications from Scratch",
            "Cloud Native Microservices & Kubernetes Patterns",
            "Practical Statistics & Probability for Data Scientists",
            "Machine Learning in Production: MLOps Guide",
            "Deep Learning Fundamentals with PyTorch",
        ]
    }
}

REGIONS = ["North", "South", "East", "West"]

def generate_random_signup_date(fake: Faker, years: int = 3) -> str:
    """Returns a random date string (YYYY-MM-DD) over the last N years."""
    end_date = date.today()
    start_date = end_date - timedelta(days=years * 365)
    return str(fake.date_between(start_date=start_date, end_date=end_date))

def generate_seasonal_sale_date(days_back: int = 730) -> str:
    """
    Generates a random date within the last 2 years with higher density
    in November and December (seasonal holiday shopping bump).
    """
    end_date = date.today()
    
    while True:
        # Pick a random day in the range
        random_days = random.randint(0, days_back)
        candidate_date = end_date - timedelta(days=random_days)
        
        # Monthly probability weight: Nov & Dec have 2.8x higher traffic
        month = candidate_date.month
        weight = 2.8 if month in (11, 12) else 1.0
        
        # Acceptance test against maximum weight (2.8)
        if random.random() < (weight / 2.8):
            return str(candidate_date)

def seed_database(db_path: str = DB_NAME):
    """Populates the sales database with realistic customers, products, and sales."""
    # Ensure tables exist
    create_schema(db_path)

    fake = Faker()
    # Ensure reproducible yet realistic generation
    random.seed(42)
    fake.seed_instance(42)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    print(f"Connecting to database at: {db_path}")

    # Clean existing data within a transaction
    with conn:
        cursor.execute("DELETE FROM sales;")
        cursor.execute("DELETE FROM products;")
        cursor.execute("DELETE FROM customers;")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('sales', 'products', 'customers');")

        # ----------------------------------------------------
        # 1. Populate Customers (500)
        # ----------------------------------------------------
        print("Generating 500 customers...")
        customers_data = []
        generated_emails = set()

        for _ in range(500):
            name = fake.name()
            # Guarantee unique email
            email = fake.unique.email()
            while email in generated_emails:
                email = fake.email()
            generated_emails.add(email)

            region = random.choice(REGIONS)
            signup_date = generate_random_signup_date(fake, years=3)
            customers_data.append((name, email, region, signup_date))

        cursor.executemany(
            "INSERT INTO customers (name, email, region, signup_date) VALUES (?, ?, ?, ?);",
            customers_data
        )

        # ----------------------------------------------------
        # 2. Populate Products (50)
        # ----------------------------------------------------
        print("Generating 50 products...")
        products_data = []
        for category, info in PRODUCT_CATALOG.items():
            min_p, max_p = info["price_range"]
            for item_name in info["items"]:
                # Realistic pricing (e.g. .99 or rounded to 2 decimals)
                raw_price = random.uniform(min_p, max_p)
                unit_price = round(raw_price, 2)
                products_data.append((item_name, category, unit_price))

        cursor.executemany(
            "INSERT INTO products (name, category, unit_price) VALUES (?, ?, ?);",
            products_data
        )

        # Retrieve created customer IDs and product IDs with unit prices
        cursor.execute("SELECT customer_id FROM customers;")
        customer_ids = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT product_id, unit_price FROM products;")
        product_rows = cursor.fetchall()  # list of (product_id, unit_price)
        product_ids = [row[0] for row in product_rows]
        product_price_map = {row[0]: row[1] for row in product_rows}

        # ----------------------------------------------------
        # 3. Populate Sales (10,000) with skewed product distribution
        # ----------------------------------------------------
        print("Generating 10,000 sales records with skewed distribution and seasonality...")

        # Weighting: 20% of products (10 products) account for ~60% of sales
        # Remaining 80% (40 products) account for ~40% of sales
        num_products = len(product_ids)
        top_count = int(num_products * 0.20)  # 10 products
        rest_count = num_products - top_count # 40 products

        top_weight_per_item = 0.60 / top_count
        rest_weight_per_item = 0.40 / rest_count

        product_weights = (
            [top_weight_per_item] * top_count +
            [rest_weight_per_item] * rest_count
        )

        sales_data = []
        for _ in range(10000):
            customer_id = random.choice(customer_ids)
            product_id = random.choices(product_ids, weights=product_weights, k=1)[0]
            quantity = random.randint(1, 10)
            sale_date = generate_seasonal_sale_date(days_back=730)
            unit_price = product_price_map[product_id]
            total_amount = round(quantity * unit_price, 2)

            sales_data.append((customer_id, product_id, quantity, sale_date, total_amount))

        cursor.executemany(
            "INSERT INTO sales (customer_id, product_id, quantity, sale_date, total_amount) VALUES (?, ?, ?, ?, ?);",
            sales_data
        )

    # ----------------------------------------------------
    # Summary of row counts
    # ----------------------------------------------------
    print("\n================ ROW COUNT SUMMARY ================")
    for table in ["customers", "products", "sales"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"Table '{table}': {count:,} rows")
    print("===================================================\n")

    conn.close()

if __name__ == "__main__":
    db_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    seed_database(db_file_path)
