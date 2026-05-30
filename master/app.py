import serial
import time
from flask import Flask, render_template, request, jsonify

from awsiot import mqtt5_client_builder
from awscrt import mqtt5
import threading

import json

app = Flask(__name__)

BAUD_RATE = 9600

# Detecta automaticamente el puerto del Arduino probando rutas comunes
def detectar_puerto():
    posibles = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0", "/dev/ttyUSB1"]
    for puerto in posibles:
        try:
            s = serial.Serial(puerto, BAUD_RATE, timeout=1)
            s.close()
            print(f"Arduino detectado en: {puerto}")
            return puerto
        except serial.SerialException:
            continue
    return None

SERIAL_PORT = detectar_puerto()
ser = None
if SERIAL_PORT:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
    except serial.SerialException as e:
        print(f"Error al abrir {SERIAL_PORT}: {e}")
else:
    print("Arduino no detectado. Conecta la placa por USB y reinicia el servidor.")


connection_success_event = threading.Event()
stopped_event = threading.Event()
endpoint_AWS="a2xyhr7rc9cefs-ats.iot.us-east-1.amazonaws.com"
cert_filepath_AWS="cert/Casa1.cert.pem"
pri_key_filepath_AWS="cert/Casa1.private.key"
clientId_AWS="basicPubSub"
nombre_casa="Casa1"
message_topic_commands_AWS="command"
message_topic_telemetry_AWS="telemetry"
client = None
iot_connected = False
TIMEOUT_CONNECT_AWS = 100


def conectar_a_aws():
    global client, iot_connected

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

    client.start()

    if not connection_success_event.wait(TIMEOUT_CONNECT_AWS):
        raise TimeoutError("Connection timeout")

    print("==== Subscribing to topic '{}' ====".format(message_topic_commands_AWS))
    subscribe_future = client.subscribe(subscribe_packet=mqtt5.SubscribePacket(
        subscriptions=[mqtt5.Subscription(
            topic_filter=message_topic_commands_AWS,
            qos=mqtt5.QoS.AT_LEAST_ONCE)]
    ))
    suback = subscribe_future.result(TIMEOUT_CONNECT_AWS)
    print("Suback received with reason code:{}\n".format(suback.reason_codes))

    iot_connected = True


def on_publish_received_AWS(publish_packet_data):
    publish_packet = publish_packet_data.publish_packet
    print("==== Received message from topic '{}': {} ====\n".format(
        publish_packet.topic, publish_packet.payload.decode('utf-8')))

    command = json.loads(publish_packet.payload.decode('utf-8'))
    if command.get('house') != nombre_casa:
        return

    print(f"Message for {nombre_casa}\n")

    if command.get('device') == "light":
        light_type = command.get('light_type', '')
        action = command.get('action', '')
        if light_type == "rgb":
            r = command.get('red', 0)
            g = command.get('green', 0)
            b = command.get('blue', 0)
            commandToHouse = f"rgb {r} {g} {b}"
        elif light_type == "rojo":
            commandToHouse = f"ledRojo {action}"
        elif light_type == "verde":
            commandToHouse = f"ledVerde {action}"
        elif light_type == "amarillo":
            commandToHouse = f"ledAmarillo {action}"
        elif light_type == "puerta":
            commandToHouse = f"ledPuerta {action}"
        else:
            print(f"Unknown light_type: {light_type}")
            return
        response = enviar_comando(commandToHouse)
        print(f"Response from HOUSE {response}")

    elif command.get('device') == "lights":
        action = command.get('action', '')
        commandToHouse = f"allLights {action}"
        response = enviar_comando(commandToHouse)
        print(f"Response from HOUSE {response}")


def on_lifecycle_stopped_AWS(lifecycle_stopped_data: mqtt5.LifecycleStoppedData):
    print("Lifecycle Stopped\n")
    stopped_event.set()


def on_lifecycle_attempting_connect_AWS(lifecycle_attempting_connect_data: mqtt5.LifecycleAttemptingConnectData):
    print("Lifecycle Connection Attempt\n")


def on_lifecycle_connection_success_AWS(lifecycle_connect_success_data: mqtt5.LifecycleConnectSuccessData):
    connack_packet = lifecycle_connect_success_data.connack_packet
    print("Lifecycle Connection Success with reason code:{}\n".format(
        repr(connack_packet.reason_code)))
    connection_success_event.set()


def on_lifecycle_connection_failure_AWS(lifecycle_connection_failure: mqtt5.LifecycleConnectFailureData):
    print("Lifecycle Connection Failure with exception:{}".format(
        lifecycle_connection_failure.exception))


def on_lifecycle_disconnection_AWS(lifecycle_disconnect_data: mqtt5.LifecycleDisconnectData):
    print("Lifecycle Disconnected with reason code:{}".format(
        lifecycle_disconnect_data.disconnect_packet.reason_code if lifecycle_disconnect_data.disconnect_packet else "None"))


def enviar_comando(command):
    if not ser or not ser.is_open:
        return ["Puerto serie no disponible."]

    print(f"Enviando comando: {command}")
    ser.write((command + '\n').encode('utf-8'))

    time.sleep(0.5)

    responses = []
    while ser.in_waiting > 0:
        try:
            line = ser.readline().decode('utf-8').strip()
            if line:
                responses.append(line)
        except UnicodeDecodeError:
            pass

    print(f"Respuesta recibida: {responses}")
    return responses if responses else ["Sin respuesta del dispositivo."]


# --- Web Routes ---

@app.route('/')
def index():
    return render_template(
        'index.html',
        endpoint_AWS=endpoint_AWS,
        cert_filepath_AWS=cert_filepath_AWS,
        pri_key_filepath_AWS=pri_key_filepath_AWS,
        clientId_AWS=clientId_AWS,
        nombre_casa=nombre_casa,
        message_topic_commands_AWS=message_topic_commands_AWS,
        message_topic_telemetry_AWS=message_topic_telemetry_AWS
    )


@app.route("/aws")
def aws_config():
    return render_template(
        "aws_config.html",
        title="AWS Configuration",
        endpoint_AWS=endpoint_AWS,
        cert_filepath_AWS=cert_filepath_AWS,
        pri_key_filepath_AWS=pri_key_filepath_AWS,
        clientId_AWS=clientId_AWS,
        nombre_casa=nombre_casa,
        message_topic_commands_AWS=message_topic_commands_AWS,
        message_topic_telemetry_AWS=message_topic_telemetry_AWS
    )


@app.route('/control', methods=['POST'])
def control():
    command = request.form.get('command')
    if not command:
        return jsonify({"status": "error", "message": "No command provided."}), 400

    response = enviar_comando(command)
    return jsonify({"status": "success", "command": command, "response": response})


@app.route('/luces')
def get_sensors():
    if not ser or not ser.is_open:
        return jsonify({"error": "Puerto serie no disponible."})

    ser.flushInput()
    response_lines = enviar_comando("lights")

    lights_data = {}
    for line in response_lines:
        if "Resultado: " in line:
            try:
                key_part, value_part = line.split("Resultado: ", 1)[1].split(': ', 1)
                key = key_part.strip().lower().replace(" ", "_")
                lights_data[key] = value_part.strip()
            except ValueError:
                pass

    for key in ["led_rojo", "led_verde", "led_amarillo", "led_puerta",
                "rgb_red", "rgb_green", "rgb_blue"]:
        if key not in lights_data:
            lights_data[key] = "OFF" if key.startswith("led_") else "0"

    lights_data["house"] = nombre_casa
    lights_data["timestamp"] = int(time.time())

    print(f"Parsed Lights Data: {lights_data}")
    mesage_json = json.dumps(lights_data)

    if iot_connected:
        print(f"Publishing to topic '{message_topic_telemetry_AWS}': {mesage_json}")
        publish_future = client.publish(
            mqtt5.PublishPacket(
                topic=message_topic_telemetry_AWS,
                payload=mesage_json,
                qos=mqtt5.QoS.AT_LEAST_ONCE
            )
        )
        publish_completion_data = publish_future.result(TIMEOUT_CONNECT_AWS)
        print("PubAck received with {}\n".format(repr(publish_completion_data.puback.reason_code)))

    return jsonify(lights_data)


@app.route('/conectar_iot', methods=['POST'])
def conectar_iot():
    global endpoint_AWS, cert_filepath_AWS, pri_key_filepath_AWS
    global clientId_AWS, nombre_casa, message_topic_commands_AWS, message_topic_telemetry_AWS

    endpoint_AWS = request.form.get("endpoint_AWS")
    cert_filepath_AWS = request.form.get("cert_filepath_AWS")
    pri_key_filepath_AWS = request.form.get("pri_key_filepath_AWS")
    clientId_AWS = request.form.get("clientId_AWS")
    nombre_casa = request.form.get("nombre_casa")
    message_topic_commands_AWS = request.form.get("message_topic_commands_AWS")
    message_topic_telemetry_AWS = request.form.get("message_topic_telemetry_AWS")

    try:
        conectar_a_aws()
        return jsonify({"status": "success", "message": "Conectado a AWS IoT"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    print("Starting Flask server. Open http://<your-pi-ip-address>:5000 in a browser.")
    app.run(host='0.0.0.0', port=5000)
