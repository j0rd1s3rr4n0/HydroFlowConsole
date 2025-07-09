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
4. Accede a `/` para visualizar el mapa de la presa y controlar compuertas si tu rol lo permite.

La cookie `session` no está firmada y usa `pickle`, por lo que puede modificarse para ejecutar código arbitrario al deserializar.
