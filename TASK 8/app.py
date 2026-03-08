from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

API_KEY = "ekrg4Adqjrw5fvd8J4kPOPObrLk8VN4w0sTo3SZS"
NASA_URL = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}"

@app.route("/")
def home():
    response = requests.get(NASA_URL)
    data = response.json()
    return render_template("index.html", data=data)

@app.route("/get_data")
def get_data():
    response = requests.get(NASA_URL)
    data = response.json()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)