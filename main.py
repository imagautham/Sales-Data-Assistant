import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from get_schema import get_schema_string
import streamlit as st

# 1. Load environment variables (.env) and OpenAI client
load_dotenv()
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 2. Load the database schema
schema = get_schema_string()

# Database path (checks Database/sales.db or sales.db)
db_path = "Database/sales.db" if os.path.exists("Database/sales.db") else "sales.db"

def generate_sql(user_question: str) -> str:
    """Sends schema and question to OpenAI to generate a SQLite query."""
    prompt = f"""
Given the following database schema:
{schema}

Write a SQLite SQL query to answer this question:
{user_question}

Return ONLY the raw SQL query without any markdown code blocks or explanations.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    sql_query = response.choices[0].message.content.strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    return sql_query

def execute_sql(sql_query: str) -> pd.DataFrame:
    """Executes a SQL query against the SQLite database and returns a DataFrame."""
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql_query, conn)
        return df
    finally:
        conn.close()

if __name__ == "__main__":
    while True:
        user_question = input("\nEnter your question (or type 'EXIT' to stop): ").strip()

        if user_question.upper() in ("EXIT", "STOP"):
            print("Goodbye!")
            break

        if not user_question:
            continue

        try:
            sql_query = generate_sql(user_question)
            print("\n--- Generated SQL Query ---")
            print(sql_query)

            df = execute_sql(sql_query)
            print("\n--- Results ---")
            print(df.to_string(index=False))
        except Exception as e:
            print(f"Error: {e}")
