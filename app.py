import os
import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# === Configure Gemini API ===
genai.configure(api_key=GOOGLE_API_KEY)

# === Prompt file ===
PROMPT_FILE = "moviesdb_prompt.txt"

# === Helper functions ===
@st.cache_data
def load_prompt_from_file(file_path):
    with open(file_path, "r") as f:
        return f.read()

def get_gemini_response(question, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([prompt, question])
    return response.text.strip()

def execute_sql_query(sql_query, db_path):
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

def save_history(prompt, query):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([[timestamp, prompt, query]], columns=["timestamp", "user_prompt", "generated_query"])
    new_entry.to_csv("history.csv", mode='a', header=not os.path.exists("history.csv"), index=False)

def load_history():
    if os.path.exists("history.csv"):
        df = pd.read_csv("history.csv")
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
        return df.sort_values("timestamp", ascending=False)
    else:
        return pd.DataFrame(columns=["timestamp", "user_prompt", "generated_query"])

def log_executed_query(nl_question, sql_query, rows):
    if "executed_queries" not in st.session_state:
        st.session_state.executed_queries = []
    st.session_state.executed_queries.append({
        "question": nl_question,
        "sql_query": sql_query,
        "rows": rows
    })

# === Streamlit UI ===
st.set_page_config(page_title="🎬 Gemini SQL Query App", layout="wide")

# === Sidebar Settings ===
with st.sidebar:
    st.header("⚙️ Settings")
    max_rows = st.slider("Max rows to display", 5, 100, 20, 5)

    uploaded_file = st.file_uploader("📤 Upload Your Movies SQLite DB", type=["sqlite", "db"])
    if uploaded_file:
        db_path = "uploaded_movies.sqlite"
        with open(db_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("✅ Custom database uploaded.")
    else:
        db_path = "sample_movies.db"
        st.info("Using default: `sample_movies.db` (place in repo)")

# === Tabs ===
tabs = st.tabs(["🧠 Ask a Question", "📜 Query History", "🗂️ Executed Queries", "🕒 All-Time History"])

# === Load prompt
prompt = load_prompt_from_file(PROMPT_FILE)

# === TAB 1: Ask a Question ===
with tabs[0]:
    st.title("🎬 Gemini SQL Data Retriever")
    st.write("Ask anything about your Movies database:")

    question = st.text_input("Your question:", placeholder="E.g., List top 5 highest rated movies")
    if st.button("Ask the question") and question.strip():
        with st.spinner("🧠 Generating SQL and fetching results..."):
            sql_query = get_gemini_response(question, prompt)
            st.subheader("📜 Generated SQL")
            st.code(sql_query, language="sql")

            df, error = execute_sql_query(sql_query, db_path)
            if error:
                st.error(f"❌ SQL Error: {error}")
            elif df.empty:
                st.warning("✅ Query successful, but no results.")
            else:
                st.success(f"✅ Showing top {min(max_rows, len(df))} rows")
                st.dataframe(df.head(max_rows), use_container_width=True)

                csv = df.head(max_rows).to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download CSV", csv, "query_results.csv", "text/csv")

                log_executed_query(question, sql_query, df.head(max_rows))
                save_history(question, sql_query)
    else:
        st.info("✍️ Type your question and click the button.")

# === TAB 2: Session Query History ===
with tabs[1]:
    st.header("📜 Query History (Session)")
    if "executed_queries" in st.session_state and st.session_state.executed_queries:
        for i, q in enumerate(reversed(st.session_state.executed_queries), 1):
            with st.expander(f"Q{i}: {q['question']}"):
                st.code(q["sql_query"], language="sql")
    else:
        st.info("No queries yet.")

# === TAB 3: Executed Queries + Results ===
with tabs[2]:
    st.header("🗂️ Executed Queries + Results")
    if "executed_queries" in st.session_state and st.session_state.executed_queries:
        for i, q in enumerate(reversed(st.session_state.executed_queries), 1):
            with st.expander(f"Q{i}: {q['question']}"):
                st.code(q["sql_query"], language="sql")
                st.dataframe(q["rows"], use_container_width=True)
    else:
        st.info("No results yet.")

# === TAB 4: All-Time History ===
with tabs[3]:
    st.header("🕒 All-Time History (from CSV)")
    history_df = load_history()
    if history_df.empty:
        st.info("No history found.")
    else:
        st.dataframe(history_df, use_container_width=True)

# === Footer ===
st.markdown("---")
st.caption("Built with ❤️ using Gemini + Streamlit")
