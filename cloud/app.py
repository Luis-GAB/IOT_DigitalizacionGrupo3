import json
import subprocess
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():

    with open("../datos.json") as f:
        data = json.load(f)

    items = data["Items"]

    # Obtener lista de casas únicas
    houses = list(set(item["house"]["S"] for item in items))

    # Casa seleccionada (por defecto la primera)
    selected_house = request.args.get("house", houses[0])

    timestamps = []
    temperature = []
    humidity = []
    distance = []

    for item in items:

        if item["house"]["S"] != selected_house:
            continue

        payload = item["payload"]["M"]

        ts = int(payload["timestamp"]["N"])
        timestamps.append(datetime.fromtimestamp(ts).strftime("%H:%M:%S"))

        temp = float(payload["temperature"]["S"].replace("C",""))
        temperature.append(temp)

        hum = float(payload["humidity"]["S"].replace("%",""))
        humidity.append(hum)

        dist = float(payload["distance"]["S"].replace(" cm",""))
        distance.append(dist)

    return render_template(
        "index.html",
        timestamps=timestamps,
        temperature=temperature,
        humidity=humidity,
        distance=distance,
        houses=houses,
        selected_house=selected_house
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)