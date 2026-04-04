from flask import Flask, render_template, Response, jsonify, request, send_file
from detector import ObjectDetector
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

detector = ObjectDetector()


@app.route("/")
def index():
    return render_template("index.html")


# 🎥 VIDEO FEED
@app.route("/video_feed")
def video_feed():
    return Response(
        detector.get_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ▶ START LAPTOP CAMERA
@app.route("/start_camera", methods=["POST"])
def start_camera():
    detector.set_source(0)
    return jsonify({"status": "Laptop webcam started"})


# 📱 CONNECT MOBILE IP CAMERA
@app.route("/connect_ip", methods=["POST"])
def connect_ip():
    data = request.get_json()
    ip_link = data.get("ip_link")

    if not ip_link:
        return jsonify({"error": "No IP link provided"}), 400

    detector.set_source(ip_link)
    return jsonify({"status": "IP camera connected"})


# 📹 CONNECT RTSP CCTV
@app.route("/connect_rtsp", methods=["POST"])
def connect_rtsp():
    data = request.get_json()
    rtsp_link = data.get("rtsp_link")

    if not rtsp_link:
        return jsonify({"error": "No RTSP link provided"}), 400

    detector.set_source(rtsp_link)
    return jsonify({"status": "RTSP camera connected"})


# 🎞 UPLOAD VIDEO
@app.route("/upload_video", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["video"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    detector.set_source(filepath)
    return jsonify({"status": "Video uploaded"})


# 📋 LIVE DETECTIONS
@app.route("/detections")
def detections():
    return jsonify(detector.detections[-50:])


# 🔔 TOGGLE ALARM
@app.route("/toggle_alarm", methods=["POST"])
def toggle_alarm():
    data = request.get_json()
    detector.alarm_enabled = data.get("alarm", True)
    return jsonify({"alarm": detector.alarm_enabled})


# ⏹ STOP CAMERA
@app.route("/stop", methods=["POST"])
def stop():
    detector.stop()
    return jsonify({"status": "Stopped"})


# ⬇ DOWNLOAD LOG
@app.route("/download_log")
def download_log():
    return send_file(detector.log_file, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)