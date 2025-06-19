# 🎬 Gemini-Powered SQL-Data-Retriever

This is an AI-powered Streamlit web app that allows users to **upload their SQLite movie databases** and ask natural language questions. The app uses **Google Gemini (via `google-generativeai`)** to convert your questions into SQL queries and display results from your database.

> 🔍 Example:  
> *"List top 10 highest-grossing action movies released after 2010"*

---

## 🚀 Features

✅ Upload the `.db` / `.sqlite` movie database  
✅ Ask natural language questions (NLQ)  
✅ Gemini generates accurate SQL queries  
✅ Run the query, view results in a table  
✅ Download result as CSV  
✅ Track query history in session and all-time (`history1.csv`)  
✅ 4-tab layout: Ask | History | Results | Logs

---

## 🧠 Tech Stack

| Tool               | Purpose                             |
|--------------------|-------------------------------------|
| Streamlit          | Frontend Web App                    |
| SQLite             | Local DB for movie data             |
| Google Gemini API  | Converts NL → SQL                   |
| Python + Pandas    | Data handling & logic               |
| Dotenv             | Secure API Key Management           |

---

## 📂 Folder Structure
├── app.py # Main Streamlit App
├── moviesdb_prompt.txt # Gemini prompt template
├── movies.db # Fallback sample DB
├── history.csv # Auto-logged query history
├── requirements.txt # All dependencies

---
🧪 Sample DB

Use the included sample_movies.db or upload your own SQLite .db file with tables like:

- movies(title, genre, year, rating, revenue)
- directors(id, name)  
- actors(id, name)
- movie_cast(movie_id, actor_id)
- You can adjust the prompt to fit your DB structure.

✨ Sample Questions

- "Top 5 movies by rating" 
- "How many action movies were released after 2015?"
- "Which movie made the highest revenue?"
- "List all movies of Shah Rukh Khan"


---

## 📦 Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/gemini-sql-app
cd gemini-sql-app

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Gemini API key
echo "GOOGLE_API_KEY=your-api-key-here" > .env

# Run the app
streamlit run app.py





