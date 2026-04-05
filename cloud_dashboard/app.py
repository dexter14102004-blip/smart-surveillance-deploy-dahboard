from flask import Flask, request, jsonify, render_template
from datetime import datetime

app = Flask(__name__)
alerts = []

@app.route("/")
def home():
    return render_template("index.html", alerts=alerts)

@app.route("/alert", methods=["POST"])
def alert():
    data = request.json

    alerts.insert(0, {
        "object": data["object"],
        "confidence": round(float(data["confidence"]), 2),
        "time": datetime.now().strftime("%H:%M:%S")
    })

    return jsonify({"status": "success"})

@app.route("/api/alerts")
def get_alerts():
    return jsonify(alerts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)