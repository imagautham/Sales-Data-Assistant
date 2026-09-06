import os
import sqlite3

DB_NAME = "sales.db"

def print_section_header(title: str):
    """Prints a styled section header."""
    print("\n" + "=" * 80)
    print(f" {title.upper()} ".center(80, "="))
    print("=" * 80)

def verify_database(db_path: str = DB_NAME):
    """Performs comprehensive verification and inspection of the sales database."""
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found. Please run 'create_schema.py' and 'seed_data.py' first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    tables = ["customers", "products", "sales"]

    # ----------------------------------------------------
    # 1. Row counts for each table
    # ----------------------------------------------------
    print_section_header("1. Row Counts")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"  * {table.ljust(15)} : {count:,} rows")

    # ----------------------------------------------------
    # 2. Table Schemas (PRAGMA table_info)
    # ----------------------------------------------------
    print_section_header("2. Table Schemas (PRAGMA table_info)")
    for table in tables:
        print(f"\n--- Schema for table: '{table}' ---")
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        # Header
        print(f"  {'CID':<5} {'Column Name':<20} {'Data Type':<18} {'NotNull':<10} {'Default':<10} {'PK':<5}")
        print("  " + "-" * 70)
        for col in columns:
            cid, name, col_type, notnull, dflt_val, pk = col
            print(f"  {cid:<5} {name:<20} {col_type:<18} {bool(notnull)!s:<10} {str(dflt_val):<10} {bool(pk)!s:<5}")

    # ----------------------------------------------------
    # 3. Foreign Key Relationships (PRAGMA foreign_key_list)
    # ----------------------------------------------------
    print_section_header("3. Foreign Key Relationships (PRAGMA foreign_key_list)")
    for table in tables:
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        fks = cursor.fetchall()
        print(f"\n--- Foreign Keys for table: '{table}' ---")
        if not fks:
            print("  (No foreign keys defined)")
        else:
            print(f"  {'ID':<5} {'From Column':<18} {'Referenced Table':<20} {'To Column':<18} {'On Update/Delete':<20}")
            print("  " + "-" * 82)
            for fk in fks:
                fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                action = f"{on_update}/{on_delete}"
                print(f"  {fk_id:<5} {from_col:<18} {ref_table:<20} {to_col:<18} {action:<20}")

    # ----------------------------------------------------
    # 4. Sample Rows (5 per table)
    # ----------------------------------------------------
    print_section_header("4. Sample Rows (5 per table)")
    for table in tables:
        print(f"\n--- Sample from table: '{table}' (first 5 rows) ---")
        cursor.execute(f"SELECT * FROM {table} LIMIT 5;")
        col_names = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        # Compute column widths
        widths = [max(len(col_names[i]), max(len(str(r[i])) for r in rows) if rows else 0) for i in range(len(col_names))]
        
        # Print table header
        header_str = " | ".join(col_names[i].ljust(widths[i]) for i in range(len(col_names)))
        separator_str = "-+-".join("-" * widths[i] for i in range(len(col_names)))
        print("  " + header_str)
        print("  " + separator_str)
        for r in rows:
            row_str = " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(r)))
            print("  " + row_str)

    # ----------------------------------------------------
    # 5. Sanity Check: Total Revenue by Category
    # ----------------------------------------------------
    print_section_header("5. Sanity Check: Total Revenue by Category")
    cursor.execute("""
        SELECT 
            p.category,
            COUNT(s.sale_id) AS total_sales_count,
            SUM(s.quantity) AS total_units_sold,
            ROUND(AVG(s.total_amount), 2) AS avg_order_value,
            ROUND(SUM(s.total_amount), 2) AS total_revenue
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.category
        ORDER BY total_revenue DESC;
    """)
    category_summary = cursor.fetchall()

    print(f"  {'Category':<15} {'Total Orders':<15} {'Units Sold':<15} {'Avg Order ($)':<15} {'Total Revenue ($)':<18}")
    print("  " + "-" * 78)
    for cat, order_cnt, units, avg_val, rev in category_summary:
        print(f"  {cat:<15} {order_cnt:<15,d} {units:<15,d} ${avg_val:<14,.2f} ${rev:<17,.2f}")

    # ----------------------------------------------------
    # 6. Orphaned Rows Check
    # ----------------------------------------------------
    print_section_header("6. Orphaned Rows & Integrity Verification")

    # Check PRAGMA foreign_key_check
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()

    # Explicit check for orphaned customer_ids in sales
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sales s 
        LEFT JOIN customers c ON s.customer_id = c.customer_id 
        WHERE c.customer_id IS NULL;
    """)
    orphaned_customers = cursor.fetchone()[0]

    # Explicit check for orphaned product_ids in sales
    cursor.execute("""
        SELECT COUNT(*) 
        FROM sales s 
        LEFT JOIN products p ON s.product_id = p.product_id 
        WHERE p.product_id IS NULL;
    """)
    orphaned_products = cursor.fetchone()[0]

    print(f"  * Orphaned customer_id references in 'sales' : {orphaned_customers}")
    print(f"  * Orphaned product_id references in 'sales'  : {orphaned_products}")
    print(f"  * PRAGMA foreign_key_check violations        : {len(fk_violations)}")

    if orphaned_customers == 0 and orphaned_products == 0 and len(fk_violations) == 0:
        print("\n  [PASS] All foreign key relationships are valid. No orphaned records found.")
    else:
        print("\n  [FAIL] Foreign key integrity violations detected!")

    print("=" * 80 + "\n")
    conn.close()

if __name__ == "__main__":
    db_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    verify_database(db_file_path)
