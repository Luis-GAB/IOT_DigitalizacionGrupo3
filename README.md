# IoT Digitalización Grupo 3 - Caso 1: Control Remoto de Luces
## Descripción del Proyecto

Nos hemos hecho con un Software publicado por Miguel Goyena en su GITHUB y lo hemos retocado para cumplir el siguiente enunciado:  

Juan es el dueño de la casa domotizada y ya está harto de dejar las luces de su casa encendidas. Entonces quiere tener un control remoto de las luces de su casa.

La casa tiene:

Sus 3 LEDS individuales, ROJO, VERDE, y AMARILLO.
Su luz RGB, donde puede poner el color que más le interese.
Su luz blanca en el exterior de su casa.

Quiere mediante una APP WEB de acceso por Internet ver el estado de todas sus luces y poder encender y apagar de forma individual las luces. En el caso del RGB quiere poner el color que quiera.

Para ello nos encontramos con la arquitectura de:

- **SLAVE (Arduino Mega 2560)**: Controla físicamente los LEDs de la casa mediante la conexion fisica de la casa con el PC.
- **MASTER (Raspberry Pi)**: Controla a traves del Raspberry Pi los controles LEDs de la casa.
- **CLOUD (AWS EC2)**: Controla remotamente desde cualquier lugar los controles LEDs de la casa.

## Cómo verificar cada capa
### SLAVE (Arduino)
- Conectar Arduino al PC por USB
- En console: 
- Enviar: `led[Color del led en ingles o castellano. Ej: ledRojo/ledRed] on/off` --> Apagara o encendera el led con el color indicado. 
- Enviar: `lights` --> Estado de todas las luces.
- Enviar: `rgb 255 128 0` --> Encendera el RGB con los valores indicado en R: 255, G: 128 Y B: 0.
- Enviar: `allLights on/off` --> Todas las luces se encienden/apagan.
### MASTER (Raspberry)
- 1º: `ssh admin@[Ip del raspberry]`
- 2º: `cd workspace-iot/master && source ~/casaIot/bin/activate && python app.py`
- 3º: `http://[Ip del raspberry]:5000`
  - Botones individuales para cada LED (Rojo, Verde, Amarillo, Exterior)
  - Sliders RGB con vista previa + "Aplicar Color"
  - "Encender Todo" / "Apagar Todo"
  - Log de respuestas en tiempo real
- Conexión AWS: `http://[Ip del raspberry]:5000/aws` > "Conectar a AWS IoT".
- Terminal: tras cada refresh se imprime `Parsed Lights Data: {...}` y `Publishing to topic 'telemetry': {...}`
### CLOUD (EC2 Windows)
- La EC2 es la de Kirian.
- 1º: `cd C:\Users\Administrator\Desktop\cloud && python app.py`
- 2º: `http://3.88.55.97:5001`
- Si funcionase bien saldria: 
  - Selector de casas
  - Panel de control de luces con botones Encender/Apagar
  - Sliders RGB + Aplicar Color
  - "Encender Todo" / "Apagar Todo"

Pero, como por restricciones de permisos de la cuenta no podemos crear un nuevo IAM y el IAM que tenemos de LabRole no tiene permisos suficientes la regla IoT no puede escribir en DynamoDB. (Lo sabemos porque nos daba este error: `La conexión de WebSocket al cliente de prueba no se realizó correctamente.
Esto puede deberse a la propagación continua del DNS, que puede tardar hasta 48 horas. Compruébelo de nuevo más tarde` y segun la IA es debido a los permisos de LabRole.

Tenemos la Tabla DynamoDB:	telemetry
Y la Regla IoT Core:	telemetry_a_dynamodb

Pero no nos va y por tanto al entrar a: `http://3.88.55.97:5001` Sale "No hay datos disponibles".
