"""Minimal Flask API for the fictional Sprout S1 plant sensor.

Sensors post soil-moisture and light readings. When a plant is too dry, the
backend sends a push alert through a webhook. This is a small but real
project so that the SBOM and vulnerability tools have something to scan.
"""

import os
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, request

load_dotenv()

app = Flask(__name__)
ALERT_WEBHOOK = os.environ.get("SPROUT_ALERT_WEBHOOK", "")
DRY_THRESHOLD = float(os.environ.get("SPROUT_DRY_THRESHOLD", "18.0"))
READINGS: list[dict] = []


@app.get("/health")
def health():
    return jsonify(status="ok", time=datetime.now(timezone.utc).isoformat())


@app.post("/api/v1/readings")
def add_reading():
    data = request.get_json(silent=True) or {}
    try:
        reading = {
            "device_id": str(data["device_id"])[:64],
            "moisture": float(data["moisture"]),
            "lux": float(data.get("lux", 0)),
            "received": datetime.now(timezone.utc).isoformat(),
        }
    except (KeyError, TypeError, ValueError):
        abort(400, "device_id and moisture are required")
    READINGS.append(reading)
    if reading["moisture"] < DRY_THRESHOLD and ALERT_WEBHOOK:
        requests.post(
            ALERT_WEBHOOK,
            json={"text": f"Plant on {reading['device_id']} needs water"},
            timeout=5,
        )
    return jsonify(reading), 201


@app.get("/api/v1/readings/<device_id>")
def list_readings(device_id: str):
    return jsonify([r for r in READINGS if r["device_id"] == device_id][-100:])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080)
