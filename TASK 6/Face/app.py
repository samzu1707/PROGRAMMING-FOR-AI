from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename
import cv2
import os

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load Haar Cascade models using OpenCV's built-in data path
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")


@app.route("/", methods=["GET", "POST"])
def index():

    result = ""
    image_filename = ""

    if request.method == "POST":

        file = request.files["image"]

        if file:

            # Secure the filename to prevent path traversal attacks
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(image_path)

            image_filename = filename

            img = cv2.imread(image_path)

            if img is None:
                result = "Error: Could not read image. Please upload a valid image file."
            else:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                if len(faces) == 0:
                    result = "No face detected. Please try another image."
                else:
                    for (x, y, w, h) in faces:

                        face = gray[y:y+h, x:x+w]
                        eyes = eye_cascade.detectMultiScale(face)

                        eye_count = len(eyes)

                        if eye_count == 2:
                            personality = "Balanced Personality"
                        elif eye_count == 1:
                            personality = "Creative Personality"
                        else:
                            personality = "Unique Personality"

                        result = f"Face Detected | Eyes: {eye_count} | Profile: {personality}"

    return render_template("index.html", result=result, image_filename=image_filename)


if __name__ == "__main__":
    app.run(debug=True)