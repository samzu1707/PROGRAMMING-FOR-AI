from flask import Flask, jsonify
import requests

app = Flask(__name__)

API_KEY = "ekrg4Adqjrw5fvd8J4kPOPObrLk8VN4w0sTo3SZS"

@app.route('/')
def home():
    url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        result = {
            "message": "Welcome to NASA Space Explorer API",
            "todays_picture": {
                "title": data["title"],
                "date": data["date"],
                "explanation": data["explanation"],
                "image_url": data["url"]
            },
            "available_routes": {
                "/space": "Get today's NASA space picture",
                "/planet/earth": "Get info about Earth",
                "/planet/mars": "Get info about Mars",
                "/planet/jupiter": "Get info about Jupiter"
            }
        }
        return jsonify(result)
    else:
        return jsonify({"error": "Error fetching NASA data"}), 500


@app.route('/space')
def space_picture():
    url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        result = {
            "title": data["title"],
            "date": data["date"],
            "explanation": data["explanation"],
            "image_url": data["url"]
        }
        return jsonify(result)
    else:
        return jsonify({"error": "Error fetching NASA data"}), 500


@app.route('/planet/<name>')       # BUG FIX: <n> tha, <name> kiya
def planet_info(name):
    planets = {
        "earth":   {"type": "terrestrial", "life": "yes"},
        "mars":    {"type": "terrestrial", "life": "possible"},
        "jupiter": {"type": "gas giant",   "life": "no"}
    }

    if name.lower() in planets:
        return jsonify(planets[name.lower()])
    else:
        return jsonify({"error": f"Planet '{name}' not found"}), 404


if __name__ == "__main__":
    app.run(debug=True)