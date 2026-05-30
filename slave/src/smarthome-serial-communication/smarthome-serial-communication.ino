/*
   Smarthome Serial Communication - Caso 1: Control Remoto de Luces
   CopyRight Ander F.L. <ander_frago@cuatrovientos.org> June 2024
*/

#define redLED 13
#define greenLED 12
#define whiteLED 9
#define yellowLED 10
#define redPin_RGB 24
#define greenPin_RGB 23
#define bluePin_RGB 22


bool estadoRojo = false;
bool estadoVerde = false;
bool estadoAmarillo = false;
bool estadoPuerta = false;
int rRGB = 0, gRGB = 0, bRGB = 0;

String command = "";

void setup() {
  Serial.begin(9600);
  command.reserve(256);

  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(whiteLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);
  pinMode(redPin_RGB, OUTPUT);
  pinMode(greenPin_RGB, OUTPUT);
  pinMode(bluePin_RGB, OUTPUT);

  Serial.println("Casa domotica lista. Introduce comandos por el monitor Serie.");
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

  Serial.print("Ejecutando comando: ");
  Serial.println(cmd);

  if (cmd.startsWith("ledRojo") || cmd.startsWith("ledRed")) {
    if (cmd.indexOf("on") > 0) {
      digitalWrite(redLED, HIGH);
      estadoRojo = true;
      Serial.println("Resultado: led_rojo: ON");
    } else if (cmd.indexOf("off") > 0) {
      digitalWrite(redLED, LOW);
      estadoRojo = false;
      Serial.println("Resultado: led_rojo: OFF");
    }
  } else if (cmd.startsWith("ledVerde") || cmd.startsWith("ledGreen")) {
    if (cmd.indexOf("on") > 0) {
      digitalWrite(greenLED, HIGH);
      estadoVerde = true;
      Serial.println("Resultado: led_verde: ON");
    } else if (cmd.indexOf("off") > 0) {
      digitalWrite(greenLED, LOW);
      estadoVerde = false;
      Serial.println("Resultado: led_verde: OFF");
    }
  } else if (cmd.startsWith("ledAmarillo") || cmd.startsWith("ledYellow")) {
    if (cmd.indexOf("on") > 0) {
      digitalWrite(yellowLED, HIGH);
      estadoAmarillo = true;
      Serial.println("Resultado: led_amarillo: ON");
    } else if (cmd.indexOf("off") > 0) {
      digitalWrite(yellowLED, LOW);
      estadoAmarillo = false;
      Serial.println("Resultado: led_amarillo: OFF");
    }
   } else if (cmd.startsWith("ledPuerta") || cmd.startsWith("ledDoor") || cmd.startsWith("ledWhite") || cmd.startsWith("ledBlanco")) { 
    if (cmd.indexOf("on") > 0) {
      digitalWrite(whiteLED, HIGH);
      estadoPuerta = true;
      Serial.println("Resultado: led_puerta: ON");
    } else if (cmd.indexOf("off") > 0) {
      digitalWrite(whiteLED, LOW);
      estadoPuerta = false;
      Serial.println("Resultado: led_puerta: OFF");
    }
  } else if (cmd.startsWith("allLights") || cmd.startsWith("todasLuces")) {
    if (cmd.indexOf("on") > 0) {
      digitalWrite(redLED, HIGH);    estadoRojo = true;
      digitalWrite(greenLED, HIGH);  estadoVerde = true;
      digitalWrite(yellowLED, HIGH); estadoAmarillo = true;
      digitalWrite(whiteLED, HIGH);  estadoPuerta = true;
      Serial.println("Resultado: all_lights: ON");
    } else if (cmd.indexOf("off") > 0) {
      digitalWrite(redLED, LOW);    estadoRojo = false;
      digitalWrite(greenLED, LOW);  estadoVerde = false;
      digitalWrite(yellowLED, LOW); estadoAmarillo = false;
      digitalWrite(whiteLED, LOW);  estadoPuerta = false;
      color(0, 0, 0);  rRGB = 0; gRGB = 0; bRGB = 0;
      Serial.println("Resultado: all_lights: OFF");
    }
  } else if (cmd.startsWith("rgb")) {
    int firstSpace = cmd.indexOf(' ');
    int secondSpace = cmd.indexOf(' ', firstSpace + 1);
    if (firstSpace > 0 && secondSpace > 0) {
      int r = cmd.substring(firstSpace + 1, secondSpace).toInt();
      int thirdSpace = cmd.indexOf(' ', secondSpace + 1);
      int g = 0, b = 0;
      if (thirdSpace > 0) {
        g = cmd.substring(secondSpace + 1, thirdSpace).toInt();
        b = cmd.substring(thirdSpace + 1).toInt();
      } else {
        g = cmd.substring(secondSpace + 1).toInt();
        b = 0;
      }
      r = constrain(r, 0, 255);
      g = constrain(g, 0, 255);
      b = constrain(b, 0, 255);
      color(r, g, b);
      rRGB = r; gRGB = g; bRGB = b;
      Serial.print("Resultado: rgb_red: ");
      Serial.println(r);
      Serial.print("Resultado: rgb_green: ");
      Serial.println(g);
      Serial.print("Resultado: rgb_blue: ");
      Serial.println(b);
    } else if (cmd.indexOf("red") > 0) {
      color(255, 0, 0); rRGB = 255; gRGB = 0; bRGB = 0;
      Serial.println("Resultado: RGB configurado a ROJO");
    } else if (cmd.indexOf("green") > 0) {
      color(0, 255, 0); rRGB = 0; gRGB = 255; bRGB = 0;
      Serial.println("Resultado: RGB configurado a VERDE");
    } else if (cmd.indexOf("blue") > 0) {
      color(0, 0, 255); rRGB = 0; gRGB = 0; bRGB = 255;
      Serial.println("Resultado: RGB configurado a AZUL");
    }
  } else if (cmd.startsWith("lights") || cmd.startsWith("estadoLuces") || cmd.startsWith("lightsStatus")) {
    readAllSensors();
  } else {
    Serial.println("Comando desconocido");
  }
}

void readAllSensors() {
  Serial.print("Resultado: led_rojo: ");
  Serial.println(estadoRojo ? "ON" : "OFF");
  Serial.print("Resultado: led_verde: ");
  Serial.println(estadoVerde ? "ON" : "OFF");
  Serial.print("Resultado: led_amarillo: ");
  Serial.println(estadoAmarillo ? "ON" : "OFF");
  Serial.print("Resultado: led_puerta: ");
  Serial.println(estadoPuerta ? "ON" : "OFF");
  Serial.print("Resultado: rgb_red: ");
  Serial.println(rRGB);
  Serial.print("Resultado: rgb_green: ");
  Serial.println(gRGB);
  Serial.print("Resultado: rgb_blue: ");
  Serial.println(bRGB);
}

void color(unsigned char red, unsigned char green, unsigned char blue) {
  analogWrite(redPin_RGB, red);
  analogWrite(greenPin_RGB, green);
  analogWrite(bluePin_RGB, blue);
}
