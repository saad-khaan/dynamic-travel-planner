from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import requests
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
GEODB_API_KEY = os.getenv("GEODB_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

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

# --- Weather helper ---
def get_weather(city):
    if not OPENWEATHER_API_KEY:
        print("No OpenWeather API key found.")
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            weather = {
                "city": data["name"],
                "temp": data["main"]["temp"],
                "desc": data["weather"][0]["description"].capitalize()
            }
            return weather
        else:
            print("Weather API error:", response.text)
            return None
    except Exception as e:
        print("Weather fetch failed:", e)
        return None

# --- Home route with trip saving and weather ---
@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    weather = None
    if request.method == "POST":
        city = request.form["city"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        # Save trip to database
        with sqlite3.connect("db.sqlite3") as conn:
            c = conn.cursor()
            c.execute("INSERT INTO itineraries (city, start_date, end_date) VALUES (?, ?, ?)",
                      (city, start_date, end_date))
            conn.commit()

        message = f"Trip to {city} saved!"
        weather = get_weather(city)

    return render_template("index.html", message=message, weather=weather)

# --- View saved itineraries ---
@app.route("/itineraries")
def itineraries():
    with sqlite3.connect("db.sqlite3") as conn:
        c = conn.cursor()
        c.execute("SELECT id, city, start_date, end_date FROM itineraries")
        trips = c.fetchall()
    return render_template("itineraries.html", itineraries=trips)

# --- Autocomplete route (proxy for GeoDB Cities API) ---
@app.route("/autocomplete")
def autocomplete():
    query = request.args.get("q", "")
    if not query or len(query) < 2:
        return jsonify([])

    url = f"https://wft-geo-db.p.rapidapi.com/v1/geo/cities?namePrefix={query}&limit=10"
    headers = {
        "X-RapidAPI-Key": GEODB_API_KEY,
        "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            suggestions = [city["city"] for city in data.get("data", [])]
            return jsonify(suggestions)
        else:
            return jsonify([])
    except Exception as e:
        print("Error fetching autocomplete:", e)
        return jsonify([])

# --- Run the app ---
if __name__ == "__main__":
    app.run(debug=True)