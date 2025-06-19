import streamlit as st
import sqlite3
import pandas as pd
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv

# === Load environment ===
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    st.error("❌ GOOGLE_API_KEY not found. Please check your .env file.")
    st.stop()

# === Configure Gemini ===
genai.configure(api_key=GOOGLE_API_KEY)

# === Helper Functions ===
@st.cache_data
def load_prompt_from_file(file_path):
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception as e:
        st.error(f"⚠️ Prompt file load error: {e}")
        return ""

def get_gemini_response(question, prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        with st.spinner("🧠 Thinking with Gemini..."):
            response = model.generate_content([prompt, question])
        return response.text.strip()
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return ""

def execute_sql_query(sql_query, db_path):
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

def save_history(prompt, query):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = pd.DataFrame([[timestamp, prompt, query]], columns=["timestamp", "user_prompt", "generated_query"])
        new_entry.to_csv("history1.csv", mode='a', header=not os.path.exists("history1.csv"), index=False)
    except Exception as e:
        st.warning(f"⚠️ Could not save history: {e}")

def load_history():
    try:
        if os.path.exists("history1.csv"):
            df = pd.read_csv("history1.csv")
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors='coerce')
            return df.sort_values("timestamp", ascending=False)
        else:
            return pd.DataFrame(columns=["timestamp", "user_prompt", "generated_query"])
    except Exception as e:
        st.warning(f"⚠️ Failed to load history: {e}")
        return pd.DataFrame()

def log_executed_query(nl_question, sql_query, rows):
    if "executed_queries" not in st.session_state:
        st.session_state.executed_queries = []
    st.session_state.executed_queries.append({
        "question": nl_question,
        "sql_query": sql_query,
        "rows": rows
    })

# === Streamlit UI ===
st.set_page_config(page_title="🧠 Gemini SQL App", layout="wide")
st.title("🧠 Gemini-Powered SQL Query Generator")
st.markdown("Ask natural language questions about your uploaded SQLite database and get instant SQL + results!")

# === Sidebar ===
with st.sidebar:
    st.header("⚙️ Settings")
    max_rows = st.slider("Max rows to display", 5, 100, 20, 5)
    uploaded_db = st.file_uploader("📂 Upload SQLite DB File (.db)", type=["db"])
    if uploaded_db:
        db_path = f"temp_uploaded_{uploaded_db.name}"
        with open(db_path, "wb") as f:
            f.write(uploaded_db.read())
    else:
        db_path = None
        st.warning("Please upload a valid SQLite `.db` file to continue.")
        st.stop()

# === Load Prompt ===
prompt = load_prompt_from_file("moviesdb_prompt.txt")
if not prompt:
    st.stop()

# === Tabs UI ===
tabs = st.tabs(["🧠 Ask Question", "📜 History", "🗂️ Executed", "🕒 Full History"])

# === TAB 1: Ask Question ===
with tabs[0]:
    st.subheader("🧠 Ask a question about your data")
    question = st.text_input("Enter your question (e.g., Top 5 directors with most movies)")

    if st.button("🔎 Run Query") and question.strip():
        sql_query = get_gemini_response(question, prompt)
        if sql_query:
            st.code(sql_query, language="sql")
            df, error = execute_sql_query(sql_query, db_path)

            if error:
                st.error(f"❌ SQL error: {error}")
            elif df.empty:
                st.warning("✅ Query ran successfully but returned no results.")
            else:
                st.success(f"✅ Query Success: Showing {min(max_rows, len(df))} rows")
                st.dataframe(df.head(max_rows), use_container_width=True)

                # Log & Export
                log_executed_query(question, sql_query, df.head(max_rows))
                save_history(question, sql_query)

                csv = df.head(max_rows).to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download CSV", csv, "query_results.csv", "text/csv")
        else:
            st.warning("⚠️ Gemini failed to generate SQL.")

# === TAB 2: Session History ===
with tabs[1]:
    st.header("📜 Query History (Current Session)")
    if "executed_queries" in st.session_state:
        for i, q in enumerate(reversed(st.session_state.executed_queries), 1):
            with st.expander(f"Q{i}: {q['question']}"):
                st.code(q["sql_query"], language="sql")
    else:
        st.info("No queries run yet.")

# === TAB 3: Executed Queries with Results ===
with tabs[2]:
    st.header("🗂️ Executed Queries + Data")
    if "executed_queries" in st.session_state:
        for i, q in enumerate(reversed(st.session_state.executed_queries), 1):
            with st.expander(f"Q{i}: {q['question']}"):
                st.code(q["sql_query"], language="sql")
                st.dataframe(q["rows"], use_container_width=True)
    else:
        st.info("No queries run yet.")

# === TAB 4: Full History CSV ===
with tabs[3]:
    st.header("🕒 All-Time Query History")
    history_df = load_history()
    if history_df.empty:
        st.info("No saved history yet.")
    else:
        st.dataframe(history_df, use_container_width=True)

st.markdown("---")
st.caption("Built with ❤️ using Streamlit + Gemini + SQLite")
