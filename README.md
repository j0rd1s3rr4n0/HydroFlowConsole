# HydroConsole

Demo de presa hidraulica vulnerable a deserialización.

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta la aplicación:
   ```bash
   python app.py
   ```
3. Entra con `/login/<usuario>` (por ejemplo `/login/eng_jose`).
4. Accede a `/` para visualizar el mapa de la presa con zona de temporal, el pueblo y varios gráficos de sensores. Podrás controlar compuertas si tu rol lo permite.
5. Usa `/logout` para cerrar la sesión y borrar la cookie.

El tablero muestra los valores numéricos de nivel de agua, presión y caudal en todo momento. Cuando el nivel supera los 250 m o la presión pasa de 280 bar aparece un aviso de peligro y la presa puede romperse e inundar la ciudad.

La cookie `session` no está firmada y usa `pickle`, por lo que puede modificarse para ejecutar código arbitrario al deserializar.
