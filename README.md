# HydroConsole

Demo de presa hidraulica y central hidroelectrica vulnerable a deserialización.

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la aplicación:
 ```bash
  python app.py
  ```
Al iniciar todas las compuertas están cerradas y las turbinas detenidas.
3. Entra con `/login/<usuario>` (por ejemplo `/login/eng_jose`).
4. Accede a `/` para visualizar el mapa de la presa. Se muestran dos cámaras: una general del pueblo (cámara 1) y otra enfocada a las compuertas (cámara 2) para ver mejor su estado.
   Puedes abrir o cerrar cada puerta si tienes rol de ingeniero o administrador.
   Las lecturas se refrescan automáticamente cada pocos segundos y difieren entre usuarios para facilitar las pruebas.
6. Usa `/logout` para cerrar la sesión y borrar la cookie.

El tablero muestra en todo momento nivel de agua, presión y caudal. Si todas las puertas están cerradas el caudal es cero. Cada compuerta tiene una turbina asociada que comienza a girar al abrirse y su velocidad depende de la presión del agua.
Cuando el nivel supera los 250 m o la presión pasa de 280 bar aparece un aviso de peligro y la presa puede romperse e inundar la ciudad.

 Tambien se registran la temperatura del agua y de cada turbina, la velocidad de rotacion (rpm) y la energia generada por la central hidroelectrica. Cada puerta dispone de una turbina asociada.

 Si la suma de potencia supera los 200 MW el sistema muestra un error 500 con el texto `flag{electric_power}` para simular un fallo catastrófico en la red.

La cookie `session` no está firmada y usa `pickle`, por lo que puede modificarse para ejecutar código arbitrario al deserializar.
