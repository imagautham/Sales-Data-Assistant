import os
import sqlite3
import pandas as pd
import streamlit as st
from get_schema import get_schema_string
from main import generate_sql, execute_sql, db_path

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sales Data Assistant",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "input_question" not in st.session_state:
    st.session_state.input_question = ""

# -----------------------------------------------------------------------------
# 3. Sidebar: Quick Stats & Schema
# -----------------------------------------------------------------------------
st.sidebar.header("Database Overview")

def get_row_counts(path: str) -> dict:
    counts = {}
    if os.path.exists(path):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        for table in ["customers", "products", "sales"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                counts[table] = cursor.fetchone()[0]
            except Exception:
                counts[table] = 0
        conn.close()
    return counts

stats = get_row_counts(db_path)

# Vertically stacked metrics so large numbers (e.g. 10,000) are never cut off
st.sidebar.metric("Customers", f"{stats.get('customers', 0):,}")
st.sidebar.metric("Products", f"{stats.get('products', 0):,}")
st.sidebar.metric("Sales", f"{stats.get('sales', 0):,}")

st.sidebar.markdown("---")

with st.sidebar.expander("Database Schema", expanded=False):
    st.code(get_schema_string(), language="text")

# -----------------------------------------------------------------------------
# 4. Main Area: Title, Subtitle & Example Buttons
# -----------------------------------------------------------------------------
st.title("Sales Data Assistant")
st.write("Ask questions in plain English about the sales database. The assistant will generate SQL, query the database, and display the results.")
st.caption("💬 You can ask questions continuously. Type **STOP** or **EXIT** when you wish to stop.")

# Example question buttons
example_questions = [
    "Top 5 customers by revenue",
    "Total sales by region",
    "Best selling product category last quarter"
]

st.write("**Example Questions:**")
cols = st.columns(len(example_questions))
for i, ex in enumerate(example_questions):
    if cols[i].button(ex, key=f"btn_{i}", use_container_width=True):
        st.session_state.input_question = ex
        st.rerun()

# Text Input
user_question = st.text_input(
    "Enter your question (or type 'STOP' to end):",
    value=st.session_state.input_question,
    placeholder="e.g. Which region had the most sales?"
)

run_button = st.button("Run Query", type="primary")

# -----------------------------------------------------------------------------
# 5. Query Execution & Output
# -----------------------------------------------------------------------------
if run_button and user_question.strip():
    query_text = user_question.strip()

    # Check if user wants to STOP
    if query_text.upper() in ("STOP", "EXIT", "QUIT"):
        st.info("🛑 **Session Stopped.** Enter a new question anytime to resume asking.")
    else:
        sql_query = None

        # Step A: Generate SQL with OpenAI
        with st.spinner("Generating SQL query..."):
            try:
                sql_query = generate_sql(query_text)
            except Exception as e:
                st.error(f"Error generating SQL from OpenAI: {e}")

        # Step B: Execute SQL and display results
        if sql_query:
            st.subheader("Generated SQL")
            st.code(sql_query, language="sql")

            try:
                df = execute_sql(sql_query)
                row_count = len(df)
                st.write(f"**Rows returned:** {row_count}")

                if df.empty:
                    st.info("No data returned for this query.")
                else:
                    st.dataframe(df, use_container_width=True)

                    # Show bar chart if numeric columns exist and rows > 1
                    numeric_cols = [
                        c for c in df.select_dtypes(include=["number"]).columns 
                        if not c.lower().endswith("_id")
                    ]
                    non_numeric_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

                    if numeric_cols and len(df) > 1:
                        st.subheader("Chart")
                        if non_numeric_cols:
                            chart_df = df.set_index(non_numeric_cols[0])[numeric_cols]
                            st.bar_chart(chart_df)
                        else:
                            st.bar_chart(df[numeric_cols])

                # Append to query history
                st.session_state.history.append({
                    "question": query_text,
                    "sql": sql_query,
                    "row_count": row_count
                })

            except Exception as e:
                st.error(f"SQL execution error: {e}")
                st.info("Please try rephrasing your question.")

# -----------------------------------------------------------------------------
# 6. Query History (Collapsible Expander, Most Recent First)
# -----------------------------------------------------------------------------
if st.session_state.history:
    st.markdown("---")
    with st.expander(f"Query History ({len(st.session_state.history)} queries)", expanded=False):
        for item in reversed(st.session_state.history):
            st.markdown(f"**Question:** {item['question']}")
            st.code(item['sql'], language="sql")
            st.caption(f"Rows returned: {item['row_count']}")
            st.markdown("---")
