from flask import Flask, render_template, request, jsonify
import os
from local_detector.detector import process_video

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["video"]
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    output_file = process_video(filepath)

    return jsonify({
        "message": "Detection complete",
        "output_video": output_file
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)