from flask import Flask, render_template, request
import sqlite3
import os

app = Flask(__name__)

# --- Initialize Database ---
def init_db():
    if not os.path.exists('db.sqlite3'):
        with sqlite3.connect('db.sqlite3') as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE itineraries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL
                )
            ''')
            conn.commit()

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    if request.method == "POST":
        city = request.form["city"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        with sqlite3.connect("db.sqlite3") as conn:
            c = conn.cursor()
            c.execute("INSERT INTO itineraries (city, start_date, end_date) VALUES (?, ?, ?)",
                      (city, start_date, end_date))
            conn.commit()

        message = f"✅ Trip to {city} saved!"

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)