// Included Libraries
#include <SPI.h>

// Pin Definitions
#define redPin_RGB 24
#define greenPin_RGB 23
#define bluePin_RGB 22

String command = "";
bool ledLight = false;
bool rgbState = false;
int rgbR = 0;
int rgbG = 0;
int rgbB = 0;

void setup() {
  // Initialize Serial
  Serial.begin(9600);
  command.reserve(256);

  pinMode(redPin_RGB, OUTPUT);
  pinMode(greenPin_RGB, OUTPUT);
  pinMode(bluePin_RGB, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.println("Smarthome Ready. Enter commands via Serial monitor.");
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      executeCommand(command);
      command = "";
    } else {
      command += c;
    }
  }
}

void executeCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  Serial.print("Executing command: ");
  Serial.println(cmd);

  if (cmd.startsWith("led")) {
    if (cmd.indexOf("on") > 0) {
      digitalWrite(LED_BUILTIN, HIGH);
      Serial.println("Result: LED is ON");
      ledLight = true;
    } else if (cmd.indexOf("off") > 0) {
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("Result: LED is OFF");
      ledLight = false;
    }
  } else if (cmd.startsWith("rgb")) {

    if (cmd == "rgb on") {
      rgbState = true;

      color(rgbR, rgbG, rgbB);

      Serial.println("RGB ENCENDIDO");
      return;
    }

    if (cmd == "rgb off") {
      rgbState = false;

      analogWrite(redPin_RGB, 0);
      analogWrite(greenPin_RGB, 0);
      analogWrite(bluePin_RGB, 0);

      Serial.println("RGB APAGADO");
      return;
    }

    int r, g, b;

    int firstSpace = cmd.indexOf(' ');
    int secondSpace = cmd.indexOf(' ', firstSpace + 1);
    int thirdSpace = cmd.indexOf(' ', secondSpace + 1);

    if (firstSpace > 0 && secondSpace > 0 && thirdSpace > 0) {
      r = cmd.substring(firstSpace + 1, secondSpace).toInt();
      g = cmd.substring(secondSpace + 1, thirdSpace).toInt();
      b = cmd.substring(thirdSpace + 1).toInt();

      rgbState = true;

      color(r, g, b);

      Serial.print("RGB personalizado: ");
      Serial.print(r);
      Serial.print(",");
      Serial.print(g);
      Serial.print(",");
      Serial.println(b);
    } else {
      Serial.println("Formato: rgb R G B (ej: rgb 255 100 50)");
    }
  } else if (cmd.startsWith("sensores")) {
    readAllSensors();
  } else {
    Serial.println("Unknown command");
  }
}

void readAllSensors() {

  String estados = "";

  if (ledLight) {
    estados += "Luz Led encendida. ";
  } else {
    estados += "Luz Led apagada. ";
  }

  if (rgbState) {
    estados += "Luz RGB encendida. ";
    estados += "Color del RGB: ";
    estados += String(rgbR);
    estados += ", ";
    estados += String(rgbG);
    estados += ", ";
    estados += String(rgbB);
    estados += ". ";
  }

  Serial.println(estados);
}


void color(int r, int g, int b) {

  rgbR = constrain(r, 0, 255);
  rgbG = constrain(g, 0, 255);
  rgbB = constrain(b, 0, 255);

  if (rgbState) {
    analogWrite(redPin_RGB, rgbR);
    analogWrite(greenPin_RGB, rgbG);
    analogWrite(bluePin_RGB, rgbB);
  }
}