"""Forwards sensor messages from the MQTT broker to the HTTP API (fictional sample)."""

import json
import os

import paho.mqtt.client as mqtt
import requests

API = os.environ.get("SPROUT_API", "http://127.0.0.1:8080/api/v1/readings")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except ValueError:
        return
    requests.post(API, json=payload, timeout=5)


def main():
    client = mqtt.Client(client_id="sprout-bridge")
    client.on_message = on_message
    client.tls_set()
    client.connect(os.environ.get("SPROUT_BROKER", "mqtt.mossbyte.example"), 8883)
    client.subscribe("sprout/+/readings", qos=1)
    client.loop_forever()


if __name__ == "__main__":
    main()
