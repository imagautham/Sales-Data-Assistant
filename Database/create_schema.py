import sqlite3
import os

DB_NAME = "sales.db"

def create_schema(db_path: str = DB_NAME):
    """Creates the SQLite database and initializes the tables with foreign key constraints."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON;")

    tables = {
        "customers": """
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                region TEXT NOT NULL,
                signup_date DATE NOT NULL
            );
        """,
        "products": """
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL
            );
        """,
        "sales": """
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                sale_date DATE NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );
        """
    }

    print(f"Connected to database: {db_path}")

    for table_name, create_sql in tables.items():
        cursor.execute(create_sql)
        print(f"Table '{table_name}' created successfully.")

    conn.commit()
    conn.close()
    print("Schema creation completed successfully.")

if __name__ == "__main__":
    db_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    create_schema(db_file_path)
