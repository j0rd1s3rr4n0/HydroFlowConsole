# HydroConsole

HydroConsole es un simulador sencillo de la presa de Tramuntana. Sirve para recrear, con un enfoque didáctico, cómo sería el panel de control de una central hidroeléctrica y a la vez exponer una vulnerabilidad de deserialización.

## Instalación y puesta en marcha
1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Arranca la aplicación en modo de desarrollo:
   ```bash
   python app.py
   ```
3. Accede con `/login/<usuario>` para obtener una cookie de sesión insegura.
4. Abre el panel visitando `/`.
5. Cierra sesión con `/logout`.

## Estructura general
- **app.py** contiene toda la lógica Flask y la simulación física.
- **templates/dashboard.html** muestra el panel con Bootstrap y gráficos de Chart.js.
- **templates/error.html** es la pantalla de fallo catastrófico.
- **requirements.txt** solo declara `Flask`.

## Funcionamiento y física empleada
Al iniciar todas las compuertas están cerradas y las turbinas paradas. Un hilo `update_state` actualiza el estado cada 3 s:

### Variables y constantes
- `NUM_GATES` = 5 compuertas.
- `MAX_LEVEL` = 250 m es el nivel máximo antes de que el agua sobrepase la presa.
- `DAM_AREA` = 1000 m² (área aproximada del vaso).
- `WATER_DENSITY` = 1000 kg/m³.
- `GRAVITY` = 9.81 m/s².
- `RPM_MIN` = 2000 rpm (mínimo de operación).
- `RPM_WARN` = 4500 rpm y `RPM_MAX` = 5000 rpm (rotura de turbina).
- `PRESSURE_MAX` = 100 bar (punto de colapso de la presa).
- `POWER_MAX` = 200 MW (sobrecalentamiento de la red eléctrica).

### Clima e inflow
Cada ciclo se generan condiciones meteorológicas aleatorias: `soleado`, `lluvia` o `lluvia fuerte`.
Dependiendo del clima, la entrada de agua se calcula así:
- Soleado: `inflow = 0.2 m³/s`.
- Lluvia: `inflow = 1.0 m³/s`.
- Lluvia fuerte: `inflow = 2.7 m³/s` (además se activa un temporizador de 60 s).

### Movimiento del agua
El número de compuertas abiertas determina el caudal de salida:
```
flow = open_gates * 1.0  # m³/s por compuerta
```
El nivel del embalse se actualiza restando el caudal y sumando la entrada de agua:
```
water_level += inflow - flow
water_level = max(water_level, 0)
```

La presión se aproxima de forma lineal a partir del nivel:
```
pressure = water_level * 1.12  # bar
```
El volumen se obtiene multiplicando la altura por el área de la presa y el peso total es:
```
volume = water_level * DAM_AREA
water_weight = (volume * WATER_DENSITY) / 1000  # toneladas
```
La misma fórmula permite calcular litros (`volume * 1000`).

### Turbinas y potencia
Cada puerta posee una turbina. Si hay más de dos compuertas abiertas el sistema calcula la velocidad objetivo en función de la presión:
```
target_rpm = max(pressure * 8, RPM_MIN)
```
Las RPM se ajustan suavemente al objetivo y nunca bajan de cero. Si superan `RPM_MAX`, la turbina se marca como rota.

La temperatura base de la turbina es la ambiental menos 3 °C. Cuando gira, aumenta un grado por cada 1000 rpm.

La potencia instantánea se calcula mediante la fórmula física clásica:
```
P = ρ * g * Q * H / 1_000_000
```
Siendo `ρ` la densidad del agua, `g` la gravedad, `Q` el caudal total y `H` la altura (nivel). El resultado se expresa en megavatios.

### Condiciones de fallo
- **Colapso de la presa**: si la presión supera `100 bar` o el nivel máximo se mantiene durante más de un minuto sin abrir compuertas.
- **Sobrecarga eléctrica**: si la potencia total rebasa `200 MW`.

Ante cualquiera de estas situaciones se activa `SYSTEM_FAILED`. Todas las variables se ponen a cero y cualquier acceso al panel muestra una página de error 500 con la bandera `flag{electric_power}`.

## Vulnerabilidad de deserialización
El endpoint `/login/<user>` genera una cookie `session` sin firma que contiene un diccionario serializado con `pickle` y codificado en base64. La cookie almacena el nombre de usuario y su rol (`viewer`, `engineer` o `admin`).

Al visitar `/` o `/dashboard`, la aplicación decodifica dicha cookie y ejecuta `pickle.loads()`. No hay ninguna verificación, por lo que es posible modificar la cookie para ejecutar código arbitrario en el servidor al deserializar.

## Interfaz
El tablero emplea Bootstrap para organizar tarjetas translúcidas con los valores actuales. Unos gráficos de Chart.js muestran la evolución del nivel del agua, la presión, el caudal, la temperatura y la potencia. Dependiendo del rol, aparecen botones para abrir o cerrar compuertas individualmente o todas a la vez.

Los datos se actualizan cada pocos segundos y cada visitante ve pequeñas variaciones aleatorias para probar la interfaz.

La cabecera muestra ahora un pequeño menú oscuro con el usuario conectado y un botón de salida. El bloque de
"Estado meteorológico" se ha ampliado para incluir la humedad relativa y se presenta con un tamaño mayor para destacar
el tiempo, la temperatura, el viento y la humedad actuales.

HydroConsole pretende ser un ejemplo didáctico de simulación y de vulnerabilidades de deserialización, a la vez que ofrece un modelo de cálculo con un mínimo de realismo físico.
