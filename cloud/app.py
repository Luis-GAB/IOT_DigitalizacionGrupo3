import json
import subprocess
import threading
from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime, timedelta

from awsiot import mqtt5_client_builder
from awscrt import mqtt5

app = Flask(__name__)

connection_success_event = threading.Event()
stopped_event = threading.Event()
endpoint_AWS="a2xyhr7rc9cefs-ats.iot.us-east-1.amazonaws.com"
cert_filepath_AWS="cert/Control.cert.pem"
pri_key_filepath_AWS="cert/Control.private.key"
clientId_AWS="Control"
message_topic_commands_AWS="command"
client = None
iot_connected = False
TIMEOUT_CONNECT_AWS = 100


def conectar_a_aws():
    global client, iot_connected

    print("==== Creating MQTT5 Client ====\n")
    client = mqtt5_client_builder.mtls_from_path(
        endpoint=endpoint_AWS,
        cert_filepath=cert_filepath_AWS,
        pri_key_filepath=pri_key_filepath_AWS,
        on_publish_received=on_publish_received_AWS,
        on_lifecycle_stopped=on_lifecycle_stopped_AWS,
        on_lifecycle_attempting_connect=on_lifecycle_attempting_connect_AWS,
        on_lifecycle_connection_success=on_lifecycle_connection_success_AWS,
        on_lifecycle_connection_failure=on_lifecycle_connection_failure_AWS,
        on_lifecycle_disconnection=on_lifecycle_disconnection_AWS,
        client_id=clientId_AWS)

    print("==== Starting client ====")
    client.start()

    if not connection_success_event.wait(TIMEOUT_CONNECT_AWS):
        raise TimeoutError("Connection timeout")

    iot_connected = True


def on_publish_received_AWS(publish_packet_data):
    publish_packet = publish_packet_data.publish_packet
    print("==== Received message from topic '{}': {} ====\n".format(
        publish_packet.topic, publish_packet.payload.decode('utf-8')))


def on_lifecycle_stopped_AWS(lifecycle_stopped_data):
    print("Lifecycle Stopped\n")
    stopped_event.set()


def on_lifecycle_attempting_connect_AWS(lifecycle_attempting_connect_data):
    print("Lifecycle Connection Attempt\n")


def on_lifecycle_connection_success_AWS(lifecycle_connect_success_data):
    connack_packet = lifecycle_connect_success_data.connack_packet
    print("Lifecycle Connection Success with reason code:{}\n".format(
        repr(connack_packet.reason_code)))
    connection_success_event.set()


def on_lifecycle_connection_failure_AWS(lifecycle_connection_failure):
    print("Lifecycle Connection Failure with exception:{}".format(
        lifecycle_connection_failure.exception))


def on_lifecycle_disconnection_AWS(lifecycle_disconnect_data):
    print("Lifecycle Disconnected with reason code:{}".format(
        lifecycle_disconnect_data.disconnect_packet.reason_code if lifecycle_disconnect_data.disconnect_packet else "None"))


def publicar_mqtt(command_dict):
    if not iot_connected:
        print("ERROR: Not connected to AWS IoT Core")
        return False
    final_message = json.dumps(command_dict)
    print(f"Publishing to '{message_topic_commands_AWS}': {final_message}")
    publish_future = client.publish(
        mqtt5.PublishPacket(
            topic=message_topic_commands_AWS,
            payload=final_message,
            qos=mqtt5.QoS.AT_LEAST_ONCE
        )
    )
    publish_completion_data = publish_future.result(TIMEOUT_CONNECT_AWS)
    print("PubAck received with {}\n".format(repr(publish_completion_data.puback.reason_code)))
    return True


def obtener_ultimo_estado_luces(items, selected_house):
    latest_ts = 0
    lights_state = {}

    for item in items:
        if item["house"]["S"] != selected_house:
            continue
        payload = item.get("payload", {}).get("M", {})
        ts_str = payload.get("timestamp", {}).get("N")
        if not ts_str:
            continue
        ts = int(ts_str)
        if ts > latest_ts:
            latest_ts = ts
            lights_state = {
                "led_rojo": payload.get("led_rojo", {}).get("S", "OFF"),
                "led_verde": payload.get("led_verde", {}).get("S", "OFF"),
                "led_amarillo": payload.get("led_amarillo", {}).get("S", "OFF"),
                "led_puerta": payload.get("led_puerta", {}).get("S", "OFF"),
                "rgb_red": payload.get("rgb_red", {}).get("S", "0"),
                "rgb_green": payload.get("rgb_green", {}).get("S", "0"),
                "rgb_blue": payload.get("rgb_blue", {}).get("S", "0"),
            }

    return lights_state


@app.route("/")
def index():
    try:
        with open("../datos.json") as f:
            data = json.load(f)
        items = data["Items"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return render_template(
            "index.html",
            houses=[], selected_house=None, lights_state={}
        )

    houses = sorted(set(item["house"]["S"] for item in items))

    if houses:
        selected_house = request.args.get("house", houses[0])
    else:
        selected_house = None

    if not houses:
        return render_template(
            "index.html",
            houses=[], selected_house=None, lights_state={}
        )

    lights_state = obtener_ultimo_estado_luces(items, selected_house)

    return render_template(
        "index.html",
        houses=houses,
        selected_house=selected_house,
        lights_state=lights_state
    )


@app.route("/luz", methods=["POST"])
def control_luz():
    house = request.form.get("house")
    light_type = request.form.get("light_type")
    action = request.form.get("action")

    if not house or not light_type or not action:
        return jsonify({"status": "error", "message": "Faltan parametros"}), 400

    command = {
        "house": house,
        "device": "light",
        "light_type": light_type,
        "action": action
    }

    if light_type == "rgb":
        command["red"] = int(request.form.get("red", 0))
        command["green"] = int(request.form.get("green", 0))
        command["blue"] = int(request.form.get("blue", 0))

    success = publicar_mqtt(command)
    return jsonify({"status": "success" if success else "error", "command": command})


@app.route("/luces", methods=["POST"])
def control_luces():
    house = request.form.get("house")
    action = request.form.get("action")

    if not house or not action:
        return jsonify({"status": "error", "message": "Faltan parametros"}), 400

    command = {
        "house": house,
        "device": "lights",
        "action": action
    }

    success = publicar_mqtt(command)
    return jsonify({"status": "success" if success else "error", "command": command})


@app.route("/refresh")
def actualizar():
    print("Actualizando datos")
    house = request.args.get("house", "")

    now = datetime.now()
    start_of_day = datetime(now.year, now.month, now.day)
    end_of_day = start_of_day + timedelta(days=1)
    start_ts = int(start_of_day.timestamp())
    end_ts = int(end_of_day.timestamp())

    command = f"""aws dynamodb scan \
    --table-name telemetry \
    --filter-expression "#ts BETWEEN :start AND :end" \
    --expression-attribute-names '{{"#ts":"timestamp"}}' \
    --expression-attribute-values '{{":start":{{"N":"{start_ts}"}},":end":{{"N":"{end_ts}"}}}}' \
    --output json > ../datos.json"""

    print("Comando ejecutado:")
    print(command)
    subprocess.run(command, shell=True)

    return redirect(url_for("index", house=house))


if __name__ == "__main__":
    try:
        conectar_a_aws()
        print("Conectado a AWS IoT")
    except Exception as e:
        print("Error conectando IOTCore: ", str(e))

    app.run(host="0.0.0.0", port=5001)
