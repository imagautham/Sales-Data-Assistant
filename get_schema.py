import os
import sqlite3

def find_database_path(db_name: str = "sales.db") -> str:
    """Locates the database path in the current directory or Database subfolder."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "Database", db_name),
        os.path.join(base_dir, db_name),
        db_name
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    # Default fallback
    return os.path.join(base_dir, "Database", db_name)

def get_schema_string(db_path: str = None) -> str:
    """
    Connects to the SQLite database and returns a cleanly formatted 
    schema description string suitable for LLM prompts.
    """
    if db_path is None:
        db_path = find_database_path("sales.db")

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 2. Query sqlite_master to get all non-internal tables
    cursor.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY 
            CASE 
                WHEN name = 'customers' THEN 1
                WHEN name = 'products' THEN 2
                WHEN name = 'sales' THEN 3
                ELSE 4
            END, name;
    """)
    tables = [row[0] for row in cursor.fetchall()]

    schema_blocks = []

    for table in tables:
        # 3. Get column names and data types
        cursor.execute(f"PRAGMA table_info({table});")
        columns_info = cursor.fetchall()
        
        # Format types (e.g., DECIMAL(10,2) -> DECIMAL)
        col_strings = []
        for col in columns_info:
            col_name = col[1]
            raw_type = col[2]
            clean_type = raw_type.split("(")[0].strip() if "(" in raw_type else raw_type.strip()
            col_strings.append(f"{col_name} ({clean_type})")
        
        table_lines = [
            f"Table: {table}",
            f"Columns: {', '.join(col_strings)}"
        ]

        # 4. Get foreign key relationships
        cursor.execute(f"PRAGMA foreign_key_list({table});")
        fk_info = cursor.fetchall()
        if fk_info:
            table_lines.append("Relationships:")
            # Sort by from_column name for consistent output
            fk_info.sort(key=lambda x: x[3])
            for fk in fk_info:
                # fk tuple: (id, seq, table, from, to, on_update, on_delete, match)
                ref_table = fk[2]
                from_col = fk[3]
                to_col = fk[4]
                table_lines.append(f"  - {table}.{from_col} references {ref_table}.{to_col}")

        schema_blocks.append("\n".join(table_lines))

    conn.close()

    # 5. Format output separated by double newlines
    return "\n\n".join(schema_blocks)

if __name__ == "__main__":
    schema_output = get_schema_string()
    print(schema_output)
