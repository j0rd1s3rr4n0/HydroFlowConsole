Perfecto, aquí tienes el README reestructurado con secciones primero en inglés y luego en español, completamente separadas. Al final te añado los badges para stars, forks y licencia.

⸻

💧 HydroFlow Console

<p align="center">
  <img src="background.png" width="100%" alt="HydroFlow Console banner">
</p>



⸻

🇬🇧 English Version

🧭 Description

HydroFlow Console is an interactive simulator of a fictional hydroelectric power plant designed for educational purposes. It combines basic physics simulation (gates, turbines, pressure, power, weather) with an intentionally insecure deserialization vulnerability via Python pickle.
It’s ideal for learning applied physics and offensive security in a controlled and realistic environment.

⸻

⚙️ Installation & Setup
	1.	Install dependencies:

pip install -r requirements.txt


	2.	Run the application:

python app.py


	3.	Access the login page: /login.
	4.	Use any username and password (only l.perez can log in without a password).
	5.	Open /dashboard to access the main panel.

⸻

🔐 Authentication & Session Cookies

Session cookies are serialized using Python’s pickle and then base64-encoded. Each cookie stores a dictionary with the user’s name and role (viewer, engineer, admin).

Although the cookie looks like editable text, it contains binary data. To successfully modify it, one must:
	1.	Decode the base64 string.
	2.	Use pickle.loads() to deserialize it.
	3.	Change values (e.g. elevate role to admin).
	4.	Serialize again with pickle.dumps().
	5.	Encode back to base64 and inject it into the browser.

Note: Editing the base64 directly (e.g. with a text editor) breaks the binary format. Manual tampering is not enough — it requires proper serialization/deserialization.

⸻

🧠 Simulation Logic

Every 3 seconds, a loop updates:
	•	Weather conditions (sunny, rain, heavy rain)
	•	Water inflow into the dam
	•	Reservoir level and pressure
	•	Turbine RPM and temperature
	•	Power generation
	•	System failures (collapse, overload, turbine breakdown)

Key constants

Parameter	Value
Max level	250 m
Max pressure	100 bar
Max RPM	5000 rpm
Max power	200 MW
Gates	5


⸻

💣 Failure Conditions
	•	Collapse: if pressure > 100 bar or max level holds too long.
	•	Electrical overload: if power > 200 MW.
	•	Turbine damage: if RPM exceeds 5000.

When failure occurs:
	•	All system values reset to 0.
	•	/dashboard shows a 500 error page.
	•	Flag: flag{electric_power} is revealed.

⸻

📡 Firmware & Autopilot

The autopilot keeps pressure between 45–55 bar by opening/closing gates.
Admins can upload plain-text firmware files via /firmware/update to control system behavior.

Example:

autopilot: off
warnings: on

⚠️ The firmware system lacks validation, allowing unauthorized instructions or logic injections.

⸻

🎛️ Interface
	•	Built with Flask + Bootstrap.
	•	Real-time dashboard with water level, pressure, RPM, temperature, power.
	•	Weather status includes wind, temperature, and humidity.
	•	Prices fluctuate each second based on energy providers (e.g. GreenGrid, EnerCo).
	•	Interface responds to role-based access: viewer, engineer, or admin.

⸻

🧨 Exploit Scripts

Two exploitation scripts are provided in /Exploit/:
	•	exploit.py: uses Selenium to hijack a session and upload firmware.
	•	exploitv2.py: lightweight version using urllib, performs cookie forgery and disables autopilot.

Both lead to a system failure that displays the flag.

⸻

📁 Project Structure

.
├── app.py
├── templates/
│   ├── dashboard.html
│   ├── error.html
├── static/
├── Exploit/
│   ├── exploit.py
│   ├── exploitv2.py
├── firmware_uploads/
├── requirements.txt
└── README.md


⸻

🎯 Why Use HydroFlow?
	•	Demonstrate insecure deserialization.
	•	Explore ICS/SCADA concepts.
	•	Simulate industrial systems in a safe lab.
	•	Perfect for red teaming, teaching, or internal workshops.

⸻

🏷️ Topics

scada water-systems ctf training deserialization pickle docker flask simulator firmware hacking iot cybersec vulnerable-app red-team infosec educational python3


⸻

🇪🇸 Versión en Español

🧭 Descripción

HydroFlow Console es un simulador interactivo de una planta hidroeléctrica ficticia diseñado con fines educativos.
Reproduce comportamientos físicos básicos (compuertas, turbinas, presión, potencia, clima) e implementa intencionadamente una vulnerabilidad crítica de deserialización insegura mediante pickle en Python.
Es ideal para aprender física aplicada y ciberseguridad ofensiva en un entorno seguro y realista.

⸻

⚙️ Instalación y ejecución
	1.	Instala las dependencias:

pip install -r requirements.txt


	2.	Lanza la aplicación:

python app.py


	3.	Accede a /login con cualquier usuario y contraseña (solo l.perez entra sin password).
	4.	Abre /dashboard para ver el panel principal.

⸻

🔐 Autenticación y cookies de sesión

Las cookies de sesión están serializadas con pickle y codificadas en base64. Cada cookie contiene un diccionario con el nombre y rol del usuario (viewer, engineer, admin).

Aunque parezcan modificables a simple vista, contienen datos binarios. Para manipularlas correctamente:
	1.	Decodifica el base64.
	2.	Usa pickle.loads() para obtener el objeto.
	3.	Modifica el campo role.
	4.	Vuelve a serializar con pickle.dumps().
	5.	Codifica de nuevo en base64 y úsala como cookie.

Importante: Editar el base64 directamente corrompe la cookie. Se requiere deserialización completa.

⸻

🧠 Lógica de simulación

Cada 3 segundos se simulan:
	•	El clima (soleado, lluvia, lluvia fuerte)
	•	Entrada de agua
	•	Nivel del embalse y presión
	•	RPM y temperatura de turbinas
	•	Potencia generada
	•	Fallos físicos y colapsos

Constantes clave

Parámetro	Valor
Nivel máximo	250 m
Presión máxima	100 bar
RPM máxima	5000 rpm
Potencia máxima	200 MW
Número de compuertas	5


⸻

💣 Condiciones de fallo
	•	Colapso si presión > 100 bar o nivel > 250 m sin abrir compuertas.
	•	Sobrecarga eléctrica si la potencia excede 200 MW.
	•	Rotura de turbina si supera las 5000 rpm.

En caso de fallo:
	•	Todo se reinicia a 0.
	•	El panel muestra error 500.
	•	Se revela la flag: flag{electric_power}.

⸻

📡 Firmware y piloto automático

El autopilot regula la presión entre 45 y 55 bar.
Los administradores pueden subir firmware en texto plano vía /firmware/update.

Ejemplo:

autopilot: off
warnings: on

⚠️ No hay validación de firmware, lo que permite la ejecución de comandos no autorizados.

⸻

🎛️ Interfaz
	•	Interfaz con Flask + Bootstrap.
	•	Dashboard en tiempo real con nivel de agua, presión, temperatura, potencia, RPM.
	•	El clima incluye humedad, viento y temperatura.
	•	Los precios se actualizan cada segundo según la mejor oferta energética.
	•	Acceso a funciones según rol.

⸻

🧨 Scripts de explotación

Incluye dos scripts en /Exploit/:
	•	exploit.py: usa Selenium para forjar la cookie y subir firmware.
	•	exploitv2.py: versión ligera con urllib.

Ambos scripts fuerzan un fallo que muestra la flag.

⸻

📁 Estructura del proyecto

.
├── app.py
├── templates/
│   ├── dashboard.html
│   ├── error.html
├── static/
├── Exploit/
├── firmware_uploads/
├── requirements.txt
└── README.md


⸻

🎯 ¿Por qué usar HydroFlow?
	•	Demuestra errores reales como deserialización insegura.
	•	Útil para clases, talleres, CTFs, formaciones internas.
	•	Simulación de sistemas industriales críticos.
	•	Ideal para aprender a explotar vulnerabilidades en entornos seguros.

⸻

🏷️ Temas

scada sistemas-de-agua ctf formación deserialización pickle docker flask simulador firmware hacking iot ciberseguridad app-vulnerable red-team infosec educativo python3


⸻

🧷 Badges (Opcionales)

Añade esto arriba del README si deseas mostrar estadísticas visuales:

![GitHub stars](https://img.shields.io/github/stars/tu_usuario/HydroFlow-Console?style=social)
![GitHub forks](https://img.shields.io/github/forks/tu_usuario/HydroFlow-Console?style=social)
![GitHub license](https://img.shields.io/github/license/tu_usuario/HydroFlow-Console)

Solo reemplaza tu_usuario por tu nombre de usuario de GitHub. Si quieres, también te lo preparo con los links ya personalizados.

¿Quieres que te lo convierta todo en un README.md listo para pegar o subir?