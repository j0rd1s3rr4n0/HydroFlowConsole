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
4. Accede a `/` para visualizar el mapa de la presa. El panel luce un estilo moderno con tarjetas translucidas y gráficos actualizados. Las cámaras se muestran en cuadrícula como si fuese una sala de seguridad: vista general, compuertas y turbinas.
   Cada cámara de turbina incluye una animación de giro y un chorro de agua cuando la puerta está abierta para aportar realismo.
   Puedes abrir o cerrar cada puerta si tienes rol de ingeniero o administrador. Además existen botones para abrir o cerrar todas las compuertas de una vez.
   Los gráficos utilizan distintos tipos (líneas y barras) según la métrica para una visualización más clara.
   Las lecturas se refrescan automáticamente cada pocos segundos y difieren entre usuarios para facilitar las pruebas.
6. Usa `/logout` para cerrar la sesión y borrar la cookie.

El tablero muestra en todo momento nivel de agua, presión y caudal. Si todas las puertas están cerradas el caudal es cero. Al accionar las compuertas el valor se recalcula inmediatamente, por lo que al cerrarlas todas el caudal pasa a 0 sin esperar a la siguiente actualización.
Cada compuerta tiene una turbina asociada que comienza a girar al abrirse y su velocidad depende de la presión del agua.
Las turbinas solo arrancan cuando el caudal total supera los 2 m³/s y nunca giran a menos de 2000 rpm. Si están paradas se mantienen a la temperatura ambiental menos tres grados. Cuando están girando su temperatura se incrementa un grado por cada 1000 rpm. La potencia generada sigue la fórmula física **P = ρ · g · Q · H** (densidad del agua, gravedad, caudal y altura en metros), por lo que aumenta con el nivel y el caudal. Si no hay caudal, la potencia mostrada es 0 MW.
El peso del agua se calcula a partir del volumen almacenado mediante **P = V × γ**,
donde `γ` es el peso específico del agua (aprox. 9810 N/m³). Para simplificar,
asumimos un área de 1000 m² por metro de altura, por lo que 1 m de nivel
equivale a unas 1000 toneladas de masa de agua.
Cuando el nivel supera los 250 m o la presión pasa de 280 bar aparece un aviso de peligro y la presa puede romperse e inundar la ciudad.

 Tambien se registran la temperatura del agua y de cada turbina, la velocidad de rotacion (rpm) y la energia generada por la central hidroelectrica. Cada puerta dispone de una turbina asociada. Puedes abrir o cerrar compuertas individualmente o con los botones "Abrir todas" y "Cerrar todas".

 Si la suma de potencia supera los 200 MW el sistema muestra un error 500 con el texto `flag{electric_power}` para simular un fallo catastrófico en la red.

La interfaz combina Bootstrap con un tema oscuro y paneles translúcidos para un aspecto más moderno.

La cookie `session` no está firmada y usa `pickle`, por lo que puede modificarse para ejecutar código arbitrario al deserializar.
