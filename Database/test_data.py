import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales.db")

# Configure pandas display settings for clean console output
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
pd.set_option("display.max_colwidth", 40)

def run_query(query: str, title: str = None) -> pd.DataFrame:
    """
    Executes a SQL query against sales.db and prints the formatted result.
    Returns the result as a pandas DataFrame.
    """
    if title:
        print("\n" + "=" * 80)
        print(f" {title.upper()} ".center(80, "="))
        print("=" * 80)
    
    print(f"\n[SQL Query]:\n{query.strip()}\n")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
        print(f"[Results ({len(df)} rows)]:")
        if df.empty:
            print("  (No rows returned)")
        else:
            print(df.to_string(index=False))
        return df
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"Connected to SQLite database: {DB_PATH}")

    # =========================================================================
    # SAMPLE QUERIES: Explore and test your data
    # =========================================================================

    # # 1. Top 5 Highest Spending Customers
    # run_query("""
    #     SELECT 
    #         c.customer_id,
    #         c.name AS customer_name,
    #         c.region,
    #         COUNT(s.sale_id) AS total_orders,
    #         SUM(s.quantity) AS total_items_bought,
    #         PRINTF('$%,.2f', SUM(s.total_amount)) AS total_spent
    #     FROM customers c
    #     JOIN sales s ON c.customer_id = s.customer_id
    #     GROUP BY c.customer_id
    #     ORDER BY SUM(s.total_amount) DESC
    #     LIMIT 5;
    # """, title="1. Top 5 Spending Customers")

    # # 2. Top 5 Best-Selling Products by Revenue
    # run_query("""
    #     SELECT 
    #         p.product_id,
    #         p.name AS product_name,
    #         p.category,
    #         PRINTF('$%,.2f', p.unit_price) AS unit_price,
    #         COUNT(s.sale_id) AS total_orders,
    #         SUM(s.quantity) AS total_quantity_sold,
    #         PRINTF('$%,.2f', SUM(s.total_amount)) AS total_revenue
    #     FROM products p
    #     JOIN sales s ON p.product_id = s.product_id
    #     GROUP BY p.product_id
    #     ORDER BY SUM(s.total_amount) DESC
    #     LIMIT 5;
    # """, title="2. Top 5 Best-Selling Products by Revenue")

    # # 3. Regional Sales Breakdown
    # run_query("""
    #     SELECT 
    #         c.region,
    #         COUNT(DISTINCT c.customer_id) AS customer_count,
    #         COUNT(s.sale_id) AS total_orders,
    #         SUM(s.quantity) AS total_items_sold,
    #         PRINTF('$%,.2f', AVG(s.total_amount)) AS avg_order_value,
    #         PRINTF('$%,.2f', SUM(s.total_amount)) AS total_revenue
    #     FROM customers c
    #     JOIN sales s ON c.customer_id = s.customer_id
    #     GROUP BY c.region
    #     ORDER BY SUM(s.total_amount) DESC;
    # """, title="3. Regional Sales Breakdown")

    # # 4. Monthly Revenue Trend (Showing Seasonal Spikes)
    # run_query("""
    #     SELECT 
    #         STRFTIME('%Y-%m', s.sale_date) AS sales_month,
    #         COUNT(s.sale_id) AS total_orders,
    #         SUM(s.quantity) AS total_units_sold,
    #         PRINTF('$%,.2f', SUM(s.total_amount)) AS monthly_revenue
    #     FROM sales s
    #     GROUP BY sales_month
    #     ORDER BY sales_month DESC
    #     LIMIT 12;
    # """, title="4. Monthly Sales & Revenue Trend (Last 12 Months)")

    # # 5. Full Transaction Details (JOIN of customers, products, and sales)
    # run_query("""
    #     SELECT 
    #         s.sale_id,
    #         s.sale_date,
    #         c.name AS customer_name,
    #         c.region,
    #         p.name AS product_name,
    #         p.category,
    #         s.quantity,
    #         PRINTF('$%,.2f', p.unit_price) AS unit_price,
    #         PRINTF('$%,.2f', s.total_amount) AS total_amount
    #     FROM sales s
    #     JOIN customers c ON s.customer_id = c.customer_id
    #     JOIN products p ON s.product_id = p.product_id
    #     ORDER BY s.sale_date DESC
    #     LIMIT 5;
    # """, title="5. 5 Most Recent Detailed Transactions")

    # =========================================================================
    # WRITE YOUR OWN QUERY BELOW:
    # Example:
    custom_sql = "SELECT * FROM products WHERE category = 'Books';"
    run_query(custom_sql, title="My Custom Query")
    # =========================================================================
